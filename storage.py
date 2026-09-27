import json

from datetime import date
from pathlib import Path

from approval import Approval
from employees import Employee, find_employee
from travel_requests import TravelRequest
from trips import Trip


def load_data(filename: Path) -> list[dict]:
    """Прочитать список словарей из JSON."""
    try:
        with filename.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except FileNotFoundError:
        return []

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise ValueError(
            f"Не удалось прочитать {filename}: {error}"
        ) from error

    if not isinstance(data, list):
        raise ValueError(
            f"В файле {filename} должен быть список"
        )

    return data


def save_data(
    filename: Path,
    data: list[dict],
) -> None:
    """Записать список словарей в JSON."""
    try:
        filename.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with filename.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except OSError as error:
        raise ValueError(
            f"Не удалось сохранить {filename}: {error}"
        ) from error


def load_employees(
    filename: Path,
) -> list[Employee]:
    """Создать объекты сотрудников из JSON."""
    try:
        return [
            Employee(
                item["id"],
                item["name"],
                item["position"],
            )
            for item in load_data(filename)
        ]

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"Некорректные данные в {filename}"
        ) from error


def save_employees(
    filename: Path,
    employees: list[Employee],
) -> None:
    """Сохранить сотрудников в JSON."""
    data = [
        {
            "id": item.id,
            "name": item.name,
            "position": item.position,
        }
        for item in employees
    ]

    save_data(filename, data)


def load_requests(
    filename: Path,
    employees: list[Employee],
) -> list[TravelRequest]:
    """Создать заявки и связать их с сотрудниками."""
    requests = []

    for item in load_data(filename):
        try:
            employee = find_employee(
                employees,
                item["employee_id"],
            )

            if employee is None:
                raise ValueError(
                    "Сотрудник заявки не найден"
                )

            trip_data = item["trip"]

            trip = Trip(
                trip_data["destination"],
                trip_data["purpose"],
                date.fromisoformat(
                    trip_data["start_date"]
                ),
                date.fromisoformat(
                    trip_data["end_date"]
                ),
                trip_data["travel_cost"],
                trip_data["hotel_cost"],
                trip_data["daily_allowance"],
            )

            request = TravelRequest(
                item["id"],
                employee,
                trip,
                item["budget_limit"],
                Approval(
                    item["approval"]["status"]
                ),
            )

            requests.append(request)

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"Некорректная заявка в {filename}"
            ) from error

    return requests


def save_requests(
    filename: Path,
    requests: list[TravelRequest],
) -> None:
    """Преобразовать заявки в словари и сохранить."""
    data = []

    for request in requests:
        trip = request.trip

        data.append(
            {
                "id": request.id,
                "employee_id": request.employee.id,
                "trip": {
                    "destination": trip.destination,
                    "purpose": trip.purpose,
                    "start_date": (
                        trip.start_date.isoformat()
                    ),
                    "end_date": (
                        trip.end_date.isoformat()
                    ),
                    "travel_cost": trip.travel_cost,
                    "hotel_cost": trip.hotel_cost,
                    "daily_allowance": (
                        trip.daily_allowance
                    ),
                },
                "total_cost": (
                    trip.calculate_total_cost()
                ),
                "budget_limit": request.budget_limit,
                "approval": {
                    "status": request.approval.status,
                },
            }
        )

    save_data(filename, data)