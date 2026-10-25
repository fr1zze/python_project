from db.database import (
    BASE_DIR,
    SCHEMA_PATH,
    get_connection,
)
from storage import load_employees, load_requests


def import_json() -> None:
    """Перенести текущие данные JSON в SQLite."""
    employees_path = BASE_DIR / "data" / "employees.json"
    requests_path = BASE_DIR / "data" / "requests.json"

    if not employees_path.is_file():
        raise FileNotFoundError(employees_path)

    if not requests_path.is_file():
        raise FileNotFoundError(requests_path)

    employees = load_employees(employees_path)
    requests = load_requests(requests_path, employees)

    employee_rows = [
        (employee.id, employee.name, employee.position)
        for employee in employees
    ]

    trip_rows = [
        (
            item.id,
            item.trip.destination,
            item.trip.purpose,
            item.trip.start_date.isoformat(),
            item.trip.end_date.isoformat(),
            item.trip.travel_cost,
            item.trip.hotel_cost,
            item.trip.daily_allowance,
        )
        for item in requests
    ]

    request_rows = [
        (
            item.id,
            item.employee.id,
            item.id,
            item.budget_limit,
        )
        for item in requests
    ]

    approval_rows = [
        (
            item.id,
            item.id,
            item.approval.status,
        )
        for item in requests
    ]

    with get_connection() as connection:
        connection.executescript(
            SCHEMA_PATH.read_text(encoding="utf-8")
        )

        try:
            connection.execute("BEGIN")

            connection.execute("DELETE FROM approvals")
            connection.execute("DELETE FROM travel_requests")
            connection.execute("DELETE FROM trips")
            connection.execute("DELETE FROM employees")

            connection.executemany(
                """
                INSERT INTO employees (id, name, position)
                VALUES (?, ?, ?)
                """,
                employee_rows,
            )

            connection.executemany(
                """
                INSERT INTO trips (
                    id,
                    destination,
                    purpose,
                    start_date,
                    end_date,
                    travel_cost,
                    hotel_cost,
                    daily_allowance
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                trip_rows,
            )

            connection.executemany(
                """
                INSERT INTO travel_requests (
                    id,
                    employee_id,
                    trip_id,
                    budget_limit
                )
                VALUES (?, ?, ?, ?)
                """,
                request_rows,
            )

            connection.executemany(
                """
                INSERT INTO approvals (
                    id,
                    request_id,
                    status
                )
                VALUES (?, ?, ?)
                """,
                approval_rows,
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    print(f"Сотрудников: {len(employee_rows)}")
    print(f"Поездок: {len(trip_rows)}")
    print(f"Заявок: {len(request_rows)}")
    print(f"Согласований: {len(approval_rows)}")
    print("Импорт завершён.")


if __name__ == "__main__":
    import_json()