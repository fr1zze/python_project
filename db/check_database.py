import json

from db.database import BASE_DIR, fetch_all, get_connection


def check_database() -> None:
    """Проверить импорт и выполнение запросов."""
    data_dir = BASE_DIR / "data"

    employees = json.loads(
        (data_dir / "employees.json").read_text(
            encoding="utf-8"
        )
    )
    requests = json.loads(
        (data_dir / "requests.json").read_text(
            encoding="utf-8"
        )
    )

    counts = fetch_all("counts")[0]

    expected = {
        "employees_count": len(employees),
        "trips_count": len(requests),
        "requests_count": len(requests),
        "approvals_count": len(requests),
    }

    for column, expected_count in expected.items():
        actual_count = counts[column]

        if actual_count != expected_count:
            raise ValueError(
                f"{column}: ожидалось {expected_count}, "
                f"получено {actual_count}"
            )

    with get_connection() as connection:
        errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if errors:
            raise ValueError(
                f"Нарушены внешние ключи: {errors}"
            )

    employee_id = employees[0]["id"] if employees else 1

    checks = [
        ("employees", ()),
        ("trips", ()),
        ("approved_requests", ("одобрена",)),
        ("trips_by_destination", ("%Москва%",)),
        ("requests_details", ()),
        ("employee_requests", (employee_id,)),
        ("counts", ()),
        ("approved_totals", ("одобрена",)),
        ("requests_by_employee", ()),
        ("requests_by_status", ()),
        ("employees_above_threshold", (0,)),
        ("available_employees", ("2026-02-15",)),
    ]

    for query_name, parameters in checks:
        rows = fetch_all(query_name, parameters)
        print(f"{query_name}: строк {len(rows)}")

    print("Количество записей совпадает с JSON.")
    print("Нарушений внешних ключей нет.")
    print("Все 12 запросов выполнены.")


if __name__ == "__main__":
    check_database()