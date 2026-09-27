from datetime import date

from trips import calculate_total_cost, calculate_trip_days


def find_request(requests: list[dict], request_id: int) -> dict:
    """Найти заявку по номеру."""
    for request in requests:
        if request["id"] == request_id:
            return request

    raise ValueError("Заявка с таким номером не найдена")


def find_requests_by_employee(
    requests: list[dict],
    employee_id: int,
) -> list[dict]:
    """Найти все заявки сотрудника."""
    result = []

    for request in requests:
        if request["employee_id"] == employee_id:
            result.append(request)

    return result


def sort_requests_by_date(requests: list[dict]) -> list[dict]:
    """Вернуть новый список заявок по дате начала поездки."""
    return sorted(
        requests,
        key=lambda item: item["trip"]["start_date"],
    )


def is_employee_available(
    requests: list[dict],
    employee_id: int,
    start_date: date,
    end_date: date,
    exclude_request_id: int,
) -> bool:
    """Проверить пересечения с уже одобренными поездками."""
    for request in requests:
        if request["id"] == exclude_request_id:
            continue

        if request["employee_id"] != employee_id:
            continue

        if request["approval"]["status"] != "одобрена":
            continue

        trip = request["trip"]
        other_start = date.fromisoformat(trip["start_date"])
        other_end = date.fromisoformat(trip["end_date"])

        if start_date <= other_end and other_start <= end_date:
            return False

    return True


def approval_status_check(
    approved: bool | None,
    total_cost: float,
    budget_limit: float,
) -> str:
    """Определить статус заявки по решению и бюджету."""
    if approved is None:
        return "на рассмотрении"

    if not approved or total_cost > budget_limit:
        return "отклонена"

    return "одобрена"


def create_request(
    requests: list[dict],
    employee_id: int,
    destination: str,
    purpose: str,
    start_date: date,
    end_date: date,
    travel_cost: float,
    hotel_cost: float,
    daily_allowance: float,
    budget_limit: float,
) -> dict:
    """Создать новую заявку с рассчитанной стоимостью."""
    if not destination.strip() or not purpose.strip():
        raise ValueError("Укажите место и цель командировки")

    if budget_limit < 0:
        raise ValueError("Лимит бюджета не может быть отрицательным")

    days = calculate_trip_days(start_date, end_date)

    total_cost = calculate_total_cost(
        travel_cost,
        hotel_cost,
        daily_allowance,
        days,
    )

    request_id = max(
        (item["id"] for item in requests),
        default=0,
    ) + 1

    request = {
        "id": request_id,
        "employee_id": employee_id,
        "trip": {
            "destination": destination.strip(),
            "purpose": purpose.strip(),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "travel_cost": travel_cost,
            "hotel_cost": hotel_cost,
            "daily_allowance": daily_allowance,
        },
        "total_cost": total_cost,
        "budget_limit": budget_limit,
        "approval": {
            "status": approval_status_check(
                None,
                total_cost,
                budget_limit,
            )
        },
    }

    requests.append(request)
    return request


def approve_request(
    requests: list[dict],
    request_id: int,
    approved: bool,
) -> dict:
    """Записать решение после проверки бюджета и дат."""
    request = find_request(requests, request_id)

    if request["approval"]["status"] != "на рассмотрении":
        raise ValueError("Эта заявка уже рассмотрена или отменена")

    if approved:
        if request["total_cost"] > request["budget_limit"]:
            raise ValueError(
                "Стоимость поездки превышает лимит бюджета"
            )

        trip = request["trip"]

        if not is_employee_available(
            requests,
            request["employee_id"],
            date.fromisoformat(trip["start_date"]),
            date.fromisoformat(trip["end_date"]),
            request_id,
        ):
            raise ValueError(
                "У сотрудника уже есть поездка на эти даты"
            )

    request["approval"]["status"] = approval_status_check(
        approved,
        request["total_cost"],
        request["budget_limit"],
    )

    return request


def get_request_statistics(requests: list[dict]) -> dict:
    """Подсчитать заявки и стоимость одобренных поездок."""
    approved = 0
    total_cost = 0.0

    for request in requests:
        if request["approval"]["status"] == "одобрена":
            approved += 1
            total_cost += request["total_cost"]

    return {
        "total": len(requests),
        "approved": approved,
        "approved_cost": round(total_cost, 2),
    }