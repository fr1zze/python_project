from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from .models import Employee


class EmployeePageTests(TestCase):
    def test_slug_uniqueness_links_and_context(self):
        first = Employee.objects.create(name="Иван", position="Инженер")
        second = Employee.objects.create(name="Иван", position="Инженер")
        self.assertNotEqual(first.slug, second.slug)
        url = first.get_absolute_url()
        response = self.client.get(url)
        self.assertContains(response, "Иван")
        self.assertContains(response, "Сотрудников: 2")
        self.assertContains(self.client.get("/employees/"), url)
        self.assertEqual(self.client.get(
            f"/employees/{first.pk}/",
        ).status_code, 200)
        first.name = "Новое имя"
        first.save()
        self.assertEqual(first.get_absolute_url(), url)
        self.assertEqual(self.client.get(
            "/employees/profile/unknown/",
        ).status_code, 404)


class EmployeeSlugMigrationTests(TransactionTestCase):
    def test_existing_employees_receive_unique_slugs(self):
        before = [("employees", "0001_initial")]
        executor = MigrationExecutor(connection)
        after = executor.loader.graph.leaf_nodes()
        executor.migrate(before)
        try:
            state = executor.loader.project_state(before)
            OldEmployee = state.apps.get_model("employees", "Employee")
            first = OldEmployee.objects.create(name="Иван", position="Инженер")
            second = OldEmployee.objects.create(
                name="Иван", position="Аналитик",
            )
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            self.assertEqual(Employee.objects.get(pk=first.pk).slug,
                             f"employee-{first.pk}")
            self.assertEqual(Employee.objects.get(pk=second.pk).slug,
                             f"employee-{second.pk}")
            self.assertEqual(Employee.objects.get(pk=second.pk).position,
                             "Аналитик")
        finally:
            MigrationExecutor(connection).migrate(after)
