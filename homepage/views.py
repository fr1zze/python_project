from django.conf import settings
from django.shortcuts import render

from models.travel_requests import get_request_statistics
from storage import load_employees, load_requests


def index(request):
    """Показать статистику проекта."""
    data_dir = settings.BASE_DIR / "data"

    employees = load_employees(
        data_dir / "employees.json"
    )
    requests = load_requests(
        data_dir / "requests.json",
        employees,
    )

    context = {
        "employees": employees,
        "statistics": get_request_statistics(requests),
    }

    return render(
        request,
        "homepage/index.html",
        context,
    )


def page_not_found(request, exception=None):
    """Показать общую страницу ошибки 404."""
    return render(
        request,
        "404.html",
        status=404,
    )