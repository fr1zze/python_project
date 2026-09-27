from datetime import date


def check_trip_dates(start_date: date, end_date: date) -> bool:
    """Проверка порядок дат командировки."""
    return end_date >= start_date


def calculate_trip_days(start_date: date, end_date: date) -> int:
    """Расчёт продолжительности командировки."""
    if not check_trip_dates(start_date, end_date):
        raise ValueError("Дата окончания раньше даты начала")

    return (end_date - start_date).days + 1


def calculate_total_cost(
    travel_cost: float,
    hotel_cost: float,
    daily_allowance: float,
    trip_days: int,
) -> float:
    """Расчёт общей стоимости командировки."""
    if min(travel_cost, hotel_cost, daily_allowance) < 0 or trip_days < 1:
        raise ValueError("Расходы не могут быть отрицательными")

    return round(
        travel_cost + hotel_cost + daily_allowance * trip_days,
        2,
    )