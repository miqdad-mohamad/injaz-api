from rest_framework import serializers

from core.models import Workspace, Project, Task, CustomUser, Comment


class WorkspaceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name',read_only=True)
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['workspace']




class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name',read_only=True)
    assignee_name = serializers.SerializerMethodField()
    watchers_names = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            user = request.user
            if user.is_superuser:
                pass
            else :
                self.fields['project'].queryset = Project.objects.filter(workspace=user.workspace)
                workspace_users = CustomUser.objects.filter(workspace=user.workspace)
                self.fields['assignee'].queryset = workspace_users
                self.fields['watchers'].queryset = workspace_users

    def get_assignee_name (self, obj):
        if obj.assignee :
            return obj.assignee.username
        return "Unassigned"

    def get_watchers_names (self, obj):
        return [user.username for user in obj.watchers.all()]

        



class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'role', 'workspace', 'is_verified']
        
        read_only_fields = [
            'workspace', 
            'is_verified',
            'groups', 
            'user_permissions', 
            'is_staff', 
            'is_superuser', 
            'is_active', 
            'date_joined', 
            'last_login'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username',read_only=True)
    task_title = serializers.CharField(source='task.title',read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'content', 'task', 'author', 'created_at','author_name',"task_title"]
        read_only_fields = ['author', 'created_at']
