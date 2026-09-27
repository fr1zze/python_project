class Employee:
    """Сотрудник организации."""

    def __init__(
        self,
        employee_id: int,
        name: str,
        position: str,
    ) -> None:
        if not name.strip() or not position.strip():
            raise ValueError(
                "Укажите ФИО и должность сотрудника"
            )

        self.id = employee_id
        self.name = name.strip()
        self.position = position.strip()

    def __str__(self) -> str:
        return f"ID {self.id}: {self.name}, {self.position}"


def find_employee(
    employees: list[Employee],
    employee_id: int,
) -> Employee | None:
    """Найти сотрудника в списке объектов."""
    for employee in employees:
        if employee.id == employee_id:
            return employee

    return None


def add_employee(
    employees: list[Employee],
    name: str,
    position: str,
) -> Employee:
    """Создать сотрудника и добавить его в список."""
    employee_id = max(
        (item.id for item in employees),
        default=0,
    ) + 1

    employee = Employee(
        employee_id,
        name,
        position,
    )

    employees.append(employee)
    return employee