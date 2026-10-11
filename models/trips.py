from datetime import date


class Trip:
    """Поездка с датами и расходами."""

    def __init__(
        self,
        destination: str,
        purpose: str,
        start_date: date,
        end_date: date,
        travel_cost: float,
        hotel_cost: float,
        daily_allowance: float,
    ) -> None:
        if not destination.strip() or not purpose.strip():
            raise ValueError(
                "Укажите место и цель командировки"
            )

        if end_date < start_date:
            raise ValueError(
                "Дата окончания раньше даты начала"
            )

        if min(
            travel_cost,
            hotel_cost,
            daily_allowance,
        ) < 0:
            raise ValueError(
                "Расходы не могут быть отрицательными"
            )

        self.destination = destination.strip()
        self.purpose = purpose.strip()
        self.start_date = start_date
        self.end_date = end_date
        self.travel_cost = travel_cost
        self.hotel_cost = hotel_cost
        self.daily_allowance = daily_allowance

    def calculate_days(self) -> int:
        """Посчитать дни поездки, включая обе даты."""
        return (
            self.end_date - self.start_date
        ).days + 1

    def calculate_total_cost(self) -> float:
        """Посчитать общую стоимость командировки."""
        total = (
            self.travel_cost
            + self.hotel_cost
            + self.daily_allowance
            * self.calculate_days()
        )

        return round(total, 2)

    def overlaps(self, other: "Trip") -> bool:
        """Проверить пересечение дат двух поездок."""
        return (
            self.start_date <= other.end_date
            and other.start_date <= self.end_date
        )

    def __str__(self) -> str:
        return (
            f"{self.destination}: "
            f"{self.start_date:%d.%m.%Y} — "
            f"{self.end_date:%d.%m.%Y}"
        )