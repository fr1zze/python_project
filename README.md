# Система учёта заявок на командировки

Учебный сквозной проект ПР1–ПР9: сотрудники, поездки, заявки и согласования.
Веб-приложение использует Django 5.2, Django Templates, Forms и SQLite через ORM.
Консольная реализация ПР1–ПР7 сохранена отдельно.

## Установка и запуск

Команды PowerShell выполняются из каталога с `manage.py`.
Python 3.10 или новее.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py import_pr7
python manage.py runserver
```

Если окружение уже существует, достаточно активировать его и выполнить
миграции. Приложение открывается по адресу http://127.0.0.1:8000/.
Без активации используйте `.\venv\Scripts\python.exe` вместо `python`.

## Модели и связи ПР9

| Модель | Файл | Поля и назначение |
|---|---|---|
| Employee | employees/models.py | id, name, position — сотрудник |
| Trip | trip_requests/models.py | id, destination, purpose, start_date, end_date, travel_cost, hotel_cost, daily_allowance — поездка |
| TravelRequest | trip_requests/models.py | id, employee, trip, budget_limit — заявка |
| Approval | trip_requests/models.py | id, request, status — согласование |

Первичные ключи — автоматические `BigAutoField`; при импорте сохраняются ID ПР7.
`TravelRequest.employee` — `ForeignKey(PROTECT)`, обратная связь
`employee.travel_requests`. У сотрудника может быть несколько заявок;
удаление сотрудника со связанными заявками запрещено.
`TravelRequest.trip` — `OneToOneField(PROTECT)`, обратная связь
`trip.travel_request`: поездка принадлежит одной заявке.
`Approval.request` — `OneToOneField(CASCADE)`, обратная связь `request.approval`.
Удаление заявки каскадно удаляет согласование. Удаление заявок в интерфейсе
не добавлялось: сохранены пользовательские сценарии предыдущих работ.

Даты описаны `DateField`, деньги — `DecimalField(12, 2)`, статусы — `TextChoices`.
Валидаторы и ограничения БД запрещают отрицательные расходы и бюджет,
окончание раньше начала, неизвестный статус. Обязательные поля проверяются
формами и `full_clean()`. Новая заявка получает статус «на рассмотрении».
При изменении одобренной заявки проверяются бюджет и пересечения с другими
одобренными поездками этого сотрудника; ошибки откатывают всю транзакцию.
Продолжительность включает обе даты; стоимость = проезд + проживание за всю
поездку + суточные × число дней. Отменённые и отклонённые поездки не блокируют
сотрудника и не входят в расходы по одобренным заявкам.

## Базы данных и перенос ПР7

Выбрана стратегия №2 из ПР9: создать таблицы Django в `db.sqlite3` и перенести
в них записи из `data/business_trips.sqlite`, не меняя исходную базу.
Все веб-страницы, включая сохранённые адреса `/sql/`, читают и изменяют
единую `db.sqlite3` через ORM. Изменения из форм сразу видны в отчётах.

Миграции: `employees/migrations/0001_initial.py` и
`trip_requests/migrations/0001_initial.py`.

```powershell
python manage.py showmigrations
python manage.py sqlmigrate trip_requests 0001
python manage.py migrate
python manage.py import_pr7
# Необязательно: указать другую исходную базу
python manage.py import_pr7 --source data/business_trips.sqlite
```

Команда `import_pr7` находится в
`trip_requests/management/commands/import_pr7.py`.
Источник открывается только для чтения, проверяются внешние ключи,
создаётся резервная копия `data/business_trips.sqlite.pr9-backup`.
Порядок переноса: сотрудники → поездки → заявки → согласования.
Даты и денежные значения преобразуются в `date` и `Decimal`.
Перенос атомарный; сохраняются все ID, поля и ссылки между записями.
Повторный запуск сверяет существующие записи и не создаёт дубликаты.
Если запись с тем же ID отличается, команда прекращает работу с ошибкой
и откатывает весь перенос, сохраняя изменения пользователя.
Записи целевой базы, отсутствующие в источнике, не удаляются.

При выполнении ПР9 перенесены 4 сотрудника, 3 поездки, 3 заявки и 3 согласования.
Одобренных заявок — 2, их стоимость — 90 000 руб.
Перед применением миграций также сохранена локальная копия старой базы Django:
`data/django-before-pr9.sqlite-backup`. Резервные копии исключены из Git.

Для новой установки достаточно отслеживаемой базы ПР7 и команды переноса.
Локальная рабочая `db.sqlite3` не включается в Git.

### Архив ПР1–ПР7

`main.py`, `storage.py` и классы в `models/` сохраняют независимую консольную
версию на `data/employees.json` и `data/requests.json`.
Её можно запустить командой `python main.py`.
Изменения консольной JSON-версии не синхронизируются с веб-приложением.
`sql/schema.sql`, `sql/queries.sql`, `db/database.py`, `db/import_json.py` и
`db/check_database.py` оставлены как реализация ПР7; веб-представления их
больше не вызывают. Прямой sqlite3 в новой команде переноса нужен только
для чтения старой схемы и создания её резервной копии.
`python -m db.import_json` пересоздаёт содержимое архивной базы ПР7 из JSON;
для обычной работы веб-приложения эта команда не нужна.

## Страницы

| URL | Возможности |
|---|---|
| / | Статистика сотрудников, заявок и одобренных расходов |
| /employees/ | Список сотрудников |
| /employees/new/ | Создание сотрудника |
| /employees/\<id\>/ | Карточка и заявки сотрудника |
| /employees/\<id\>/edit/ | Изменение и защищённое удаление |
| /requests/ | Фильтры, поиск, сортировка и пагинация заявок |
| /requests/new/ | Создание заявки и поездки |
| /requests/\<id\>/ | Карточка заявки с расходами и согласованием |
| /requests/\<id\>/edit/ | Изменение с сохранением статуса |
| /sql/employees/ | Отчёт по сотрудникам через ORM |
| /sql/trips/ | Отчёт по поездкам через ORM |
| /sql/requests/ | Связанные данные и фильтр сотрудника |
| /sql/search/ | Поиск направления и свободных сотрудников на дату |
| /sql/statistics/ | Сводные показатели, группировка, фильтр по числу заявок |

Список `/requests/` принимает `employee_id`, `selected_date`, `status`,
`destination`, `q`, `sort`, `page`.
Дата попадает в включительный интервал поездки. `q` ищет по ФИО,
направлению и цели; `destination` — по части направления.
Допустимые сортировки: `date`, `-date`, `employee`, `destination`;
поля заданы белым списком в `trip_requests/views.py`.
Пагинация — по 10 записей, ссылки сохраняют остальные GET-параметры,
новый запрос формы сбрасывает страницу. `Paginator.get_page()` обрабатывает
нечисловые и выходящие за пределы номера. При неверных фильтрах форма
показывает ошибки, список пуст. Несуществующие карточки возвращают 404.

## Каталог ORM-выражений для защиты ПР9

Все перечисленные запросы используются страницами или командой переноса.
Основная логика находится в `trip_requests/queries.py` и `views.py` приложений.

| № | Выражение / сценарий | Категория |
|---|---|---|
| 1 | Employee.objects.all() — список | Базовое чтение |
| 2 | get_object_or_404(Employee, pk=...) — карточка | Один объект |
| 3 | Employee.objects.get(pk=...) — сотрудник при сохранении | Один объект |
| 4 | TravelRequest.objects.select_related(employee, trip, approval) | Связи, оптимизация |
| 5 | employee.travel_requests.select_related(trip, approval) | Обратная связь |
| 6 | queryset.filter(employee_id=...) | Фильтр одного поля |
| 7 | queryset.filter(trip__start_date__lte=..., trip__end_date__gte=...) | Несколько условий, связанные поля |
| 8 | queryset.filter(approval__status=...) | Связанная модель |
| 9 | Конфликты одобренных поездок: filter(...).exclude(pk=self.pk).exists() | Исключение |
| 10 | queryset.filter(trip__destination__icontains=...) | Строковый поиск |
| 11 | queryset.filter(Q(employee__name__icontains=...) \| Q(trip__destination__icontains=...) \| Q(trip__purpose__icontains=...)) | Поиск по нескольким полям |
| 12 | queryset.order_by(trip__start_date, id) | Сортировка дат |
| 13 | queryset.order_by(employee__name, trip__start_date, id) | Сортировка связанных полей |
| 14 | Employee.objects.exclude(pk__in=busy) | Свободные сотрудники, подзапрос |
| 15 | Employee.objects.values(id, name, position) | Сокращённый набор полей |
| 16 | approved_totals(): filter(...).aggregate(Count, Sum) | Сводные расходы с выражением длительности |
| 17 | Employee.objects.annotate(request_count=Count(travel_requests)) | Группировка, включая сотрудников без заявок |
| 18 | employee_counts().filter(request_count__gt=minimum) | Аналог HAVING |
| 19 | Approval.objects.values(status).annotate(request_count=Count(pk)) | Группировка по статусам |
| 20 | Paginator(queryset, 10).get_page(page) | Постраничный вывод |

Создание: `Employee.objects.create()`, `Trip.save()`, `TravelRequest.save()`,
`Approval.objects.get_or_create()`; изменение: присваивание полей и `save()`;
удаление: `employee.delete()` с обработкой `ProtectedError`.

## Проверки

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py test --verbosity 2
python -m pytest -v -o cache_dir=tmp/pytest-cache
python -m flake8 . --extend-exclude=venv
```

