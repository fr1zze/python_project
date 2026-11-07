from django.db import models


class Employee(models.Model):
    """Сотрудник; связанные заявки запрещают его удаление."""

    name = models.CharField("ФИО", max_length=150)
    position = models.CharField("Должность", max_length=150)

    class Meta:
        ordering = ("name", "id")
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name=""), name="employee_name_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(position=""),
                name="employee_position_not_empty",
            ),
        ]

    def __str__(self):
        return self.name
