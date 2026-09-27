from employees import Employee, add_employee, find_employee


def test_employee_attributes():
    employee = Employee(101, "Иванов Иван", "Разработчик")

    assert employee.id == 101
    assert employee.name == "Иванов Иван"
    assert employee.position == "Разработчик"
    assert "Иванов Иван" in str(employee)


def test_add_and_find_employee():
    employees = []
    employee = add_employee(employees, "Петров Пётр", "Аналитик")

    assert len(employees) == 1
    assert find_employee(employees, employee.id) is employee