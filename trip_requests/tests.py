import sqlite3
from contextlib import closing
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from employees.models import Employee

from .models import Approval, TravelRequest, Trip
from .queries import (
    approved_totals, available_employees, employee_counts, related_requests,
    status_totals,
)


class ORMTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employee = Employee.objects.create(
            name="Иван", position="Аналитик",
        )
        cls.free = Employee.objects.create(
            name="Пётр", position="Разработчик",
        )
        cls.trip = Trip.objects.create(
            destination="Москва", purpose="Встреча",
            start_date=date(2026, 11, 7), end_date=date(2026, 11, 9),
            travel_cost=Decimal("100.10"), hotel_cost=Decimal("200.20"),
            daily_allowance=Decimal("50.05"),
        )
        cls.item = TravelRequest.objects.create(
            employee=cls.employee, trip=cls.trip, budget_limit=1000,
        )
        Approval.objects.create(request=cls.item, status="одобрена")

    def form_data(self, **changes):
        data = {
            "employee_id": self.employee.pk, "destination": "Казань",
            "purpose": "Доклад", "start_date": "2026-11-08",
            "end_date": "2026-11-09", "travel_cost": "100.00",
            "hotel_cost": "200.00", "daily_allowance": "50.00",
            "budget_limit": "1000.00",
        }
        return {**data, **changes}

    def test_cost_and_aggregate(self):
        self.assertEqual(self.trip.calculate_days(), 3)
        self.assertEqual(self.trip.calculate_total_cost(), Decimal("450.45"))
        self.assertEqual(approved_totals(), {
            "approved_count": 1, "approved_cost": Decimal("450.45"),
        })
        Approval.objects.update(status="отменена")
        self.assertEqual(approved_totals()["approved_cost"], 0)

    def test_availability_inclusive_and_cancelled(self):
        for day in (self.trip.start_date, self.trip.end_date):
            self.assertNotIn(self.employee, available_employees(day))
        self.assertIn(self.employee, available_employees(
            self.trip.end_date + timedelta(days=1),
        ))
        Approval.objects.update(status="отменена")
        self.assertIn(self.employee, available_employees(self.trip.start_date))
        self.assertIn(self.free, available_employees(self.trip.start_date))

    def test_relations_query_count_and_zero_groups(self):
        with self.assertNumQueries(1):
            rows = [(r.employee.name, r.trip.destination, r.approval.status)
                    for r in related_requests()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            employee_counts().get(pk=self.free.pk).request_count, 0,
        )
        with self.assertRaises(ProtectedError):
            self.employee.delete()

    def test_database_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Trip.objects.filter(pk=self.trip.pk).update(travel_cost=-1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Approval.objects.update(status="wrong")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Trip.objects.filter(pk=self.trip.pk).update(end_date="2020-01-01")

    def test_pages_and_404(self):
        urls = ["/", "/employees/", f"/employees/{self.employee.pk}/",
                "/employees/new/", f"/employees/{self.employee.pk}/edit/",
                "/requests/", f"/requests/{self.item.pk}/", "/requests/new/",
                f"/requests/{self.item.pk}/edit/", "/sql/employees/",
                "/sql/trips/", "/sql/requests/", "/sql/search/",
                "/sql/statistics/"]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get("/employees/99999/").status_code, 404)
        self.assertEqual(self.client.get("/requests/99999/").status_code, 404)

    def test_employee_crud_and_protected_delete(self):
        response = self.client.post("/employees/new/", {
            "name": "Новый", "position": "Инженер",
        })
        self.assertEqual(response.status_code, 302)
        employee = Employee.objects.get(name="Новый")
        url = f"/employees/{employee.pk}/edit/"
        self.client.post(url, {"name": "Изменён", "position": "Инженер"})
        employee.refresh_from_db()
        self.assertEqual(employee.name, "Изменён")
        response = self.client.post(url, {"action": "delete"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Employee.objects.filter(pk=employee.pk).exists())
        response = self.client.post(
            f"/employees/{self.employee.pk}/edit/", {"action": "delete"},
        )
        self.assertContains(response, "Нельзя удалить сотрудника")

    def test_request_create_edit_and_rollback(self):
        response = self.client.post("/requests/new/", self.form_data())
        self.assertEqual(response.status_code, 302)
        item = TravelRequest.objects.exclude(pk=self.item.pk).get()
        self.assertEqual(item.approval.status, "на рассмотрении")
        url = f"/requests/{item.pk}/edit/"
        self.client.post(url, self.form_data(destination="Сочи"))
        item.trip.refresh_from_db()
        self.assertEqual(item.trip.destination, "Сочи")
        # Попытка передвинуть одобренную поездку на чужой одобренный интервал.
        Approval.objects.filter(request=item).update(status="одобрена")
        original_url = f"/requests/{self.item.pk}/edit/"
        response = self.client.post(original_url, self.form_data())
        self.assertContains(response, "У сотрудника есть поездка на эти даты")
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.destination, "Москва")
        response = self.client.post(original_url,
                                    self.form_data(budget_limit="1.00"))
        self.assertContains(response, "Стоимость превышает лимит бюджета")
        before = Trip.objects.count()
        response = self.client.post("/requests/new/", self.form_data(
            end_date="2020-01-01",
        ))
        self.assertContains(response, "Дата окончания раньше даты начала")
        self.assertEqual(Trip.objects.count(), before)

    def test_filter_search_sort_and_pagination(self):
        for index in range(11):
            trip = Trip.objects.get(pk=self.trip.pk)
            trip.pk = None
            trip.save()
            item = TravelRequest.objects.create(
                employee=self.employee, trip=trip, budget_limit=1000,
            )
            Approval.objects.create(request=item)
        params = {"employee_id": self.employee.pk, "destination": "Москва",
                  "q": "Встреча", "selected_date": "2026-11-09",
                  "sort": "-date"}
        response = self.client.get("/requests/", params)
        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        self.assertEqual(len(response.context["travel_requests"]), 10)
        self.assertContains(response, "sort=-date")
        self.assertEqual(len(self.client.get("/requests/", {
            **params, "page": 2,
        }).context["travel_requests"]), 2)
        for page in ("wrong", "-1", "999999"):
            self.assertEqual(self.client.get("/requests/", {
                **params, "page": page,
            }).status_code, 200)
        for invalid in ({"sort": "trip__secret"}, {"selected_date": "wrong"},
                        {"employee_id": "-1"}, {"status": "wrong"}):
            result = self.client.get("/requests/", invalid)
            self.assertEqual(result.status_code, 200)
            self.assertTrue(result.context["form"].errors)
            self.assertEqual(result.context["page_obj"].paginator.count, 0)
        self.assertEqual(self.client.get("/requests/", {
            "status": "одобрена",
        }).context["page_obj"].paginator.count, 1)

    def test_report_inputs_and_search(self):
        for url in ("/sql/requests/?employee_id=bad",
                    "/sql/search/?selected_date=bad",
                    "/sql/statistics/?minimum=-1"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        response = self.client.get("/sql/search/", {
            "destination": "Моск", "selected_date": "2026-11-07",
        })
        self.assertTrue(response.context["searched"])
        self.assertEqual(len(response.context["trips_table"]["rows"]), 1)
        self.assertEqual(len(response.context["employees_table"]["rows"]), 1)

    def test_sorting_by_date_and_employee(self):
        trip = Trip.objects.get(pk=self.trip.pk)
        trip.pk = None
        trip.start_date = date(2026, 12, 1)
        trip.end_date = date(2026, 12, 2)
        trip.save()
        later = TravelRequest.objects.create(
            employee=self.free, trip=trip, budget_limit=1000,
        )
        Approval.objects.create(request=later)
        for sort, expected in (
            ("date", [self.item.pk, later.pk]),
            ("-date", [later.pk, self.item.pk]),
            ("employee", [later.pk, self.item.pk]),
        ):
            response = self.client.get("/requests/", {"sort": sort})
            self.assertEqual(
                [item.pk for item in response.context["travel_requests"]],
                expected,
            )

    def test_queryset_methods_rows_and_status_totals(self):
        self.assertEqual(TravelRequest.objects.approved().for_date(
            self.trip.end_date,
        ).get(), self.item)
        self.assertFalse(TravelRequest.objects.cancelled().exists())
        self.assertFalse(TravelRequest.objects.pending().exists())
        self.assertFalse(TravelRequest.objects.rejected().exists())
        with self.assertNumQueries(1):
            row = TravelRequest.objects.rows().get(pk=self.item.pk)
        self.assertEqual(row["employee_name"], self.employee.name)
        self.assertEqual(row["destination"], "Москва")
        self.assertEqual(status_totals(), {
            "total": 1, "approved": 1, "pending": 0,
            "rejected": 0, "cancelled": 0,
        })
        Approval.objects.update(status=Approval.Status.CANCELLED)
        self.assertEqual(TravelRequest.objects.cancelled().count(), 1)
        self.assertEqual(status_totals()["cancelled"], 1)
        self.assertEqual(status_totals()["approved"], 0)

    def test_admin_pages_search_filter_and_inline(self):
        user = get_user_model().objects.create_superuser(
            username="test-admin", password="test-admin-password",
        )
        self.client.force_login(user)
        for url in (
            "/admin/", "/admin/employees/employee/",
            f"/admin/employees/employee/{self.employee.pk}/change/",
            "/admin/trip_requests/trip/",
            f"/admin/trip_requests/trip/{self.trip.pk}/change/",
            "/admin/trip_requests/travelrequest/",
            f"/admin/trip_requests/travelrequest/{self.item.pk}/change/",
            "/admin/trip_requests/approval/",
            f"/admin/trip_requests/approval/{self.item.approval.pk}/change/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        url = "/admin/trip_requests/travelrequest/"
        response = self.client.get(url, {
            "q": "Москва", "approval__status__exact": "одобрена",
        })
        self.assertEqual(response.context["cl"].result_count, 1)
        response = self.client.get(url, {"q": "Неизвестный город"})
        self.assertEqual(response.context["cl"].result_count, 0)
        response = self.client.get(
            f"/admin/employees/employee/{self.employee.pk}/change/",
        )
        self.assertContains(response, "Москва")

    def test_admin_business_validation(self):
        from .admin_forms import (
            ApprovalAdminForm, TravelRequestAdminForm, TripAdminForm,
        )
        form = TravelRequestAdminForm(data={
            "employee": self.employee.pk, "trip": self.trip.pk,
            "budget_limit": "1.00",
        }, instance=self.item)
        self.assertFalse(form.is_valid())
        self.assertIn("Стоимость превышает", str(form.errors))
        trip = Trip.objects.get(pk=self.trip.pk)
        form = TripAdminForm(data={
            "destination": trip.destination, "purpose": trip.purpose,
            "start_date": trip.start_date, "end_date": trip.end_date,
            "travel_cost": "2000.00", "hotel_cost": trip.hotel_cost,
            "daily_allowance": trip.daily_allowance,
        }, instance=trip)
        self.assertFalse(form.is_valid())
        self.assertIn("Стоимость превышает", str(form.errors))
        trip = Trip.objects.get(pk=self.trip.pk)
        trip.pk = None
        trip.save()
        other = TravelRequest.objects.create(
            employee=self.employee, trip=trip, budget_limit=1000,
        )
        approval = Approval.objects.create(request=other)
        form = ApprovalAdminForm(data={
            "request": other.pk, "status": Approval.Status.APPROVED,
        }, instance=approval)
        self.assertFalse(form.is_valid())
        self.assertIn("есть поездка", str(form.errors))
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)

    def test_admin_create_request_and_change_status(self):
        user = get_user_model().objects.create_superuser(
            username="admin-crud", password="test-admin-password",
        )
        self.client.force_login(user)
        trip = Trip.objects.get(pk=self.trip.pk)
        trip.pk = None
        trip.save()
        url = "/admin/trip_requests/travelrequest/add/"
        response = self.client.post(url, {
            "employee": self.free.pk, "trip": trip.pk,
            "budget_limit": "1000.00", "_save": "Сохранить",
            "approval-TOTAL_FORMS": "0", "approval-INITIAL_FORMS": "0",
            "approval-MIN_NUM_FORMS": "0", "approval-MAX_NUM_FORMS": "1",
        })
        self.assertEqual(response.status_code, 302)
        item = TravelRequest.objects.get(trip=trip)
        approval = item.approval
        self.assertEqual(approval.status, Approval.Status.PENDING)
        url = f"/admin/trip_requests/approval/{approval.pk}/change/"
        response = self.client.post(url, {
            "status": Approval.Status.APPROVED, "_save": "Сохранить",
        })
        self.assertEqual(response.status_code, 302)
        approval.refresh_from_db()
        self.assertEqual(approval.status, Approval.Status.APPROVED)
        self.assertNotIn(self.free, available_employees(trip.start_date))
        response = self.client.post(url, {
            "status": Approval.Status.CANCELLED, "_save": "Сохранить",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.free, available_employees(trip.start_date))
        response = self.client.get(
            f"/admin/trip_requests/approval/{approval.pk}/delete/",
        )
        self.assertEqual(response.status_code, 403)

    def test_changed_cost_and_related_values(self):
        self.trip.travel_cost = Decimal("110.10")
        self.trip.save()
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.calculate_total_cost(), Decimal("460.45"))
        self.assertEqual(approved_totals()["approved_cost"], Decimal("460.45"))
        self.employee.name = "Новое имя"
        self.employee.save()
        self.assertEqual(TravelRequest.objects.rows().get(
            pk=self.item.pk,
        )["employee_name"], "Новое имя")


class ImportTests(TestCase):
    def test_import_repeat_conflict_and_rollback(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite"
            with closing(sqlite3.connect(source)) as connection:
                connection.executescript((
                    settings.BASE_DIR / "sql/schema.sql"
                ).read_text(encoding="utf-8"))
                connection.executescript("""
                    INSERT INTO employees VALUES (101, 'Name', 'Role');
                    INSERT INTO trips VALUES (
                        404, 'City', 'Meeting', '2026-11-07', '2026-11-09',
                        100.1, 200.2, 50.05
                    );
                    INSERT INTO travel_requests VALUES (404, 101, 404, 1000);
                    INSERT INTO approvals VALUES (404, 404, 'одобрена');
                """)
            output = StringIO()
            call_command("import_pr7", source=source, stdout=output)
            expected = (
                Employee.objects.count(), Trip.objects.count(),
                TravelRequest.objects.count(), Approval.objects.count(),
            )
            call_command("import_pr7", source=source, stdout=output)
            self.assertEqual(expected, (1, 1, 1, 1))
            self.assertEqual(TravelRequest.objects.count(), 1)
            self.assertEqual(approved_totals()["approved_cost"],
                             Decimal("450.45"))
            with closing(sqlite3.connect(source)) as connection:
                connection.execute(
                    "INSERT INTO employees VALUES (1, 'New', 'Role')",
                )
                connection.execute("UPDATE employees SET name='Conflict' "
                                   "WHERE id=101")
                connection.commit()
            with self.assertRaises(CommandError):
                call_command("import_pr7", source=source, stdout=output)
            self.assertFalse(Employee.objects.filter(pk=1).exists())
            self.assertEqual(Employee.objects.count(), 1)
            backup = source.with_name(source.name + ".pr9-backup")
            self.assertTrue(backup.exists())
