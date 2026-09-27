class Approval:
    """Результат согласования заявки."""

    def __init__(
        self,
        status: str = "на рассмотрении",
    ) -> None:
        allowed = {
            "на рассмотрении",
            "одобрена",
            "отклонена",
            "отменена",
        }

        if status not in allowed:
            raise ValueError(
                "Неизвестный статус заявки"
            )

        self.status = status

    def decide(self, approved: bool) -> None:
        """Одобрить или отклонить заявку."""
        if self.status != "на рассмотрении":
            raise ValueError(
                "Эта заявка уже рассмотрена"
            )

        if approved:
            self.status = "одобрена"
        else:
            self.status = "отклонена"

    def __str__(self) -> str:
        return self.status