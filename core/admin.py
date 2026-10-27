from django.contrib import admin
from .models import Workspace, CustomUser, Project, Task

admin.site.register(Workspace)
admin.site.register(CustomUser)
admin.site.register(Project)
admin.site.register(Task)
