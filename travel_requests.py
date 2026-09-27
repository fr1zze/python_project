from approval import Approval
from employees import Employee
from trips import Trip


class TravelRequest:
    """Заявка на командировку."""

    def __init__(
        self,
        request_id: int,
        employee: Employee,
        trip: Trip,
        budget_limit: float,
        approval: Approval | None = None,
    ) -> None:
        if budget_limit < 0:
            raise ValueError(
                "Лимит бюджета не может быть отрицательным"
            )

        self.id = request_id
        self.employee = employee
        self.trip = trip
        self.budget_limit = budget_limit

        if approval is None:
            self.approval = Approval()
        else:
            self.approval = approval

    def approve(
        self,
        requests: list["TravelRequest"],
        approved: bool,
    ) -> None:
        """Проверить правила и записать решение."""
        if self.approval.status != "на рассмотрении":
            raise ValueError(
                "Эта заявка уже рассмотрена"
            )

        if approved:
            if (
                self.trip.calculate_total_cost()
                > self.budget_limit
            ):
                raise ValueError(
                    "Стоимость превышает лимит бюджета"
                )

            for other in requests:
                if other is self:
                    continue

                if other.employee.id != self.employee.id:
                    continue

                if other.approval.status != "одобрена":
                    continue

                if self.trip.overlaps(other.trip):
                    raise ValueError(
                        "У сотрудника есть поездка "
                        "на эти даты"
                    )

        self.approval.decide(approved)

    def __str__(self) -> str:
        return (
            f"№{self.id}: {self.employee.name}, "
            f"{self.trip}, "
            f"{self.trip.calculate_total_cost():.2f} руб., "
            f"{self.approval}"
        )


def create_request(
    requests: list[TravelRequest],
    employee: Employee,
    trip: Trip,
    budget_limit: float,
) -> TravelRequest:
    """Создать заявку и добавить её в список."""
    request_id = max(
        (item.id for item in requests),
        default=0,
    ) + 1

    request = TravelRequest(
        request_id,
        employee,
        trip,
        budget_limit,
    )

    requests.append(request)
    return request


def find_request(
    requests: list[TravelRequest],
    request_id: int,
) -> TravelRequest:
    """Найти заявку по номеру."""
    for request in requests:
        if request.id == request_id:
            return request

    raise ValueError(
        "Заявка с таким номером не найдена"
    )


def find_requests_by_employee(
    requests: list[TravelRequest],
    employee_id: int,
) -> list[TravelRequest]:
    """Найти заявки сотрудника."""
    return [
        item
        for item in requests
        if item.employee.id == employee_id
    ]


def sort_requests_by_date(
    requests: list[TravelRequest],
) -> list[TravelRequest]:
    """Отсортировать заявки по дате поездки."""
    return sorted(
        requests,
        key=lambda item: item.trip.start_date,
    )


def get_request_statistics(
    requests: list[TravelRequest],
) -> dict:
    """Посчитать заявки и стоимость одобренных поездок."""
    approved = [
        item
        for item in requests
        if item.approval.status == "одобрена"
    ]

    return {
        "total": len(requests),
        "approved": len(approved),
        "approved_cost": round(
            sum(
                item.trip.calculate_total_cost()
                for item in approved
            ),
            2,
        ),
    }