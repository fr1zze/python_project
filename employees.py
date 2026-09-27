def find_employee(
    employees: list[dict],
    employee_id: int,
) -> dict | None:
    """Поиск сотрудника по идентификатору."""
    for employee in employees:
        if employee["id"] == employee_id:
            return employee

    return None


def add_employee(
    employees: list[dict],
    name: str,
    position: str,
) -> dict:
    """Добавить сотрудника и вернуть его данные."""
    name = name.strip()
    position = position.strip()

    if not name or not position:
        raise ValueError("Укажите имя и должность сотрудника")

    employee_id = max(
        (employee["id"] for employee in employees),
        default=0,
    ) + 1

    employee = {
        "id": employee_id,
        "name": name,
        "position": position,
    }

    employees.append(employee)
    return employee