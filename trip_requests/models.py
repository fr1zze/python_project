from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


def money_field(label):
    return models.DecimalField(
        label, max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )


class Trip(models.Model):
    """Поездка с включительными датами и денежными расходами."""

    destination = models.CharField("Направление", max_length=150)
    purpose = models.TextField("Цель", max_length=500)
    start_date = models.DateField("Начало")
    end_date = models.DateField("Окончание")
    travel_cost = money_field("Проезд")
    hotel_cost = money_field("Проживание")
    daily_allowance = money_field("Суточные за день")

    class Meta:
        ordering = ("start_date", "id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="trip_dates_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(travel_cost__gte=0, hotel_cost__gte=0,
                                   daily_allowance__gte=0),
                name="trip_costs_nonnegative",
            ),
        ]

    def clean(self):
        super().clean()
        if (self.start_date and self.end_date
                and self.end_date < self.start_date):
            raise ValidationError("Дата окончания раньше даты начала.")

    def calculate_days(self):
        return (self.end_date - self.start_date).days + 1

    def calculate_total_cost(self):
        return (self.travel_cost + self.hotel_cost
                + self.daily_allowance * self.calculate_days())

    def __str__(self):
        return self.destination


class TravelRequest(models.Model):
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT,
        related_name="travel_requests",
    )
    trip = models.OneToOneField(
        Trip, on_delete=models.PROTECT, related_name="travel_request",
    )
    budget_limit = money_field("Лимит бюджета")

    class Meta:
        ordering = ("trip__start_date", "id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(budget_limit__gte=0),
                name="request_budget_nonnegative",
            ),
        ]

    def validate_approved(self):
        """Правила для одобренной заявки, включая её редактирование."""
        if self.trip.calculate_total_cost() > self.budget_limit:
            raise ValidationError("Стоимость превышает лимит бюджета.")
        conflicts = TravelRequest.objects.filter(
            employee_id=self.employee_id,
            approval__status=Approval.Status.APPROVED,
            trip__start_date__lte=self.trip.end_date,
            trip__end_date__gte=self.trip.start_date,
        ).exclude(pk=self.pk)
        if conflicts.exists():
            raise ValidationError("У сотрудника есть поездка на эти даты.")

    def __str__(self):
        return f"Заявка №{self.pk}"


class Approval(models.Model):
    class Status(models.TextChoices):
        PENDING = "на рассмотрении", "На рассмотрении"
        APPROVED = "одобрена", "Одобрена"
        REJECTED = "отклонена", "Отклонена"
        CANCELLED = "отменена", "Отменена"

    request = models.OneToOneField(
        TravelRequest, on_delete=models.CASCADE, related_name="approval",
    )
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=[
                    "на рассмотрении", "одобрена", "отклонена", "отменена",
                ]), name="approval_status_valid",
            ),
        ]

    def __str__(self):
        return self.status
