from pathlib import Path

from employees import (
    Employee,
    add_employee,
    find_employee,
)
from storage import (
    load_employees,
    load_requests,
    save_employees,
    save_requests,
)
from travel_requests import (
    TravelRequest,
    create_request,
    find_request,
    find_requests_by_employee,
    get_request_statistics,
    sort_requests_by_date,
)
from trips import Trip
from utils import (
    input_date,
    input_float,
    input_int,
)


DATA_DIR = Path(__file__).resolve().parent / "data"

EMPLOYEES_FILE = DATA_DIR / "employees.json"
REQUESTS_FILE = DATA_DIR / "requests.json"


def show_employees(
    employees: list[Employee],
) -> None:
    """Показать список сотрудников."""
    if not employees:
        print("Сотрудники не найдены.")

    for employee in employees:
        print(employee)


def show_requests(
    requests: list[TravelRequest],
) -> None:
    """Показать список заявок."""
    if not requests:
        print("Заявки не найдены.")

    for request in requests:
        print(request)


def main() -> None:
    """Загрузить объекты и показать меню."""
    try:
        employees = load_employees(
            EMPLOYEES_FILE
        )
        requests = load_requests(
            REQUESTS_FILE,
            employees,
        )

    except ValueError as error:
        print(f"Ошибка загрузки: {error}")
        return

    while True:
        print("\n=== Заявки на командировки ===")
        print("1. Показать все заявки")
        print("2. Добавить сотрудника")
        print("3. Создать заявку")
        print("4. Найти заявки сотрудника")
        print("5. Показать заявки по дате")
        print("6. Согласовать или отклонить заявку")
        print("7. Статистика")
        print("8. Показать сотрудников")
        print("0. Выход")

        choice = input(
            "Выберите действие: "
        ).strip()

        try:
            if choice == "0":
                return

            elif choice == "1":
                show_requests(requests)

            elif choice == "2":
                employee = add_employee(
                    employees,
                    input("ФИО: "),
                    input("Должность: "),
                )

                save_employees(
                    EMPLOYEES_FILE,
                    employees,
                )

                print(
                    f"Добавлен сотрудник: {employee}"
                )

            elif choice == "3":
                employee_id = input_int(
                    "ID сотрудника: "
                )

                selected_employee = find_employee(
                    employees,
                    employee_id,
                )

                if selected_employee is None:
                    raise ValueError(
                        "Сотрудник с таким ID не найден"
                    )

                trip = Trip(
                    input("Место назначения: "),
                    input("Цель поездки: "),
                    input_date(
                        "Начало (ДД.ММ.ГГГГ): "
                    ),
                    input_date(
                        "Окончание (ДД.ММ.ГГГГ): "
                    ),
                    input_float(
                        "Стоимость проезда: "
                    ),
                    input_float(
                        "Стоимость проживания: "
                    ),
                    input_float(
                        "Суточные за день: "
                    ),
                )

                request = create_request(
                    requests,
                    employee,
                    trip,
                    input_float(
                        "Лимит бюджета: "
                    ),
                )

                save_requests(
                    REQUESTS_FILE,
                    requests,
                )

                print(
                    f"Создана заявка №{request.id}"
                )

            elif choice == "4":
                employee_id = input_int(
                    "ID сотрудника: "
                )

                found = find_requests_by_employee(
                    requests,
                    employee_id,
                )

                show_requests(found)

            elif choice == "5":
                sorted_requests = (
                    sort_requests_by_date(requests)
                )

                show_requests(sorted_requests)

            elif choice == "6":
                request_id = input_int(
                    "Номер заявки: "
                )

                decision = input(
                    "Одобрить? (д/н): "
                ).strip().lower()

                if decision not in ("д", "н"):
                    raise ValueError(
                        "Введите д или н"
                    )

                request = find_request(
                    requests,
                    request_id,
                )

                request.approve(
                    requests,
                    decision == "д",
                )

                save_requests(
                    REQUESTS_FILE,
                    requests,
                )

                print(
                    f"Статус: {request.approval}"
                )

            elif choice == "7":
                stats = get_request_statistics(
                    requests
                )

                print(
                    f'Всего заявок: {stats["total"]}'
                )
                print(
                    f'Одобрено: {stats["approved"]}'
                )
                print(
                    "Стоимость одобренных: "
                    f'{stats["approved_cost"]:.2f} руб.'
                )

            elif choice == "8":
                show_employees(employees)

            else:
                print(
                    "Такого пункта меню нет."
                )

        except ValueError as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()