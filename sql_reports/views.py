"""Прежние адреса SQL-раздела теперь получают данные через ORM."""
from datetime import date

from django.db.models import Count
from django.shortcuts import render

from employees.models import Employee
from trip_requests.models import Approval, TravelRequest, Trip
from trip_requests.queries import (
    approved_totals, available_employees, employee_counts, related_requests,
)

from .forms import EmployeeFilterForm, SearchForm, StatisticsForm


def make_table(title, columns, headers, rows):
    return {
        "title": title, "headers": headers,
        "rows": [[row[column] for column in columns] for row in rows],
    }


def employee_list(request):
    table = make_table(
        "Сотрудники", ("id", "name", "position"),
        ("ID", "ФИО", "Должность"),
        Employee.objects.values("id", "name", "position"),
    )
    return render(request, "sql_reports/table.html", {"table": table})


def trips_table(rows):
    return make_table(
        "Поездки", ("id", "destination", "purpose", "start_date", "end_date"),
        ("ID", "Направление", "Цель", "Начало", "Окончание"), rows,
    )


def trip_list(request):
    return render(request, "sql_reports/table.html", {
        "table": trips_table(Trip.objects.values()),
    })


def request_list(request):
    form = EmployeeFilterForm(request.GET or None)
    queryset = related_requests()
    if form.is_bound:
        if form.is_valid():
            if form.cleaned_data["employee_id"] is not None:
                queryset = queryset.filter(
                    employee_id=form.cleaned_data["employee_id"],
                )
        else:
            queryset = queryset.none()
    rows = [{
        "id": item.pk, "employee_name": item.employee.name,
        "destination": item.trip.destination,
        "start_date": item.trip.start_date, "end_date": item.trip.end_date,
        "status": item.approval.status, "budget_limit": item.budget_limit,
    } for item in queryset]
    return render(request, "sql_reports/requests.html", {
        "form": form,
        "table": make_table(
            "Заявки", ("id", "employee_name", "destination", "start_date",
                       "end_date", "status", "budget_limit"),
            ("ID", "Сотрудник", "Направление", "Начало", "Окончание",
             "Статус", "Бюджет"), rows,
        ),
        "approved": make_table(
            "Одобренные заявки", ("request_id", "status"),
            ("ID заявки", "Статус"), Approval.objects.filter(
                status=Approval.Status.APPROVED,
            ).order_by("request_id").values("request_id", "status"),
        ),
    })


def search(request):
    form = SearchForm(request.GET or None,
                      initial={"selected_date": date.today()})
    searched = form.is_bound and form.is_valid()
    trips, employees = [], []
    destination = ""
    if searched:
        destination = form.cleaned_data["destination"]
        if destination:
            trips = Trip.objects.filter(
                destination__icontains=destination,
            ).values()
        employees = available_employees(
            form.cleaned_data["selected_date"],
        ).values("id", "name", "position")
    return render(request, "sql_reports/search.html", {
        "form": form, "searched": searched,
        "has_destination": bool(destination),
        "trips_table": trips_table(trips),
        "employees_table": make_table(
            "Сотрудники без одобренной поездки на дату",
            ("id", "name", "position"), ("ID", "ФИО", "Должность"), employees,
        ),
    })


def statistics(request):
    form = StatisticsForm(request.GET or None, initial={"minimum": 0})
    minimum = 0
    valid = True
    if form.is_bound:
        valid = form.is_valid()
        if valid:
            minimum = form.cleaned_data["minimum"]
    counts = employee_counts()
    context = {
        "form": form,
        "counts": {
            "employees_count": Employee.objects.count(),
            "trips_count": Trip.objects.count(),
            "requests_count": TravelRequest.objects.count(),
            "approvals_count": Approval.objects.count(),
        },
        "totals": approved_totals(),
        "by_employee": make_table(
            "Количество заявок по сотрудникам",
            ("id", "name", "request_count"),
            ("ID", "ФИО", "Количество заявок"),
            counts.values("id", "name", "request_count"),
        ),
        "by_status": make_table(
            "Количество заявок по статусам", ("status", "request_count"),
            ("Статус", "Количество"),
            Approval.objects.values("status").annotate(
                request_count=Count("pk"),
            ).order_by("status"),
        ),
        "above_threshold": make_table(
            "Сотрудники с числом заявок больше порога",
            ("id", "name", "request_count"),
            ("ID", "ФИО", "Количество заявок"),
            counts.filter(request_count__gt=minimum).values(
                "id", "name", "request_count",
            ) if valid else [],
        ),
    }
    return render(request, "sql_reports/statistics.html", context)
