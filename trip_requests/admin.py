from django.contrib import admin

from .admin_forms import (
    ApprovalAdminForm, TravelRequestAdminForm, TripAdminForm,
)
from .models import Approval, TravelRequest, Trip


class TravelRequestInline(admin.TabularInline):
    model = TravelRequest
    fields = ("trip", "budget_limit")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("trip")


class ApprovalInline(admin.TabularInline):
    model = Approval
    fields = ("status",)
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    form = TripAdminForm
    list_display = ("id", "destination", "purpose", "start_date", "end_date",
                    "total_cost")
    search_fields = ("destination", "purpose")
    list_filter = ("start_date", "end_date")
    ordering = ("start_date", "id")
    list_per_page = 10
    readonly_fields = ("total_cost",)

    @admin.display(description="Полная стоимость")
    def total_cost(self, obj):
        if obj and obj.pk:
            return obj.calculate_total_cost()
        return "—"


@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    form = TravelRequestAdminForm
    list_display = ("id", "employee", "trip", "budget_limit", "status")
    search_fields = ("employee__name", "trip__destination", "trip__purpose")
    list_filter = ("approval__status", "trip__start_date")
    list_select_related = ("employee", "trip", "approval")
    ordering = ("-trip__start_date", "id")
    list_per_page = 10
    inlines = (ApprovalInline,)

    @admin.display(description="Статус", ordering="approval__status")
    def status(self, obj):
        return obj.approval.get_status_display() if hasattr(
            obj, "approval",
        ) else "Нет согласования"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        Approval.objects.get_or_create(request=obj)


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    form = ApprovalAdminForm
    list_display = ("id", "request", "employee", "destination", "status")
    search_fields = ("request__employee__name", "request__trip__destination")
    list_filter = ("status",)
    list_select_related = ("request__employee", "request__trip")
    ordering = ("request_id",)
    list_per_page = 10

    def get_readonly_fields(self, request, obj=None):
        # Перенос согласования оставил бы исходную заявку без статуса.
        return ("request",) if obj else ()

    def has_delete_permission(self, request, obj=None):
        # Согласование удаляется каскадно вместе с заявкой.
        return False

    @admin.display(description="Сотрудник")
    def employee(self, obj):
        return obj.request.employee

    @admin.display(description="Направление")
    def destination(self, obj):
        return obj.request.trip.destination
