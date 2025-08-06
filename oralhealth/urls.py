"""
URL configuration for OralHealth project.
Part of the Xera DB ecosystem.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('guidelines.urls')),
    path('cochrane/', include('cochrane.urls')),
    path('search/', include('search.urls')),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "OralHealth Administration"
admin.site.site_title = "OralHealth Admin"
admin.site.index_title = "Welcome to OralHealth Administration"