from html import escape

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from homepage.views import form_page, page
from models.approval import Approval
from models.employees import find_employee
from models.travel_requests import (
    TravelRequest,
    create_request,
    find_request,
    sort_requests_by_date,
)
from models.trips import Trip
from storage import (
    load_employees,
    load_requests,
    save_requests,
)

from .forms import TravelRequestForm


STATUS_COLORS = {
    "на рассмотрении": "bg-warning text-dark",
    "одобрена": "bg-success",
    "отклонена": "bg-danger",
    "отменена": "bg-secondary",
}


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
    requests = sort_requests_by_date(requests)

    items = ""

    for travel_request in requests:
        status = travel_request.approval.status
        badge = STATUS_COLORS.get(
            status,
            "bg-secondary",
        )

        items += f"""
        <li class="list-group-item">
            <div class="d-flex flex-wrap gap-2">
                <a href="/requests/{travel_request.id}/">
                    Заявка №{travel_request.id}
                </a>
                <span class="badge {badge}">
                    {escape(status)}
                </span>
            </div>

            <p class="mb-1 mt-2">
                Сотрудник:
                {escape(travel_request.employee.name)}
            </p>
            <p class="mb-1">
                Направление:
                {escape(travel_request.trip.destination)}
            </p>
            <p class="mb-0">
                Начало:
                {travel_request.trip.start_date:%d.%m.%Y}
            </p>

            <div class="mt-3">
                <a href="/requests/{travel_request.id}/edit/"
                   class="btn btn-outline-primary btn-sm">
                    Редактировать
                </a>
            </div>
        </li>
        """

    if not requests:
        items = """
        <li class="list-group-item">
            Заявки пока не созданы.
        </li>
        """

    content = f"""
    <div class="d-flex flex-wrap gap-3 mb-4
                justify-content-between align-items-center">
        <h1 class="mb-0">Заявки на командировки</h1>

        <a href="/requests/new/" class="btn btn-primary">
            Создать заявку
        </a>
    </div>

    <p class="text-muted">
        Заявки расположены по дате начала поездки.
    </p>

    <ul class="list-group">
        {items}
    </ul>
    """

    return HttpResponse(
        page("Командировки — заявки", content)
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
        content = """
        <h1 class="text-danger">Заявка не найдена</h1>
        <a href="/requests/" class="btn btn-secondary">
            К списку заявок
        </a>
        """

        return HttpResponse(
            page("Заявка не найдена", content),
            status=404,
        )

    trip = travel_request.trip
    employee = travel_request.employee
    status = travel_request.approval.status

    badge = STATUS_COLORS.get(
        status,
        "bg-secondary",
    )

    content = f"""
    <div class="card">
        <div class="card-body">
            <h1 class="h3">
                Заявка №{travel_request.id}
            </h1>

            <p>
                Сотрудник:
                <a href="/employees/{employee.id}/">
                    {escape(employee.name)}
                </a>
            </p>

            <p>Направление: {escape(trip.destination)}</p>
            <p>Цель: {escape(trip.purpose)}</p>
            <p>Начало: {trip.start_date:%d.%m.%Y}</p>
            <p>Окончание: {trip.end_date:%d.%m.%Y}</p>
            <p>Продолжительность: {trip.calculate_days()} дн.</p>

            <h2 class="h5">Расходы</h2>
            <p>Проезд: {trip.travel_cost:.2f} руб.</p>
            <p>Проживание: {trip.hotel_cost:.2f} руб.</p>
            <p>
                Суточные за день:
                {trip.daily_allowance:.2f} руб.
            </p>
            <p>
                <strong>
                    Общая стоимость:
                    {trip.calculate_total_cost():.2f} руб.
                </strong>
            </p>
            <p>
                Лимит бюджета:
                {travel_request.budget_limit:.2f} руб.
            </p>

            <p>
                Согласование:
                <span class="badge {badge}">
                    {escape(status)}
                </span>
            </p>

            <a href="/requests/{travel_request.id}/edit/"
               class="btn btn-primary me-2">
                Редактировать заявку
            </a>

            <a href="/requests/" class="btn btn-secondary">
                К списку заявок
            </a>
        </div>
    </div>
    """

    return HttpResponse(
        page(
            f"Заявка №{travel_request.id}",
            content,
        )
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
    requests = load_requests(
        filename,
        employees,
    )

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

            save_requests(
                filename,
                requests,
            )
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            return redirect(
                "request_detail",
                request_id=travel_request.id,
            )

    return form_page(
        request,
        "Создать заявку",
        form,
        "/requests/",
    )


@require_http_methods(["GET", "POST"])
def request_edit(request, request_id):
    """Изменить заявку, сохранив её статус."""
    data_dir = settings.BASE_DIR / "data"
    filename = data_dir / "requests.json"

    employees = load_employees(
        data_dir / "employees.json"
    )
    requests = load_requests(
        filename,
        employees,
    )

    try:
        original = find_request(
            requests,
            request_id,
        )
    except ValueError:
        return HttpResponse(
            page(
                "Заявка не найдена",
                "<h1>Заявка не найдена</h1>",
            ),
            status=404,
        )

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

            save_requests(
                filename,
                updated_requests,
            )
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            return redirect(
                "request_detail",
                request_id=original.id,
            )

    return form_page(
        request,
        "Редактировать заявку",
        form,
        f"/requests/{original.id}/",
    )