from rest_framework import viewsets
from core.models import Workspace, Project, Task, CustomUser, Comment
from core.serializers import WorkspaceSerializer, ProjectSerializer, TaskSerializer, CustomUserSerializer, CommentSerializer
from .permissions import IsCompanyAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdminOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Workspace.objects.all()
        else :
            return Workspace.objects.filter(id=self.request.user.workspace.id)
    def perform_create(self, serializer):
        if self.request.user.workspace is not None :
            raise ValidationError("You are already part of workspace, you cannot create a new one")
        workspace = serializer.save()
        user = self.request.user
        user.workspace = workspace
        user.role = 'AD'
        user.save()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdminOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_superuser :
            return Project.objects.all()
        else :
            return Project.objects.filter(workspace=self.request.user.workspace)
        
    

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdminOrReadOnly]

    def get_queryset(self):
            if self.request.user.is_superuser :
                return Task.objects.all()
            else :
                return Task.objects.filter(project__workspace=self.request.user.workspace)


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserSerializer
    permission_classes = []

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser :
            return CustomUser.objects.all()
        elif user.workspace is not None:
            return CustomUser.objects.filter(workspace=user.workspace)
        else :
            return CustomUser.objects.filter(id=user.id)

    def perform_create(self, serializer):
        user = self.request.user

        if user.is_superuser:
            serializer.save()

        elif user.workspace is not None:
            serializer.save(workspace=user.workspace, is_superuser=False)



class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCompanyAdminOrReadOnly]

    def get_queryset(self):
                if self.request.user.is_superuser :
                    return Comment.objects.all()
                else :
                    return Comment.objects.filter(task__project__workspace=self.request.user.workspace)

