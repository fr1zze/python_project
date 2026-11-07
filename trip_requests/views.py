from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from employees.models import Employee

from .forms import RequestFilterForm, TravelRequestForm
from .models import Approval, TravelRequest, Trip
from .queries import filter_requests, related_requests


SORT_FIELDS = {
    "date": ("trip__start_date", "id"),
    "-date": ("-trip__start_date", "id"),
    "employee": ("employee__name", "trip__start_date", "id"),
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
        "travel_request": item,
    })


def request_initial(item):
    return {
        "employee_id": item.employee_id,
        "budget_limit": item.budget_limit,
        **{field: getattr(item.trip, field) for field in (
            "destination", "purpose", "start_date", "end_date",
            "travel_cost", "hotel_cost", "daily_allowance",
        )},
    }


def save_request(form, item=None):
    """Атомарно сохранить поездку, заявку и согласование."""
    data = form.cleaned_data.copy()
    employee_id = data.pop("employee_id")
    budget = data.pop("budget_limit")
    with transaction.atomic():
        # Одобренная заявка повторно проходит проверку бизнес-правил.
        trip = item.trip if item else Trip()
        for field, value in data.items():
            setattr(trip, field, value)
        trip.full_clean()
        if item is None:
            item = TravelRequest()
        item.employee = Employee.objects.get(pk=employee_id)
        item.budget_limit = budget
        if item.pk and item.approval.status == Approval.Status.APPROVED:
            item.validate_approved()
        trip.save()
        item.trip = trip
        item.full_clean()
        item.save()
        Approval.objects.get_or_create(request=item)
    return item


def request_form(request, item=None):
    form = TravelRequestForm(
        request.POST if request.method == "POST" else None,
        employees=Employee.objects.all(),
        initial=request_initial(item) if item else None,
    )
    if request.method == "POST" and form.is_valid():
        try:
            saved = save_request(form, item)
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
        related_requests(), pk=request_id,
    ))
