from django import forms


class EmployeeForm(forms.Form):
    """Форма создания и редактирования сотрудника."""

    name = forms.CharField(
        label="ФИО",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Иванов Иван Иванович",
            }
        ),
    )

    position = forms.CharField(
        label="Должность",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Например, аналитик",
            }
        ),
    )