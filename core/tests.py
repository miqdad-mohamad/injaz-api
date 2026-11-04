from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Workspace, CustomUser, Project, Task, Comment


class BaseAPITestCase(APITestCase):
    """
    Base setup for all tests. Creates two distinct workspaces to test isolation.
    """

    def setUp(self):
        # 1. Workspaces
        self.workspace_a = Workspace.objects.create(name="Company A")
        self.workspace_b = Workspace.objects.create(name="Company B")

        # 2. Users for Workspace A
        self.admin_a = CustomUser.objects.create_user(
            username='admin_a', email='admin_a@test.com', password='password123',
            workspace=self.workspace_a, role='AD'
        )
        self.member_a = CustomUser.objects.create_user(
            username='member_a', email='member_a@test.com', password='password123',
            workspace=self.workspace_a, role='ME'
        )

        # 3. Admin for Workspace B (To test isolation)
        self.admin_b = CustomUser.objects.create_user(
            username='admin_b', email='admin_b@test.com', password='password123',
            workspace=self.workspace_b, role='AD'
        )

        # 4. Project and Task in Workspace A
        self.project_a = Project.objects.create(
            name="Project A", description="Test", workspace=self.workspace_a
        )
        self.task_a = Task.objects.create(
            title="Task A", description="Test", project=self.project_a,
            assignee=self.member_a, created_by=self.admin_a
        )

        # 5. A user without a workspace (For testing workspace creation)
        self.free_user = CustomUser.objects.create_user(
            username='free_user', email='free@test.com', password='password123'
        )


class AuthAndUserTests(BaseAPITestCase):
    """
    Tests for Token Generation, User Creation, and Privilege Escalation prevention.
    """

    def test_obtain_token(self):
        # Try to get a token with correct credentials
        url = reverse('token_obtain_pair')
        response = self.client.post(
            url, {'username': 'admin_a', 'password': 'password123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data) 
        self.assertIn('refresh', response.data)

    def test_admin_can_create_user(self):
        self.client.force_authenticate(user=self.admin_a)
        url = reverse('customuser-list')
        data = {
            "username": "new_emp", "email": "new@test.com", "password": "password123",
            "is_staff": True  # Malicious attempt
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if workspace was auto-assigned and is_staff was ignored (Security check)
        new_user = CustomUser.objects.get(username="new_emp")
        self.assertEqual(new_user.workspace, self.workspace_a)
        self.assertFalse(new_user.is_staff)

    def test_member_cannot_create_user(self):
        self.client.force_authenticate(user=self.member_a)
        url = reverse('customuser-list')
        data = {"username": "hacker", "email": "h@test.com",
                "password": "password123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class WorkspaceTests(BaseAPITestCase):
    """
    Tests for Workspace creation and isolation.
    """

    def test_free_user_creates_workspace_and_becomes_admin(self):
        self.client.force_authenticate(user=self.free_user)
        url = reverse('workspace-list')
        response = self.client.post(
            url, {'name': 'New Startup'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.free_user.refresh_from_db()
        self.assertEqual(self.free_user.role, 'AD')
        self.assertEqual(self.free_user.workspace.name, 'New Startup')

    def test_admin_b_cannot_see_workspace_a(self):
        self.client.force_authenticate(user=self.admin_b)
        url = reverse('workspace-detail', kwargs={'pk': self.workspace_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProjectTests(BaseAPITestCase):
    """
    Tests for Project creation and Multi-Tenancy.
    """

    def test_admin_can_create_project(self):
        self.client.force_authenticate(user=self.admin_a)
        url = reverse('project-list')
        data = {"name": "New Project", "description": "Test"}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_project = Project.objects.get(name="New Project")
        self.assertEqual(new_project.workspace,
                         self.workspace_a)  # Auto-assigned

    def test_member_cannot_create_project(self):
        self.client.force_authenticate(user=self.member_a)
        url = reverse('project-list')
        data = {"name": "Member Project", "description": "Test"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_isolation_between_projects(self):
        self.client.force_authenticate(user=self.admin_b)
        url = reverse('project-detail', kwargs={'pk': self.project_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskTests(BaseAPITestCase):
    """
    Tests for Task creation, Permissions (Assignee vs Creator), and Isolation.
    """

    def test_admin_can_create_task(self):
        self.client.force_authenticate(user=self.admin_a)
        url = reverse('task-list')
        data = {
            "title": "New Task", "description": "Test",
            "project": self.project_a.id, "assignee": self.member_a.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_task = Task.objects.get(title="New Task")
        self.assertEqual(new_task.created_by, self.admin_a)  # Auto-assigned

    def test_member_cannot_create_task(self):
        # Normal member is not AD or MO
        self.client.force_authenticate(user=self.member_a)
        url = reverse('task-list')
        data = {"title": "Hacked Task", "project": self.project_a.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assignee_can_only_update_status(self):
        self.client.force_authenticate(user=self.member_a)
        url = reverse('task-detail', kwargs={'pk': self.task_a.id})

        # 1. Update status (Should pass)
        response = self.client.patch(url, {'status': 'DONE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Update title (Should fail)
        response = self.client.patch(url, {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_can_update_title(self):
        self.client.force_authenticate(user=self.admin_a)
        url = reverse('task-detail', kwargs={'pk': self.task_a.id})
        response = self.client.patch(
            url, {'title': 'Updated Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CommentTests(BaseAPITestCase):
    """
    Tests for Comments: Auto-author, Validation, and Isolation.
    """

    def test_create_comment(self):
        self.client.force_authenticate(user=self.member_a)
        url = reverse('comment-list')
        data = {"content": "This is a comment", "task": self.task_a.id}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_comment = Comment.objects.get(content="This is a comment")
        self.assertEqual(new_comment.author, self.member_a)  # Auto-assigned

    def test_cannot_comment_on_other_workspace_task(self):
        self.client.force_authenticate(user=self.admin_b)
        url = reverse('comment-list')
        # Admin B tries to comment on Task A (Belongs to Workspace A)
        data = {"content": "I shouldn't be here", "task": self.task_a.id}
        response = self.client.post(url, data, format='json')

        # Should fail because of our custom validate_task in the serializer
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
