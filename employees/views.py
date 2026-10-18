from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from homepage.views import page_not_found
from models.employees import Employee, add_employee, find_employee
from models.travel_requests import find_requests_by_employee
from storage import load_employees, load_requests, save_employees

from .forms import EmployeeForm


def employee_list(request):
    """Показать список сотрудников."""
    employees = load_employees(
        settings.BASE_DIR / "data" / "employees.json"
    )

    return render(
        request,
        "employees/employee_list.html",
        {"employees": employees},
    )


def employee_detail(request, employee_id):
    """Показать сотрудника и его заявки."""
    data_dir = settings.BASE_DIR / "data"
    employees = load_employees(
        data_dir / "employees.json"
    )
    employee = find_employee(employees, employee_id)

    if employee is None:
        return page_not_found(request)

    requests = load_requests(
        data_dir / "requests.json",
        employees,
    )
    employee_requests = find_requests_by_employee(
        requests,
        employee.id,
    )

    context = {
        "employee": employee,
        "employee_requests": employee_requests,
    }

    return render(
        request,
        "employees/employee_detail.html",
        context,
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
            save_employees(filename, employees)
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            return redirect(
                "employees:detail",
                employee_id=employee.id,
            )

    context = {
        "title": "Добавить сотрудника",
        "form": form,
        "back_url": reverse("employees:list"),
    }

    return render(request, "form.html", context)


@require_http_methods(["GET", "POST"])
def employee_edit(request, employee_id):
    """Изменить сотрудника или удалить его."""
    data_dir = settings.BASE_DIR / "data"
    filename = data_dir / "employees.json"

    employees = load_employees(filename)
    employee = find_employee(employees, employee_id)

    if employee is None:
        return page_not_found(request)

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
                    return redirect("employees:list")

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
                    "employees:detail",
                    employee_id=employee.id,
                )

    context = {
        "title": "Редактировать сотрудника",
        "form": form,
        "back_url": reverse(
            "employees:detail",
            kwargs={"employee_id": employee.id},
        ),
        "can_delete": True,
    }

    return render(request, "form.html", context)