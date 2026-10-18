from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from homepage.views import page_not_found
from models.approval import Approval
from models.employees import find_employee
from models.travel_requests import (
    TravelRequest,
    create_request,
    find_request,
    sort_requests_by_date,
)
from models.trips import Trip
from storage import load_employees, load_requests, save_requests

from .forms import TravelRequestForm


def request_list(request):
    """Показать заявки по дате начала поездки."""
    data_dir = settings.BASE_DIR / "data"
    employees = load_employees(
        data_dir / "employees.json"
    )
    requests = load_requests(
        data_dir / "requests.json",
        employees,
    )

    context = {
        "travel_requests": sort_requests_by_date(requests),
    }

    return render(
        request,
        "trip_requests/request_list.html",
        context,
    )


def request_detail(request, request_id):
    """Показать заявку, поездку и согласование."""
    data_dir = settings.BASE_DIR / "data"
    employees = load_employees(
        data_dir / "employees.json"
    )
    requests = load_requests(
        data_dir / "requests.json",
        employees,
    )

    try:
        travel_request = find_request(
            requests,
            request_id,
        )
    except ValueError:
        return page_not_found(request)

    return render(
        request,
        "trip_requests/request_detail.html",
        {"travel_request": travel_request},
    )


def request_data_from_form(form, employees):
    """Получить сотрудника, поездку и бюджет из формы."""
    data = form.cleaned_data

    employee = find_employee(
        employees,
        data["employee_id"],
    )

    if employee is None:
        raise ValueError("Выбранный сотрудник не найден.")

    trip = Trip(
        data["destination"],
        data["purpose"],
        data["start_date"],
        data["end_date"],
        float(data["travel_cost"]),
        float(data["hotel_cost"]),
        float(data["daily_allowance"]),
    )

    return (
        employee,
        trip,
        float(data["budget_limit"]),
    )


def request_initial(travel_request):
    """Получить текущие значения заявки для формы."""
    trip = travel_request.trip

    return {
        "employee_id": travel_request.employee.id,
        "destination": trip.destination,
        "purpose": trip.purpose,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "travel_cost": trip.travel_cost,
        "hotel_cost": trip.hotel_cost,
        "daily_allowance": trip.daily_allowance,
        "budget_limit": travel_request.budget_limit,
    }


@require_http_methods(["GET", "POST"])
def request_create(request):
    """Создать заявку со статусом на рассмотрении."""
    data_dir = settings.BASE_DIR / "data"
    filename = data_dir / "requests.json"

    employees = load_employees(
        data_dir / "employees.json"
    )
    requests = load_requests(filename, employees)

    form = TravelRequestForm(
        request.POST if request.method == "POST" else None,
        employees=employees,
    )

    if request.method == "POST" and form.is_valid():
        try:
            employee, trip, budget = request_data_from_form(
                form,
                employees,
            )
            travel_request = create_request(
                requests,
                employee,
                trip,
                budget,
            )
            save_requests(filename, requests)
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            return redirect(
                "trip_requests:detail",
                request_id=travel_request.id,
            )

    context = {
        "title": "Создать заявку",
        "form": form,
        "back_url": reverse("trip_requests:list"),
    }

    return render(request, "form.html", context)


@require_http_methods(["GET", "POST"])
def request_edit(request, request_id):
    """Изменить заявку, сохранив её статус."""
    data_dir = settings.BASE_DIR / "data"
    filename = data_dir / "requests.json"

    employees = load_employees(
        data_dir / "employees.json"
    )
    requests = load_requests(filename, employees)

    try:
        original = find_request(requests, request_id)
    except ValueError:
        return page_not_found(request)

    form = TravelRequestForm(
        request.POST if request.method == "POST" else None,
        employees=employees,
        initial=request_initial(original),
    )

    if request.method == "POST" and form.is_valid():
        try:
            employee, trip, budget = request_data_from_form(
                form,
                employees,
            )

            updated_request = TravelRequest(
                original.id,
                employee,
                trip,
                budget,
            )

            if original.approval.status == "одобрена":
                other_requests = [
                    item
                    for item in requests
                    if item.id != original.id
                ]
                updated_request.approve(
                    other_requests,
                    True,
                )
            else:
                updated_request.approval = Approval(
                    original.approval.status
                )

            updated_requests = [
                updated_request
                if item.id == original.id
                else item
                for item in requests
            ]

            save_requests(filename, updated_requests)
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            return redirect(
                "trip_requests:detail",
                request_id=original.id,
            )

    context = {
        "title": "Редактировать заявку",
        "form": form,
        "back_url": reverse(
            "trip_requests:detail",
            kwargs={"request_id": original.id},
        ),
    }

    return render(request, "form.html", context)