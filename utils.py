from datetime import date, datetime


def input_int(prompt: str) -> int:
    """Запрашивать целое число до правильного ввода."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Введите целое число.")


def input_float(prompt: str) -> float:
    """Запрашивать неотрицательную сумму."""
    while True:
        try:
            value = float(
                input(prompt).replace(",", ".")
            )

            if value < 0 or not value < float("inf"):
                raise ValueError

            return value

        except ValueError:
            print("Введите неотрицательное число.")


def input_date(prompt: str) -> date:
    """Запрашивать дату в формате ДД.ММ.ГГГГ."""
    while True:
        try:
            value = input(prompt)
            return datetime.strptime(
                value,
                "%d.%m.%Y",
            ).date()

        except ValueError:
            print("Введите дату в формате ДД.ММ.ГГГГ.")