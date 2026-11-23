from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import RequestFilterForm, TravelRequestForm
from .models import Approval
from .queries import filter_requests, related_requests


SORT_FIELDS = {
    "date": ("trip__start_date", "id"),
    "-date": ("-trip__start_date", "id"),
    "employee": ("-employee__name", "trip__start_date", "id"),
    "destination": ("trip__destination", "trip__start_date", "id"),
}


def request_list(request):
    form = RequestFilterForm(request.GET or None)
    queryset = related_requests()
    sort = "date"
    if form.is_bound:
        if form.is_valid():
            queryset = filter_requests(queryset, form.cleaned_data)
            sort = form.cleaned_data["sort"] or "date"
        else:
            queryset = queryset.none()
    page = Paginator(queryset.order_by(*SORT_FIELDS[sort]), 10).get_page(
        request.GET.get("page"),
    )
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "trip_requests/request_list.html", {
        "travel_requests": page, "page_obj": page,
        "form": form, "query_string": params.urlencode(),
    })


def request_detail(request, request_id):
    item = get_object_or_404(related_requests(), pk=request_id)
    return render(request, "trip_requests/request_detail.html", {
        "travel_request": item, "can_edit": item.can_edit,
    })


def request_form(request, item=None):
    form = TravelRequestForm(
        request.POST if request.method == "POST" else None,
        instance=item,
    )
    if request.method == "POST" and form.is_valid():
        try:
            saved = form.save()
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect("trip_requests:detail", request_id=saved.pk)
    back_url = reverse("trip_requests:list")
    if item:
        back_url = reverse("trip_requests:detail", kwargs={
            "request_id": item.pk,
        })
    return render(request, "form.html", {
        "title": "Редактировать заявку" if item else "Создать заявку",
        "form": form, "back_url": back_url,
    })


@require_http_methods(["GET", "POST"])
def request_create(request):
    return request_form(request)


@require_http_methods(["GET", "POST"])
def request_edit(request, request_id):
    return request_form(request, get_object_or_404(
        editable_requests(), pk=request_id,
    ))


def editable_requests():
    return related_requests().filter(approval__status__in=[
        Approval.Status.PENDING, Approval.Status.APPROVED,
    ])


@require_POST
def request_cancel(request, request_id):
    item = get_object_or_404(editable_requests(), pk=request_id)
    item.cancel()
    return redirect("trip_requests:detail", request_id=item.pk)
