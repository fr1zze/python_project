from django.urls import path

from . import views


app_name = "sql_reports"

urlpatterns = [
    path(
        "employees/",
        views.employee_list,
        name="employees",
    ),
    path(
        "trips/",
        views.trip_list,
        name="trips",
    ),
    path(
        "requests/",
        views.request_list,
        name="requests",
    ),
    path(
        "search/",
        views.search,
        name="search",
    ),
    path(
        "statistics/",
        views.statistics,
        name="statistics",
    ),
]