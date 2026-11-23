from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Approval, TravelRequest, Trip


class RequestFilterForm(forms.Form):
    employee_id = forms.IntegerField(
        label="ID сотрудника", required=False, min_value=1,
    )
    selected_date = forms.DateField(
        label="Дата поездки", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    status = forms.ChoiceField(
        label="Статус", required=False,
        choices=[("", "Все статусы"), *Approval.Status.choices],
    )
    destination = forms.CharField(
        label="Направление", required=False, max_length=150,
    )
    q = forms.CharField(
        label="Поиск по сотруднику, направлению и цели",
        required=False, max_length=150,
    )
    sort = forms.ChoiceField(
        label="Сортировка", required=False,
        choices=[("date", "Сначала ранние поездки"),
                 ("-date", "Сначала поздние поездки"),
                 ("employee", "По сотруднику (Я–А)"),
                 ("destination", "По направлению")],
    )


class TravelRequestForm(forms.ModelForm):
    """Одна форма для заявки и полей связанной поездки."""

    destination = forms.CharField(
        label="Место назначения",
        max_length=150,
    )

    purpose = forms.CharField(
        label="Цель командировки",
        max_length=500,
        widget=forms.Textarea(
            attrs={"rows": 3}
        ),
    )

    start_date = forms.DateField(
        label="Дата начала",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    end_date = forms.DateField(
        label="Дата окончания",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    travel_cost = forms.DecimalField(
        label="Стоимость проезда, руб.",
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    hotel_cost = forms.DecimalField(
        label="Проживание за всю поездку, руб.",
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    daily_allowance = forms.DecimalField(
        label="Суточные за день, руб.",
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    budget_limit = forms.DecimalField(
        label="Лимит бюджета, руб.",
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    trip_fields = (
        "destination", "purpose", "start_date", "end_date",
        "travel_cost", "hotel_cost", "daily_allowance",
    )

    class Meta:
        model = TravelRequest
        fields = (
            "employee", "destination", "purpose", "start_date", "end_date",
            "travel_cost", "hotel_cost", "daily_allowance", "budget_limit",
        )
        help_texts = {
            "employee": "Выберите сотрудника для командировки.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee"].empty_label = "Выберите сотрудника"
        self.fields["start_date"].help_text = (
            "Новая дата начала не может быть в прошлом."
        )
        self.fields["hotel_cost"].help_text = "Стоимость за всю поездку."
        if self.instance.pk:
            for field in self.trip_fields:
                self.initial[field] = getattr(self.instance.trip, field)
        else:
            self.initial.setdefault("start_date", timezone.localdate())
            self.initial.setdefault("end_date", timezone.localdate())
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"

    def clean_start_date(self):
        value = self.cleaned_data["start_date"]
        # Существующие исторические поездки можно исправить без смены даты.
        original = self.instance.trip.start_date if self.instance.pk else None
        if value < timezone.localdate() and value != original:
            raise ValidationError("Дата начала не может быть в прошлом.")
        return value

    def clean(self):
        data = super().clean()
        if not all(field in data for field in self.trip_fields):
            return data
        trip = self.instance.trip if self.instance.pk else Trip()
        for field in self.trip_fields:
            setattr(trip, field, data[field])
        try:
            trip.full_clean()
        except ValidationError as error:
            if hasattr(error, "message_dict"):
                for field, messages in error.message_dict.items():
                    self.add_error(field if field in self.fields else None,
                                   messages)
            else:
                self.add_error(None, error)
            return data
        self.instance.trip = trip
        if data.get("employee") and "budget_limit" in data:
            candidate = TravelRequest(
                pk=self.instance.pk, employee=data["employee"], trip=trip,
                budget_limit=data["budget_limit"],
            )
            # Любая новая заявка проверяется против уже одобренных поездок.
            candidate.validate_approved()
        return data

    def save(self, commit=True):
        item = super().save(commit=False)
        if commit:
            with transaction.atomic():
                item.trip.full_clean()
                item.validate_approved()
                trip = item.trip
                trip.save()
                item.trip = trip
                item.full_clean()
                item.save()
                self.save_m2m()
                Approval.objects.get_or_create(request=item)
        return item
