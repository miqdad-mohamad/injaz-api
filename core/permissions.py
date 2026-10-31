from rest_framework import permissions


class IsCompanyAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'AD'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        if hasattr(obj, 'workspace'):
            obj_workspace = obj.workspace
        if hasattr(obj, 'project'):
            obj_workspace = obj.project.workspace
        if hasattr(obj, 'task'):
            obj_workspace = obj.task.project.workspace
        else:
            obj_workspace = None

        if obj_workspace == request.user.workspace:
            return True

        return False


class IsTaskAssigneeOrCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return bool(
                request.user and
                request.user.is_authenticated and
                (request.user.is_superuser or request.user.role in [
                 'AD', 'MO'])
            )
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser or request.user.role in ['AD', 'MO']:
            return True

        if request.method == 'DELETE':
            return obj.created_by == request.user

        return obj.assignee == request.user or obj.created_by == request.user


class IsCommentAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser or request.user.role == 'AD':
            return True

        return obj.author == request.user
