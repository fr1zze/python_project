from django import forms

from .models import Approval


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
                 ("employee", "По сотруднику"),
                 ("destination", "По направлению")],
    )


class TravelRequestForm(forms.Form):
    """Форма создания и редактирования заявки."""

    employee_id = forms.TypedChoiceField(
        label="Сотрудник",
        coerce=int,
        choices=[],
    )

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

    def __init__(self, *args, employees, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["employee_id"].choices = [
            ("", "Выберите сотрудника"),
        ] + [
            (
                employee.id,
                f"{employee.name} — {employee.position}",
            )
            for employee in employees
        ]

        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"
