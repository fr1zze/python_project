from django import forms


class EmployeeFilterForm(forms.Form):
    employee_id = forms.IntegerField(
        label="ID сотрудника",
        required=False,
        min_value=1,
        widget=forms.NumberInput(
            attrs={"class": "form-control"}
        ),
    )


class SearchForm(forms.Form):
    destination = forms.CharField(
        label="Часть названия направления",
        required=False,
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    selected_date = forms.DateField(
        label="Дата проверки занятости сотрудников",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "class": "form-control",
            },
        ),
    )


class StatisticsForm(forms.Form):
    minimum = forms.IntegerField(
        label="Показать сотрудников с числом заявок больше",
        min_value=0,
        widget=forms.NumberInput(
            attrs={"class": "form-control"}
        ),
    )