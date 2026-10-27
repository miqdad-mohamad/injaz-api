import os
from django.contrib import admin
from django.urls import path, include

admin_url = os.environ.get('ADMIN_URL', 'admin/')
urlpatterns = [
    path(admin_url, admin.site.urls),
    path ('api/', include('core.urls')),
]
