from datetime import date

from travel_requests import (
    create_request,
    find_requests_by_employee,
)
from trips import calculate_total_cost, calculate_trip_days


def test_calculate_trip_days():
    start = date(2026, 10, 1)
    end = date(2026, 10, 4)

    assert calculate_trip_days(start, end) == 4


def test_calculate_total_cost():
    total = calculate_total_cost(8000, 5000, 3000, 4)

    assert total == 25000


def test_create_request():
    requests = []

    create_request(
        requests,
        101,
        "Москва",
        "Встреча",
        date(2026, 10, 1),
        date(2026, 10, 4),
        8000,
        5000,
        3000,
        55000,
    )

    assert len(requests) == 1


def test_find_requests_by_employee():
    requests = [
        {"employee_id": 101},
        {"employee_id": 102},
    ]

    found = find_requests_by_employee(requests, 101)

    assert len(found) == 1