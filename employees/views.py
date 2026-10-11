from html import escape

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from homepage.views import form_page, page
from models.employees import (
    Employee,
    add_employee,
    find_employee,
)
from models.travel_requests import find_requests_by_employee
from storage import (
    load_employees,
    load_requests,
    save_employees,
)

from .forms import EmployeeForm


def employee_list(request):
    """Показать список сотрудников."""
    employees = load_employees(
        settings.BASE_DIR / "data" / "employees.json"
    )

    items = ""

    for employee in employees:
        items += f"""
        <li class="list-group-item">
            <div class="d-flex flex-wrap gap-3
                        justify-content-between align-items-center">
                <div>
                    <a href="/employees/{employee.id}/"
                       class="fw-semibold text-decoration-none">
                        {escape(employee.name)}
                    </a>
                    <div class="text-muted mt-1">
                        {escape(employee.position)}
                    </div>
                </div>

                <a href="/employees/{employee.id}/edit/"
                   class="btn btn-outline-primary btn-sm">
                    Редактировать
                </a>
            </div>
        </li>
        """

    if not employees:
        items = """
        <li class="list-group-item">
            Сотрудники пока не добавлены.
        </li>
        """

    content = f"""
    <div class="d-flex flex-wrap gap-3 mb-4
                justify-content-between align-items-center">
        <h1 class="mb-0">Сотрудники</h1>

        <a href="/employees/new/" class="btn btn-primary">
            Добавить сотрудника
        </a>
    </div>

    <ul class="list-group">
        {items}
    </ul>
    """

    return HttpResponse(
        page("Командировки — сотрудники", content)
    )


def employee_detail(request, employee_id):
    """Показать сотрудника и связанные с ним заявки."""
    data_dir = settings.BASE_DIR / "data"

    employees = load_employees(
        data_dir / "employees.json"
    )
    employee = find_employee(
        employees,
        employee_id,
    )

    if employee is None:
        content = """
        <h1 class="text-danger">Сотрудник не найден</h1>
        <a href="/employees/" class="btn btn-secondary">
            К списку сотрудников
        </a>
        """

        return HttpResponse(
            page("Сотрудник не найден", content),
            status=404,
        )

    requests = load_requests(
        data_dir / "requests.json",
        employees,
    )
    employee_requests = find_requests_by_employee(
        requests,
        employee.id,
    )

    items = ""

    for travel_request in employee_requests:
        items += f"""
        <li class="list-group-item">
            <a href="/requests/{travel_request.id}/">
                Заявка №{travel_request.id}
            </a>
            — {escape(travel_request.trip.destination)},
            {escape(travel_request.approval.status)}
        </li>
        """

    if not employee_requests:
        items = """
        <li class="list-group-item">
            У сотрудника пока нет заявок.
        </li>
        """

    content = f"""
    <div class="card mb-4">
        <div class="card-body">
            <h1 class="h3">{escape(employee.name)}</h1>
            <p>ID: {employee.id}</p>
            <p>Должность: {escape(employee.position)}</p>
        </div>
    </div>

    <h2 class="h4">Заявки сотрудника</h2>
    <ul class="list-group mb-4">
        {items}
    </ul>

    <a href="/employees/{employee.id}/edit/"
       class="btn btn-primary me-2">
        Редактировать сотрудника
    </a>

    <a href="/employees/" class="btn btn-secondary">
        К списку сотрудников
    </a>
    """

    return HttpResponse(
        page(employee.name, content)
    )


@require_http_methods(["GET", "POST"])
def employee_create(request):
    """Создать сотрудника."""
    filename = (
        settings.BASE_DIR / "data" / "employees.json"
    )
    employees = load_employees(filename)

    form = EmployeeForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            employee = add_employee(
                employees,
                form.cleaned_data["name"],
                form.cleaned_data["position"],
            )
            save_employees(
                filename,
                employees,
            )
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            return redirect(
                "employee_detail",
                employee_id=employee.id,
            )

    return form_page(
        request,
        "Добавить сотрудника",
        form,
        "/employees/",
    )


@require_http_methods(["GET", "POST"])
def employee_edit(request, employee_id):
    """Изменить сотрудника или удалить его."""
    data_dir = settings.BASE_DIR / "data"
    filename = data_dir / "employees.json"

    employees = load_employees(filename)
    employee = find_employee(
        employees,
        employee_id,
    )

    if employee is None:
        return HttpResponse(
            page(
                "Сотрудник не найден",
                "<h1>Сотрудник не найден</h1>",
            ),
            status=404,
        )

    form = EmployeeForm(
        request.POST if request.method == "POST" else None,
        initial={
            "name": employee.name,
            "position": employee.position,
        },
    )

    if request.method == "POST":
        action = request.POST.get("action", "save")

        if action == "delete":
            requests = load_requests(
                data_dir / "requests.json",
                employees,
            )
            linked_requests = find_requests_by_employee(
                requests,
                employee.id,
            )

            if linked_requests:
                form.add_error(
                    None,
                    "Нельзя удалить сотрудника: "
                    "с ним связаны заявки на командировки.",
                )
            else:
                remaining = [
                    item
                    for item in employees
                    if item.id != employee.id
                ]

                try:
                    save_employees(filename, remaining)
                except ValueError as error:
                    form.add_error(None, str(error))
                else:
                    return redirect("employee_list")

        elif form.is_valid():
            try:
                updated_employee = Employee(
                    employee.id,
                    form.cleaned_data["name"],
                    form.cleaned_data["position"],
                )

                updated_employees = [
                    updated_employee
                    if item.id == employee.id
                    else item
                    for item in employees
                ]

                save_employees(
                    filename,
                    updated_employees,
                )
            except ValueError as error:
                form.add_error(None, str(error))
            else:
                return redirect(
                    "employee_detail",
                    employee_id=employee.id,
                )

    delete_button = """
    <button type="submit"
            name="action"
            value="delete"
            formnovalidate
            class="btn btn-outline-danger ms-sm-auto"
            onclick="return confirm('Удалить сотрудника?');">
        Удалить сотрудника
    </button>
    """

    return form_page(
        request,
        "Редактировать сотрудника",
        form,
        f"/employees/{employee.id}/",
        delete_button,
    )