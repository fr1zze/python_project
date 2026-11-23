from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Employee(models.Model):
    """Сотрудник; связанные заявки запрещают его удаление."""

    name = models.CharField("ФИО", max_length=150)
    position = models.CharField("Должность", max_length=150)
    photo = models.ImageField("Фотография", upload_to="employees/", blank=True)
    slug = models.SlugField("Адрес страницы", max_length=170, unique=True,
                            blank=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
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

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "employee"
            self.slug = base
            number = 2
            while type(self).objects.filter(slug=self.slug).exclude(
                pk=self.pk,
            ).exists():
                self.slug = f"{base}-{number}"
                number += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("employees:detail_by_slug", kwargs={"slug": self.slug})
