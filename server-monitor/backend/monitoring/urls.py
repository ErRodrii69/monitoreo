from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AppSettingsView,
    IncidentListView,
    RecentChecksView,
    ServerChecksView,
    ServerViewSet,
    SummaryView,
)


router = DefaultRouter()
router.register("servers", ServerViewSet, basename="server")

urlpatterns = [
    path("checks/", RecentChecksView.as_view(), name="recent-checks"),
    path("checks/server/<int:server_id>/", ServerChecksView.as_view(), name="server-checks"),
    path("incidents/", IncidentListView.as_view(), name="incidents"),
    path("settings/", AppSettingsView.as_view(), name="settings"),
    path("summary/", SummaryView.as_view(), name="summary"),
]
urlpatterns += router.urls
