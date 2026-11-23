from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from .models import Employee


class EmployeePageTests(TestCase):
    @staticmethod
    def photo(name="photo.png"):
        output = BytesIO()
        Image.new("RGB", (4, 4), "white").save(output, format="PNG")
        return SimpleUploadedFile(name, output.getvalue(),
                                  content_type="image/png")

    def test_photo_create_retain_replace_and_clear(self):
        with TemporaryDirectory() as directory, self.settings(
            MEDIA_ROOT=directory,
        ):
            response = self.client.post("/employees/new/", {
                "name": "Фото", "position": "Инженер", "photo": self.photo(),
            })
            self.assertEqual(response.status_code, 302)
            employee = Employee.objects.get(name="Фото")
            self.assertTrue(employee.photo.storage.exists(employee.photo.name))
            self.assertContains(self.client.get(employee.get_absolute_url()),
                                employee.photo.url)
            old_name = employee.photo.name
            url = f"/employees/{employee.pk}/edit/"
            self.client.post(url, {"name": "Фото", "position": "Аналитик"})
            employee.refresh_from_db()
            self.assertEqual(employee.photo.name, old_name)
            self.client.post(url, {
                "name": "Фото", "position": "Аналитик",
                "photo": self.photo("second.png"),
            })
            employee.refresh_from_db()
            self.assertNotEqual(employee.photo.name, old_name)
            self.assertTrue(employee.photo.storage.exists(employee.photo.name))
            self.client.post(url, {
                "name": "Фото", "position": "Аналитик", "photo-clear": "on",
            })
            employee.refresh_from_db()
            self.assertFalse(employee.photo)

    def test_invalid_image_does_not_create_employee(self):
        response = self.client.post("/employees/new/", {
            "name": "Фото", "position": "Инженер",
            "photo": SimpleUploadedFile("fake.png", b"invalid-image",
                                        content_type="image/png"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("photo", response.context["form"].errors)
        self.assertFalse(Employee.objects.exists())

    def test_admin_photo_upload(self):
        user = get_user_model().objects.create_superuser(
            username="photo-admin", password="test-photo-password",
        )
        self.client.force_login(user)
        employee = Employee.objects.create(name="Фото", position="Инженер")
        url = f"/admin/employees/employee/{employee.pk}/change/"
        with TemporaryDirectory() as directory, self.settings(
            MEDIA_ROOT=directory,
        ):
            for name in ("admin-first.png", "admin-second.png"):
                response = self.client.post(url, {
                    "name": employee.name, "position": employee.position,
                    "slug": employee.slug, "photo": self.photo(name),
                    "travel_requests-TOTAL_FORMS": "0",
                    "travel_requests-INITIAL_FORMS": "0",
                    "travel_requests-MIN_NUM_FORMS": "0",
                    "travel_requests-MAX_NUM_FORMS": "0", "_save": "Save",
                })
                self.assertEqual(response.status_code, 302)
                employee.refresh_from_db()
                self.assertTrue(employee.photo.name.endswith(name))
                self.assertTrue(employee.photo.storage.exists(
                    employee.photo.name,
                ))
                response = self.client.get(employee.get_absolute_url())
                self.assertContains(response, employee.photo.url)

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
