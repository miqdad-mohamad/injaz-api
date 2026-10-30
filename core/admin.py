from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Workspace, CustomUser, Project, Task


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('workspace', 'role', 'is_verified')}),
    )
    list_display = ['username', 'email', 'role', 'workspace', 'is_staff']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Workspace)
admin.site.register(Project)
admin.site.register(Task)
