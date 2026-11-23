from django.contrib import admin

from trip_requests.admin import TravelRequestInline

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "position", "slug")
    search_fields = ("name", "position")
    list_filter = ("position",)
    ordering = ("name", "id")
    list_per_page = 10
    inlines = (TravelRequestInline,)
