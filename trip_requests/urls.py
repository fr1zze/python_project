from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.request_list,
        name="request_list",
    ),
    path(
        "new/",
        views.request_create,
        name="request_create",
    ),
    path(
        "<int:request_id>/edit/",
        views.request_edit,
        name="request_edit",
    ),
    path(
        "<int:request_id>/",
        views.request_detail,
        name="request_detail",
    ),
]