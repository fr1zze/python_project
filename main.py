from pathlib import Path

from employees import add_employee, find_employee
from storage import load_data, save_data
from travel_requests import (
    approve_request,
    create_request,
    find_requests_by_employee,
    get_request_statistics,
    sort_requests_by_date,
)
from utils import input_date, input_float, input_int


DATA_DIR = Path(__file__).resolve().parent / "data"

EMPLOYEES_FILE = DATA_DIR / "employees.json"
REQUESTS_FILE = DATA_DIR / "requests.json"


def show_requests(
    requests: list[dict],
    employees: list[dict],
) -> None:
    """Показать заявки с именами сотрудников."""
    if not requests:
        print("Заявки не найдены.")
        return

    for request in requests:
        employee = find_employee(
            employees,
            request["employee_id"],
        )

        if employee:
            name = employee["name"]
        else:
            name = "Неизвестный сотрудник"

        trip = request["trip"]

        print(
            f'№{request["id"]}: {name}, '
            f'{trip["destination"]}, '
            f'{trip["start_date"]} — {trip["end_date"]}, '
            f'{request["total_cost"]:.2f} руб., '
            f'{request["approval"]["status"]}'
        )


def show_employees(employees: list[dict]) -> None:
    """Показать список сотрудников."""
    if not employees:
        print("Сотрудники не найдены.")
        return

    for employee in employees:
        print(
            f'ID: {employee["id"]}, '
            f'ФИО: {employee["name"]}, '
            f'должность: {employee["position"]}'
        )


def main() -> None:
    """Загрузить данные и показать консольное меню."""
    try:
        employees = load_data(EMPLOYEES_FILE)
        requests = load_data(REQUESTS_FILE)

    except ValueError as error:
        print(f"Ошибка загрузки: {error}")
        return

    while True:
        print("\n=== Заявки на командировки ===")
        print("1. Показать все заявки")
        print("2. Показать сотрудников")
        print("3. Добавить сотрудника")
        print("4. Создать заявку")
        print("5. Найти заявки сотрудника")
        print("6. Показать заявки по дате")
        print("7. Согласовать или отклонить заявку")
        print("8. Статистика")
        print("0. Выход")

        choice = input("Выберите действие: ").strip()

        try:
            if choice == "0":
                print("Выход из программы...")
                return

            elif choice == "1":
                show_requests(requests, employees)

            elif choice == "2":
                show_employees(employees)   

            elif choice == "3":
                name = input("ФИО: ")
                position = input("Должность: ")

                employee = add_employee(
                    employees,
                    name,
                    position,
                )

                save_data(EMPLOYEES_FILE, employees)

                print(
                    f'Сотрудник добавлен, ID: {employee["id"]}'
                )

            elif choice == "4":
                employee_id = input_int(
                    "ID сотрудника: "
                )

                if find_employee(
                    employees,
                    employee_id,
                ) is None:
                    raise ValueError(
                        "Сотрудник с таким ID не найден"
                    )

                destination = input(
                    "Место назначения: "
                )
                purpose = input(
                    "Цель поездки: "
                )

                start_date = input_date(
                    "Начало (ДД.ММ.ГГГГ): "
                )
                end_date = input_date(
                    "Окончание (ДД.ММ.ГГГГ): "
                )

                travel_cost = input_float(
                    "Стоимость проезда: "
                )
                hotel_cost = input_float(
                    "Стоимость проживания: "
                )
                daily_allowance = input_float(
                    "Суточные за день: "
                )
                budget_limit = input_float(
                    "Лимит бюджета: "
                )

                request = create_request(
                    requests,
                    employee_id,
                    destination,
                    purpose,
                    start_date,
                    end_date,
                    travel_cost,
                    hotel_cost,
                    daily_allowance,
                    budget_limit,
                )

                save_data(REQUESTS_FILE, requests)

                print(
                    f'Заявка №{request["id"]} создана.'
                )

            elif choice == "5":
                employee_id = input_int(
                    "ID сотрудника: "
                )

                found = find_requests_by_employee(
                    requests,
                    employee_id,
                )

                show_requests(found, employees)

            elif choice == "6":
                sorted_requests = sort_requests_by_date(
                    requests
                )

                show_requests(
                    sorted_requests,
                    employees,
                )

            elif choice == "7":
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

                request = approve_request(
                    requests,
                    request_id,
                    decision == "д",
                )

                save_data(REQUESTS_FILE, requests)

                print(
                    f'Статус: '
                    f'{request["approval"]["status"]}'
                )

            elif choice == "8":
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

            else:
                print("Такого пункта меню нет.")

        except ValueError as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()