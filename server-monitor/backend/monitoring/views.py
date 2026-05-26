from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AppSetting, CheckLog, Incident, IncidentStatus, Server
from .serializers import (
    AppSettingSerializer,
    CheckLogSerializer,
    IncidentSerializer,
    ManualCheckResponseSerializer,
    ServerSerializer,
)
from .services.monitoring import run_server_checks


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all().order_by("name")
    serializer_class = ServerSerializer

    def perform_create(self, serializer):
        server = serializer.save()
        if server.is_active:
            run_server_checks(server, send_alerts=False)

    def perform_update(self, serializer):
        server = serializer.save()
        if server.is_active:
            run_server_checks(server, send_alerts=False)

    @action(detail=True, methods=["post"], url_path="check")
    def check_now(self, request, pk=None):
        server = self.get_object()
        result = run_server_checks(server, send_alerts=False)
        payload = {
            "server_id": server.id,
            "server_name": result.server.name,
            "ip_address": result.server.ip_address,
            "success": result.overall_status == "up",
            "last_status": result.overall_status,
            "response_ms": result.response_ms,
            "error": result.error,
            "checked_at": result.checked_at,
            "checks": result.logs,
        }
        serializer = ManualCheckResponseSerializer(payload)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="ping")
    def ping_alias(self, request, pk=None):
        return self.check_now(request, pk=pk)


class RecentChecksView(ListAPIView):
    serializer_class = CheckLogSerializer

    def get_queryset(self):
        limit = _bounded_limit(self.request.query_params.get("limit"), 50, 1, 500)
        return CheckLog.objects.select_related("server").order_by("-checked_at")[:limit]


class ServerChecksView(ListAPIView):
    serializer_class = CheckLogSerializer

    def get_queryset(self):
        limit = _bounded_limit(self.request.query_params.get("limit"), 100, 1, 1000)
        return (
            CheckLog.objects.select_related("server")
            .filter(server_id=self.kwargs["server_id"])
            .order_by("-checked_at")[:limit]
        )


class IncidentListView(ListAPIView):
    serializer_class = IncidentSerializer

    def get_queryset(self):
        queryset = Incident.objects.select_related("server").order_by("-started_at")
        wanted_status = self.request.query_params.get("status", "open")
        if wanted_status in {IncidentStatus.OPEN, IncidentStatus.RESOLVED}:
            queryset = queryset.filter(status=wanted_status)
        limit = _bounded_limit(self.request.query_params.get("limit"), 50, 1, 500)
        return queryset[:limit]


class AppSettingsView(APIView):
    def get(self, request):
        serializer = AppSettingSerializer(AppSetting.load())
        return Response(serializer.data)

    def patch(self, request):
        instance = AppSetting.load()
        serializer = AppSettingSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AppSettingSerializer(instance).data)


class SummaryView(APIView):
    def get(self, request):
        totals = Server.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
            up=Count("id", filter=Q(is_active=True, last_status="up")),
            down=Count("id", filter=Q(is_active=True, last_status="down")),
            unknown=Count("id", filter=Q(is_active=True, last_status="unknown")),
        )
        totals["open_incidents"] = Incident.objects.filter(
            status=IncidentStatus.OPEN
        ).count()
        return Response(totals, status=status.HTTP_200_OK)


def _bounded_limit(value, default: int, minimum: int, maximum: int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = default
    return min(max(limit, minimum), maximum)
