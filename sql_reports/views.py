from datetime import date

from django.shortcuts import render

from db.database import fetch_all

from .forms import (
    EmployeeFilterForm,
    SearchForm,
    StatisticsForm,
)


def make_table(title, columns, headers, rows):
    """Подготовить именованные результаты SQL для таблицы."""
    return {
        "title": title,
        "headers": headers,
        "rows": [
            [row[column] for column in columns]
            for row in rows
        ],
    }


def employee_list(request):
    """Показать сотрудников из SQLite."""
    rows = fetch_all("employees")

    table = make_table(
        "Сотрудники из SQLite",
        ("id", "name", "position"),
        ("ID", "ФИО", "Должность"),
        rows,
    )

    return render(
        request,
        "sql_reports/table.html",
        {"table": table},
    )


def trip_list(request):
    """Показать поездки из SQLite."""
    rows = fetch_all("trips")

    table = make_table(
        "Поездки из SQLite",
        (
            "id",
            "destination",
            "purpose",
            "start_date",
            "end_date",
        ),
        (
            "ID",
            "Направление",
            "Цель",
            "Начало",
            "Окончание",
        ),
        rows,
    )

    return render(
        request,
        "sql_reports/table.html",
        {"table": table},
    )


def request_list(request):
    """Показать заявки и фильтр по сотруднику."""
    form = EmployeeFilterForm(request.GET or None)
    rows = fetch_all("requests_details")

    if form.is_bound:
        if form.is_valid():
            employee_id = form.cleaned_data["employee_id"]

            if employee_id is not None:
                rows = fetch_all(
                    "employee_requests",
                    (employee_id,),
                )
        else:
            rows = []

    table = make_table(
        "Заявки из SQLite",
        (
            "id",
            "employee_name",
            "destination",
            "start_date",
            "end_date",
            "status",
            "budget_limit",
        ),
        (
            "ID",
            "Сотрудник",
            "Направление",
            "Начало",
            "Окончание",
            "Статус",
            "Бюджет",
        ),
        rows,
    )

    approved = make_table(
        "Одобренные заявки",
        ("request_id", "status"),
        ("ID заявки", "Статус"),
        fetch_all(
            "approved_requests",
            ("одобрена",),
        ),
    )

    return render(
        request,
        "sql_reports/requests.html",
        {
            "form": form,
            "table": table,
            "approved": approved,
        },
    )


def search(request):
    """Найти поездки и свободных на дату сотрудников."""
    form = SearchForm(
        request.GET if request.GET else None,
        initial={"selected_date": date.today()},
    )

    trips = []
    employees = []
    searched = False

    if form.is_bound and form.is_valid():
        searched = True

        destination = form.cleaned_data["destination"]
        selected_date = form.cleaned_data["selected_date"]

        if destination:
            trips = fetch_all(
                "trips_by_destination",
                (f"%{destination}%",),
            )

        employees = fetch_all(
            "available_employees",
            (selected_date.isoformat(),),
        )

    trips_table = make_table(
        "Поездки по направлению",
        (
            "id",
            "destination",
            "purpose",
            "start_date",
            "end_date",
        ),
        (
            "ID",
            "Направление",
            "Цель",
            "Начало",
            "Окончание",
        ),
        trips,
    )

    employees_table = make_table(
        "Сотрудники без одобренной поездки на дату",
        ("id", "name", "position"),
        ("ID", "ФИО", "Должность"),
        employees,
    )

    return render(
        request,
        "sql_reports/search.html",
        {
            "form": form,
            "searched": searched,
            "has_destination": bool(
                form.cleaned_data.get("destination")
            ) if searched else False,
            "trips_table": trips_table,
            "employees_table": employees_table,
        },
    )


def statistics(request):
    """Показать агрегаты, группировку и HAVING."""
    form = StatisticsForm(
        request.GET if request.GET else None,
        initial={"minimum": 0},
    )

    minimum = 0
    valid_threshold = True

    if form.is_bound:
        if form.is_valid():
            minimum = form.cleaned_data["minimum"]
        else:
            valid_threshold = False

    above_threshold = []

    if valid_threshold:
        above_threshold = fetch_all(
            "employees_above_threshold",
            (minimum,),
        )

    context = {
        "form": form,
        "counts": fetch_all("counts")[0],
        "totals": fetch_all(
            "approved_totals",
            ("одобрена",),
        )[0],
        "by_employee": make_table(
            "Количество заявок по сотрудникам",
            ("id", "name", "request_count"),
            ("ID", "ФИО", "Количество заявок"),
            fetch_all("requests_by_employee"),
        ),
        "by_status": make_table(
            "Количество заявок по статусам",
            ("status", "request_count"),
            ("Статус", "Количество"),
            fetch_all("requests_by_status"),
        ),
        "above_threshold": make_table(
            "Сотрудники, прошедшие условие HAVING",
            ("id", "name", "request_count"),
            ("ID", "ФИО", "Количество заявок"),
            above_threshold,
        ),
    }

    return render(
        request,
        "sql_reports/statistics.html",
        context,
    )