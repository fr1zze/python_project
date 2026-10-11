from html import escape

from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import get_token

from models.travel_requests import get_request_statistics
from storage import load_employees, load_requests


def page(title: str, content: str) -> str:
    """Сформировать общий HTML-каркас."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/"
        "dist/css/bootstrap.min.css"
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="{bootstrap}">

    <style>
        body {{
            background: #f5f6fa;
            color: #253046;
        }}

        .site-header {{
            background: white;
            border-bottom: 1px solid #e5e8ef;
        }}

        .brand {{
            font-weight: 700;
            font-size: 20px;
            color: #253046;
            text-decoration: none;
        }}

        .nav-link {{
            color: #566176;
            font-weight: 500;
            border-radius: 8px;
        }}

        .nav-link:hover {{
            background: #eef2ff;
            color: #3858c9;
        }}

        main {{
            padding-top: 32px;
            padding-bottom: 40px;
        }}

        h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 20px;
        }}

        .card {{
            border: 1px solid #e5e8ef;
            border-radius: 14px;
            box-shadow: 0 4px 16px rgba(30, 40, 70, 0.04);
        }}

        .stat-label {{
            color: #758096;
            font-size: 14px;
        }}

        .stat-value {{
            font-size: 28px;
            font-weight: 700;
            margin-top: 8px;
        }}

        .btn {{
            border-radius: 8px;
        }}

        .list-group-item {{
            padding: 18px;
            border-color: #e5e8ef;
        }}

        .form-card {{
            max-width: 760px;
            margin: 0 auto;
        }}

        .form-card label {{
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
        }}

        .form-card form p {{
            margin-bottom: 18px;
        }}

        .errorlist {{
            color: #b42318;
            background: #fff0ef;
            border-radius: 8px;
            padding: 12px 12px 12px 30px;
        }}

        .helptext {{
            display: block;
            color: #758096;
            font-size: 13px;
            margin-top: 5px;
        }}
    </style>
</head>

<body>
    <header class="site-header">
        <div class="container py-3">
            <div class="d-flex flex-wrap gap-3
                        justify-content-between align-items-center">
                <a class="brand" href="/">Командировки</a>

                <nav class="nav gap-1">
                    <a class="nav-link" href="/">Главная</a>
                    <a class="nav-link" href="/employees/">
                        Сотрудники
                    </a>
                    <a class="nav-link" href="/requests/">
                        Заявки
                    </a>
                </nav>
            </div>
        </div>
    </header>

    <main class="container">
        {content}
    </main>
</body>
</html>"""


def index(request):
    """Показать статистику проекта."""
    data_dir = settings.BASE_DIR / "data"

    employees = load_employees(
        data_dir / "employees.json"
    )
    requests = load_requests(
        data_dir / "requests.json",
        employees,
    )
    statistics = get_request_statistics(requests)

    content = f"""
    <h1>Статистика</h1>
    <p class="text-muted mb-4">
        Сотрудники, заявки и расходы на одобренные поездки.
    </p>

    <div class="row g-3">
        <div class="col-12 col-sm-6 col-xl-3">
            <div class="card h-100">
                <div class="card-body">
                    <div class="stat-label">Сотрудников</div>
                    <div class="stat-value">{len(employees)}</div>
                </div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="card h-100">
                <div class="card-body">
                    <div class="stat-label">Всего заявок</div>
                    <div class="stat-value">
                        {statistics["total"]}
                    </div>
                </div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="card h-100">
                <div class="card-body">
                    <div class="stat-label">Одобрено</div>
                    <div class="stat-value text-success">
                        {statistics["approved"]}
                    </div>
                </div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="card h-100">
                <div class="card-body">
                    <div class="stat-label">
                        Расходы по одобренным заявкам
                    </div>
                    <div class="stat-value">
                        {statistics["approved_cost"]:.2f}
                    </div>
                    <div class="text-muted">рублей</div>
                </div>
            </div>
        </div>
    </div>
    """

    return HttpResponse(
        page("Командировки — обзор", content)
    )


def form_page(
    request,
    title,
    form,
    back_url,
    extra_buttons="",
):
    """Показать форму с кнопками и CSRF-токеном."""
    token = escape(get_token(request))

    content = f"""
    <div class="card form-card">
        <div class="card-body p-4">
            <h1>{escape(title)}</h1>

            <form method="post">
                <input type="hidden"
                       name="csrfmiddlewaretoken"
                       value="{token}">

                {form.as_p()}

                <div class="d-flex flex-wrap gap-2 mt-4">
                    <button type="submit"
                            name="action"
                            value="save"
                            class="btn btn-primary">
                        Сохранить
                    </button>

                    <a href="{escape(back_url)}"
                       class="btn btn-outline-secondary">
                        Отмена
                    </a>

                    {extra_buttons}
                </div>
            </form>
        </div>
    </div>
    """

    return HttpResponse(
        page(title, content)
    )


def page_not_found(request, exception):
    """Показать страницу ошибки 404."""
    content = """
    <div class="card">
        <div class="card-body p-4">
            <h1>404 — страница не найдена</h1>
            <p class="text-muted">
                Проверьте адрес или вернитесь на главную.
            </p>
            <a href="/" class="btn btn-primary">
                На главную
            </a>
        </div>
    </div>
    """

    return HttpResponse(
        page("Страница не найдена", content),
        status=404,
    )