from django.shortcuts import render

from employees.models import Employee
from trip_requests.models import TravelRequest
from trip_requests.queries import approved_totals


def index(request):
    totals = approved_totals()
    return render(request, "homepage/index.html", {
        "employees": Employee.objects.all(),
        "statistics": {
            "total": TravelRequest.objects.count(),
            "approved": totals["approved_count"],
            "approved_cost": totals["approved_cost"],
        },
    })


def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)
