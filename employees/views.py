from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import EmployeeForm
from .models import Employee


def employee_list(request):
    return render(request, "employees/employee_list.html", {
        "employees": Employee.objects.all(),
    })


def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    return render(request, "employees/employee_detail.html", {
        "employee": employee,
        "employee_requests": employee.travel_requests.select_related(
            "trip", "approval",
        ),
    })


@require_http_methods(["GET", "POST"])
def employee_create(request):
    form = EmployeeForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        employee = Employee.objects.create(**form.cleaned_data)
        return redirect("employees:detail", employee_id=employee.pk)
    return render(request, "form.html", {
        "title": "Добавить сотрудника", "form": form,
        "back_url": reverse("employees:list"),
    })


@require_http_methods(["GET", "POST"])
def employee_edit(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    form = EmployeeForm(
        request.POST if request.method == "POST" else None,
        initial={"name": employee.name, "position": employee.position},
    )
    if request.method == "POST":
        if request.POST.get("action") == "delete":
            # Инициализировать ошибки перед add_error().
            form.is_valid()
            try:
                employee.delete()
            except ProtectedError:
                form.add_error(None, "Нельзя удалить сотрудника: "
                               "с ним связаны заявки на командировки.")
            else:
                return redirect("employees:list")
        elif form.is_valid():
            employee.name = form.cleaned_data["name"]
            employee.position = form.cleaned_data["position"]
            employee.full_clean()
            employee.save()
            return redirect("employees:detail", employee_id=employee.pk)
    return render(request, "form.html", {
        "title": "Редактировать сотрудника", "form": form,
        "back_url": reverse("employees:detail", kwargs={
            "employee_id": employee.pk,
        }), "can_delete": True,
    })
