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
        verbose_name = "Поездка"
        verbose_name_plural = "Поездки"
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


class TravelRequestQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(approval__status=Approval.Status.APPROVED)

    def pending(self):
        return self.filter(approval__status=Approval.Status.PENDING)

    def cancelled(self):
        return self.filter(approval__status=Approval.Status.CANCELLED)

    def rejected(self):
        return self.filter(approval__status=Approval.Status.REJECTED)

    def for_date(self, selected_date):
        return self.filter(trip__start_date__lte=selected_date,
                           trip__end_date__gte=selected_date)

    def with_details(self):
        return self.select_related("employee", "trip", "approval")

    def rows(self):
        """Словари для табличного отчёта; JOIN выполняется одним запросом."""
        return self.annotate(
            employee_name=models.F("employee__name"),
            destination=models.F("trip__destination"),
            start_date=models.F("trip__start_date"),
            end_date=models.F("trip__end_date"),
            status=models.F("approval__status"),
        ).values("id", "employee_name", "destination", "start_date",
                 "end_date", "status", "budget_limit")


class TravelRequest(models.Model):
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT,
        related_name="travel_requests",
        verbose_name="Сотрудник",
    )
    trip = models.OneToOneField(
        Trip, on_delete=models.PROTECT, related_name="travel_request",
        verbose_name="Поездка",
    )
    budget_limit = money_field("Лимит бюджета")
    objects = TravelRequestQuerySet.as_manager()

    class Meta:
        verbose_name = "Заявка на командировку"
        verbose_name_plural = "Заявки на командировки"
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
        verbose_name="Заявка",
    )
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:
        verbose_name = "Согласование"
        verbose_name_plural = "Согласования"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=[
                    "на рассмотрении", "одобрена", "отклонена", "отменена",
                ]), name="approval_status_valid",
            ),
        ]

    def __str__(self):
        return self.status
