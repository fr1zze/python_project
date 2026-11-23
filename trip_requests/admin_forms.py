"""Проверка правил одобренной заявки при изменениях через админку."""
from django import forms
from django.core.exceptions import ValidationError

from .models import Approval, TravelRequest, Trip


class TravelRequestAdminForm(forms.ModelForm):
    class Meta:
        model = TravelRequest
        fields = "__all__"

    def _post_clean(self):
        super()._post_clean()
        if not self.errors and self.instance.pk:
            if Approval.objects.filter(
                request=self.instance, status=Approval.Status.APPROVED,
            ).exists():
                try:
                    self.instance.validate_approved()
                except ValidationError as error:
                    self.add_error(None, error)


class TripAdminForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = "__all__"

    def _post_clean(self):
        super()._post_clean()
        if not self.errors and self.instance.pk:
            item = TravelRequest.objects.approved().filter(
                trip=self.instance,
            ).first()
            if item:
                item.trip = self.instance
                try:
                    item.validate_approved()
                except ValidationError as error:
                    self.add_error(None, error)


class ApprovalAdminForm(forms.ModelForm):
    class Meta:
        model = Approval
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if (data.get("status") == Approval.Status.APPROVED
                and data.get("request")):
            data["request"].validate_approved()
        return data
