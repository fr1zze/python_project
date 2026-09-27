from datetime import date

from trips import Trip


def test_trip_days_and_cost():
    trip = Trip(
        "Москва", "Встреча", date(2026, 10, 1), date(2026, 10, 4),
        8000, 5000, 3000,
    )

    assert trip.destination == "Москва"
    assert trip.calculate_days() == 4
    assert trip.calculate_total_cost() == 25000
    assert "Москва" in str(trip)


def test_trip_overlaps():
    first = Trip(
        "Москва", "Встреча", date(2026, 10, 1), date(2026, 10, 4),
        8000, 5000, 3000,
    )
    second = Trip(
        "Казань", "Форум", date(2026, 10, 4), date(2026, 10, 6),
        4000, 5000, 2000,
    )

    assert first.overlaps(second)