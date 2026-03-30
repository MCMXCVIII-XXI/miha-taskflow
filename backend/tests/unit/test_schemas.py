import pytest
from pydantic import ValidationError

from app.schemas.task import TaskCreate, TaskPriority, TaskStatus, TaskUpdate
from app.schemas.user import UserCreate


class TestTaskSchemas:
    def test_task_create_validates_priority(self):
        """TaskCreate accepts valid priority values."""
        task_data = {
            "title": "Test Task",
            "description": "Test",
            "priority": "high",
            "group_id": 1,
        }
        task = TaskCreate(**task_data)
        assert task.priority == TaskPriority.HIGH

    def test_task_create_rejects_invalid_priority(self):
        """TaskCreate rejects invalid priority values."""
        task_data = {
            "title": "Test Task",
            "description": "Test",
            "priority": "invalid",
            "group_id": 1,
        }
        with pytest.raises(ValidationError):
            TaskCreate(**task_data)

    def test_task_priority_enum_values(self):
        """TaskPriority enum has correct values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"

    def test_task_status_enum_values(self):
        """TaskStatus enum has correct values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.DONE.value == "done"


class TestUserSchemas:
    def test_user_create_validates_email(self):
        """UserCreate validates email format."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User",
        }
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"

    def test_user_create_rejects_invalid_email(self):
        """UserCreate rejects invalid email format."""
        user_data = {
            "username": "testuser",
            "email": "not-an-email",
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User",
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_validates_password_length(self):
        """UserCreate enforces minimum password length."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Short1",
            "first_name": "Test",
            "last_name": "User",
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_user_create_validates_username_length(self):
        """UserCreate enforces minimum username length."""
        user_data = {
            "username": "ab",
            "email": "test@example.com",
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User",
        }
        with pytest.raises(ValidationError):
            UserCreate(**user_data)


class TestEdgeCases:
    def test_task_title_min_length(self):
        """Task title must be at least 3 characters."""
        task_data = {
            "title": "ab",
            "description": "Test",
            "priority": "high",
            "group_id": 1,
        }
        with pytest.raises(ValidationError):
            TaskCreate(**task_data)

    def test_task_title_max_length(self):
        """Task title must not exceed 200 characters."""
        task_data = {
            "title": "x" * 201,
            "description": "Test",
            "priority": "high",
            "group_id": 1,
        }
        with pytest.raises(ValidationError):
            TaskCreate(**task_data)

    def test_task_title_no_leading_spaces(self):
        """Task title cannot have leading spaces."""
        task_data = {
            "title": " Test Task",
            "description": "Test",
            "priority": "high",
            "group_id": 1,
        }
        with pytest.raises(ValidationError):
            TaskCreate(**task_data)

    def test_task_title_no_trailing_spaces(self):
        """Task title cannot have trailing spaces."""
        task_data = {
            "title": "Test Task ",
            "description": "Test",
            "priority": "high",
            "group_id": 1,
        }
        with pytest.raises(ValidationError):
            TaskCreate(**task_data)

    def test_task_priority_default_value(self):
        """Task priority defaults to MEDIUM."""
        task_data = {
            "title": "Test Task",
            "description": "Test",
            "group_id": 1,
        }
        task = TaskCreate(**task_data)
        assert task.priority == TaskPriority.MEDIUM

    def test_task_update_allows_partial_fields(self):
        """TaskUpdate allows partial updates."""
        update_data = {"title": "New Title"}
        task = TaskUpdate(**update_data)
        assert task.title == "New Title"

    def test_task_update_preserves_other_fields(self):
        """TaskUpdate preserves fields not provided."""
        update_data = {"title": "New Title"}
        task = TaskUpdate(**update_data)
        assert task.description is None
        assert task.priority is None
