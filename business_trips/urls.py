from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("employees/", include("employees.urls")),
    path("requests/", include("trip_requests.urls")),
    path("sql/", include("sql_reports.urls")),
]

handler404 = "homepage.views.page_not_found"

if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
    )

admin.site.site_header = "Командировки — администрирование"
admin.site.site_title = "Командировки"
admin.site.index_title = "Управление данными"
