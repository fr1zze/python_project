"""Общие ORM-выборки для страниц и статистики."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Count, DecimalField, ExpressionWrapper, F, IntegerField, Q, Sum, Value,
)

from employees.models import Employee

from .models import Approval, TravelRequest


def related_requests():
    return TravelRequest.objects.select_related("employee", "trip", "approval")


def available_employees(selected_date):
    busy = TravelRequest.objects.filter(
        approval__status=Approval.Status.APPROVED,
        trip__start_date__lte=selected_date,
        trip__end_date__gte=selected_date,
    ).values("employee_id")
    return Employee.objects.exclude(pk__in=busy)


def approved_totals():
    # Разность DateField хранится Django как длительность; делим на сутки.
    days = ExpressionWrapper(
        (F("trip__end_date") - F("trip__start_date"))
        / Value(timedelta(days=1)) + Value(1),
        output_field=IntegerField(),
    )
    cost = ExpressionWrapper(
        F("trip__travel_cost") + F("trip__hotel_cost")
        + F("trip__daily_allowance") * days,
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )
    return TravelRequest.objects.filter(
        approval__status=Approval.Status.APPROVED,
    ).aggregate(
        approved_count=Count("pk"),
        approved_cost=Sum(cost, default=Decimal("0.00")),
    )


def employee_counts():
    return Employee.objects.annotate(
        request_count=Count("travel_requests"),
    ).order_by("-request_count", "id")


def filter_requests(queryset, data):
    if data.get("employee_id"):
        queryset = queryset.filter(employee_id=data["employee_id"])
    if data.get("selected_date"):
        queryset = queryset.filter(
            trip__start_date__lte=data["selected_date"],
            trip__end_date__gte=data["selected_date"],
        )
    if data.get("status"):
        queryset = queryset.filter(approval__status=data["status"])
    if data.get("destination"):
        queryset = queryset.filter(
            trip__destination__icontains=data["destination"],
        )
    if data.get("q"):
        queryset = queryset.filter(
            Q(employee__name__icontains=data["q"])
            | Q(trip__destination__icontains=data["q"])
            | Q(trip__purpose__icontains=data["q"]),
        )
    return queryset
