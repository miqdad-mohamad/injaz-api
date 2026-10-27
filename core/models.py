from django.db import models
from django.contrib.auth.models import AbstractUser


class Workspace(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(
        upload_to='workspace_logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    workspace = models.ForeignKey(
        'Workspace', on_delete=models.CASCADE, null=True, blank=True, related_name='customusers')
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(
        max_length=100, null=True, blank=True)
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    reset_token_expiry = models.DateTimeField(null=True, blank=True)
    ROLE_CHOICES = [
        ('AD', 'Administrator'),
        ('MO', 'Moderator'),
        ('ME', 'Regular Member'),
    ]
    role = models.CharField(
        max_length=2,
        choices=ROLE_CHOICES,
        default='ME',
    )

    def __str__(self):
        return self.username


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    workspace = models.ForeignKey(
        'Workspace', on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, related_name='tasks')
    watchers = models.ManyToManyField(
        'CustomUser', related_name='watched_tasks', blank=True)
    assignee = models.ForeignKey(
        'CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    STATUS_CHOICES = [
        ('TO_DO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='TO_DO',
    )

    def __str__(self):
        return self.title


class Comment(models.Model):
    content = models.TextField()
    task = models.ForeignKey(
        'Task', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.task.title}'
