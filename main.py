from datetime import datetime


# Данные сотрудника
employee_id = 101
employee_name = "Шлапаков Максим"
employee_position = "Разработчик"

# Данные поездки
destination = "Москва"
trip_purpose = "Бизнес-встреча"

start_date = datetime(2026, 2, 12)
end_date = datetime(2026, 2, 24)
start_date_str = start_date.strftime("%d.%m.%Y")
end_date_str = end_date.strftime("%d.%m.%Y")

travel_cost = 8000.00
hotel_cost = 5000.00
daily_salary = 3000.00

# Данные заявки
request_id = 404
budget_limit = 55000.00

# Данные соглосования
approval_status = True


# Проверка правительности дат поездки
def check_trip_dates(start_date, end_date):
    if end_date < start_date:
        return False
    elif start_date >= end_date:
        return False
    
    return True


# Расчёт продолжительности командировки
def calculate_trip_days(start_date, end_date):
    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        return 0
    return total_days


# Расчёт общей стоимости командировки
def calculate_total_cost(travel_cost, hotel_cost, daily_salary, trip_days):
    total_cost = travel_cost + hotel_cost + (daily_salary * trip_days)
    return total_cost


# Определение статуса согласования заявки
def approval_status_check(approval_status, total_cost, budget_limit):
    if approval_status and total_cost <= budget_limit:
        return "Заявка одобрена"
    elif not approval_status or total_cost > budget_limit:
        return "Заявка отклонена"
    return "Заявка находится на рассмотрении"


trip_date_valid = check_trip_dates(start_date, end_date)
trip_days = calculate_trip_days(start_date, end_date)
total_cost = calculate_total_cost(travel_cost, hotel_cost, daily_salary, 
                                  trip_days)
approval_result = approval_status_check(approval_status, total_cost, 
                                        budget_limit)

print("Система учета заявок на командировки")
print("--------------------------------------------")

print(f"Номер заявки: {request_id}")
print(f"Сотрудник: {employee_name} (ID: {employee_id})")
print(f"Должность: {employee_position}")

print()

print(f"Место назначения: {destination}")
print(f"Цель поездки: {trip_purpose}")

if trip_date_valid:
    print(f"Начало поездки: {start_date_str}")
    print(f"Окончание поездки: {end_date_str}")

    print()

    print(f"Продолжительность поездки: {trip_days} дней")
    print(f"Стоимость поездки: {travel_cost:.2f} руб.")
    print(f"Стоимость проживания: {hotel_cost:.2f} руб.")
    print(f"Ежедневная зарплата: {daily_salary:.2f} руб.")
    print(f"Общая стоимость командировки: {total_cost:.2f} руб.")

    print()

    print(f"Статус заявки: {approval_result}")
else:
    print("Ошибка: Даты введены некорректно.")

print("--------------------------------------------")
