"""Одноразовый перенос ПР7; повтор безопасен без перезаписи изменений."""
import sqlite3
from contextlib import closing
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from employees.models import Employee
from trip_requests.models import Approval, TravelRequest, Trip


class Command(BaseCommand):
    help = "Перенести SQLite ПР7 в ORM, сохранив ID и связи."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", type=Path,
            default=settings.BASE_DIR / "data" / "business_trips.sqlite",
        )

    def handle(self, *args, **options):
        source = options["source"].resolve()
        if not source.is_file():
            raise CommandError(f"Нет исходной базы: {source}")
        target = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if source == target:
            raise CommandError("Источник и целевая база должны различаться.")
        try:
            connection = sqlite3.connect(
                source.as_uri() + "?mode=ro", uri=True,
            )
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("BEGIN")
                if connection.execute("PRAGMA foreign_key_check").fetchall():
                    raise CommandError("Нарушены внешние ключи источника.")
                tables = {
                    "employees": Employee,
                    "trips": Trip,
                    "travel_requests": TravelRequest,
                    "approvals": Approval,
                }
                rows = {
                    name: [dict(row) for row in connection.execute(
                        f'SELECT * FROM "{name}" ORDER BY id',
                    )] for name in tables
                }
                backup = source.with_name(source.name + ".pr9-backup")
                if not backup.exists():
                    with closing(sqlite3.connect(backup)) as destination:
                        connection.backup(destination)
            finally:
                connection.close()
            counts = {}
            with transaction.atomic():
                for name, model in tables.items():
                    created_count = 0
                    for row in rows[name]:
                        pk = row.pop("id")
                        for field in model._meta.fields:
                            key = field.attname
                            if key not in row:
                                continue
                            if field.get_internal_type() == "DecimalField":
                                row[key] = Decimal(str(row[key])).quantize(
                                    Decimal("0.01"),
                                )
                            elif field.get_internal_type() == "DateField":
                                row[key] = date.fromisoformat(row[key])
                        existing = model.objects.filter(pk=pk).first()
                        if existing is not None:
                            if any(getattr(existing, key) != value
                                   for key, value in row.items()):
                                raise CommandError(
                                    f"Конфликт {name} id={pk}: "
                                    "целевая запись отличается. "
                                    "Перенос отменён.",
                                )
                        else:
                            item = model(pk=pk, **row)
                            item.full_clean()
                            item.save(force_insert=True)
                            created_count += 1
                    counts[name] = (len(rows[name]), created_count)
        except (sqlite3.Error, ValidationError, ValueError) as error:
            raise CommandError(str(error)) from error
        for name, (total, created) in counts.items():
            self.stdout.write(f"{name}: проверено {total}, создано {created}")
        self.stdout.write(self.style.SUCCESS("Перенос и сверка завершены."))