Новые Django-тесты в `trip_requests/tests.py` проверяют модели, ограничения БД,
связи без N+1, стоимость, свободных сотрудников, HTTP-страницы, 404,
CRUD, бизнес-правила, откат изменений, фильтры, сортировку, пагинацию,
перенос, повторный импорт и откат конфликтующего импорта.
Они работают на отдельной временной тестовой базе, не изменяя рабочие данные.
Девять прежних pytest-тестов проверяют консольную объектную модель.
Для pytest указан доступный каталог кеша: исходный `.pytest_cache`
в текущем окружении защищён от записи.
Flake8 исключает локальные вспомогательные `.docx_qa/`, `tmp/`, окружение и кеши;
для автоматически созданных миграций допускаются длинные строки.

## Выгрузка и загрузка данных ORM

```powershell
python manage.py dumpdata employees trip_requests --indent 2 --output data/orm_export.json
# Загружать в чистую совместимую базу после migrate:
python manage.py loaddata data/orm_export.json
```

Перед загрузкой fixture в непустую базу следует проверить совпадения ID:
`loaddata` может обновить записи с совпадающими первичными ключами.

Краткий отчёт и сведения о проверках находятся в `docs/PR9_report.md`.
Задания личного кабинета Яндекс Практикума выполняются и подтверждаются
студентом отдельно; проект не подтверждает их прохождение.
