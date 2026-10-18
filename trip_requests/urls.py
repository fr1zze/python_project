from django.urls import path

from . import views


app_name = "trip_requests"

urlpatterns = [
    path("", views.request_list, name="list"),
    path("new/", views.request_create, name="create"),
    path(
        "<int:request_id>/edit/",
        views.request_edit,
        name="edit",
    ),
    path(
        "<int:request_id>/",
        views.request_detail,
        name="detail",
    ),
]