from employees.models import Employee


def site_info(request):
    return {
        "site_name": "Система учёта заявок на командировки",
        "site_employee_count": Employee.objects.count(),
    }
