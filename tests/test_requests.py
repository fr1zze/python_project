from datetime import date

import pytest

from employees import Employee
from travel_requests import (
    create_request,
    find_requests_by_employee,
    get_request_statistics,
    sort_requests_by_date,
)
from trips import Trip


def test_request_links_objects():
    employee = Employee(101, "Иванов Иван", "Разработчик")
    trip = Trip(
        "Москва", "Встреча", date(2026, 10, 1), date(2026, 10, 4),
        8000, 5000, 3000,
    )
    requests = []
    request = create_request(requests, employee, trip, 55000)

    assert requests == [request]
    assert request.employee is employee
    assert request.trip is trip
    assert request.approval.status == "на рассмотрении"


def test_approval_changes_status():
    employee = Employee(101, "Иванов Иван", "Разработчик")
    trip = Trip(
        "Москва", "Встреча", date(2026, 10, 1), date(2026, 10, 4),
        8000, 5000, 3000,
    )
    requests = []
    request = create_request(requests, employee, trip, 55000)

    request.approve(requests, True)

    assert request.approval.status == "одобрена"
    assert get_request_statistics(requests)["approved"] == 1


def test_budget_limit():
    employee = Employee(101, "Иванов Иван", "Разработчик")
    trip = Trip(
        "Москва", "Встреча", date(2026, 10, 1), date(2026, 10, 4),
        8000, 5000, 3000,
    )
    requests = []
    request = create_request(requests, employee, trip, 20000)

    with pytest.raises(ValueError):
        request.approve(requests, True)

    assert request.approval.status == "на рассмотрении"


def test_overlapping_approved_trips():
    employee = Employee(101, "Иванов Иван", "Разработчик")
    first_trip = Trip(
        "Москва", "Встреча", date(2026, 10, 1), date(2026, 10, 4),
        8000, 5000, 3000,
    )
    second_trip = Trip(
        "Казань", "Форум", date(2026, 10, 4), date(2026, 10, 6),
        4000, 5000, 2000,
    )
    requests = []
    first = create_request(requests, employee, first_trip, 55000)
    second = create_request(requests, employee, second_trip, 55000)

    first.approve(requests, True)

    with pytest.raises(ValueError):
        second.approve(requests, True)

    assert second.approval.status == "на рассмотрении"


def test_find_and_sort_requests():
    employee = Employee(101, "Иванов Иван", "Разработчик")
    late_trip = Trip(
        "Москва", "Встреча", date(2026, 10, 10), date(2026, 10, 12),
        8000, 5000, 3000,
    )
    early_trip = Trip(
        "Казань", "Форум", date(2026, 10, 1), date(2026, 10, 2),
        4000, 5000, 2000,
    )
    requests = []
    late = create_request(requests, employee, late_trip, 55000)
    early = create_request(requests, employee, early_trip, 55000)

    assert find_requests_by_employee(requests, 101) == requests
    assert sort_requests_by_date(requests) == [early, late]