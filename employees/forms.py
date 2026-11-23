from django import forms

from .models import Employee


class EmployeeForm(forms.ModelForm):
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

    class Meta:
        model = Employee
        fields = ("name", "position", "photo")
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_texts = {"photo": "Необязательная фотография сотрудника."}
