from typing import Any, ClassVar

from elasticsearch.dsl import (
    AsyncFacetedSearch,
    DateHistogramFacet,
    Facet,
    RangeFacet,
    TermsFacet,
)

from app.indexes import CommentDoc, NotificationDoc, TaskDoc, UserDoc, UserGroupDoc


class TaskFacetedSearch(AsyncFacetedSearch):
    """Faceted search configuration for tasks.

    Provides faceted search capabilities for tasks with filtering by
    status, priority, difficulty, skill spheres, group, and assignees.
    Uses multi-field text search with weighted fields for relevance ranking.

    Attributes:
        doc_types (ClassVar[list[Any]]): Document types to search (TaskDoc)
        fields (ClassVar[list[str]]): Fields to search with relevance weights
        facets (ClassVar[dict[str, Facet]]): Available facets for filtering
    """

    index = "tasks_v1"
    doc_types: ClassVar[list[Any]] = [TaskDoc]
    fields: ClassVar[list[str]] = ["title^3", "description^2", "group_name"]
    facets: ClassVar[dict[str, Facet]] = {
        "status": TermsFacet(field="status.keyword"),
        "priority": TermsFacet(field="priority.keyword"),
        "difficulty": TermsFacet(field="difficulty.keyword"),
        "spheres": TermsFacet(field="spheres.keyword"),
        "group_id": TermsFacet(field="group_id"),
        "assignee_ids": TermsFacet(field="assignee_ids.keyword"),
        "is_active": TermsFacet(field="is_active"),
        "date_created": DateHistogramFacet(field="created_at", fixed_interval="30d"),
        "date_deadline": DateHistogramFacet(field="deadline", fixed_interval="7d"),
    }


class UserFacetedSearch(AsyncFacetedSearch):
    """Faceted search configuration for users.

    Provides faceted search capabilities for users with filtering by
    role, active status, and group membership. Uses multi-field text
    search with weighted fields for relevance ranking.

    Attributes:
        doc_types (ClassVar[list[Any]]): Document types to search (UserDoc)
        fields (ClassVar[list[str]]): Fields to search with relevance weights
        facets (ClassVar[dict[str, Facet]]): Available facets for filtering
    """

    index = "users_v1"
    doc_types: ClassVar[list[Any]] = [UserDoc]
    fields: ClassVar[list[str]] = ["username^3", "first_name^2", "last_name^2", "email"]
    facets: ClassVar[dict[str, Facet]] = {
        "role": TermsFacet(field="role.keyword"),
        "is_active": TermsFacet(field="is_active"),
        "group_ids": TermsFacet(field="group_ids.keyword"),
    }


class GroupFacetedSearch(AsyncFacetedSearch):
    """Faceted search configuration for user groups.

    Provides faceted search capabilities for groups with filtering by
    visibility, join policy, and invite policy. Uses multi-field text
    search with weighted fields for relevance ranking.

    Attributes:
        doc_types (ClassVar[list[Any]]): Document types to search (UserGroupDoc)
        fields (ClassVar[list[str]]): Fields to search with relevance weights
        facets (ClassVar[dict[str, Facet]]): Available facets for filtering
    """

    index = "groups_v1"
    doc_types: ClassVar[list[Any]] = [UserGroupDoc]
    fields: ClassVar[list[str]] = ["name^3", "description^2", "admin_username"]
    facets: ClassVar[dict[str, Facet]] = {
        "visibility": TermsFacet(field="visibility.keyword"),
        "join_policy": TermsFacet(field="join_policy.keyword"),
        "invite_policy": TermsFacet(field="invite_policy.keyword"),
        "is_active": TermsFacet(field="is_active"),
        "level": RangeFacet(
            field="level",
            ranges=[
                ("root", (None, 1)),  # level 0
                ("l1", (1, 2)),  # level 1
                ("l2", (2, 3)),  # level 2
                ("l3", (3, 4)),  # level 3
                ("deep", (4, None)),  # level 4+
            ],
        ),
    }


class CommentFacetedSearch(AsyncFacetedSearch):
    """Faceted search configuration for comments.

    Provides faceted search capabilities for comments with filtering by
    task and user. Uses multi-field text search with weighted fields
    for relevance ranking.

    Attributes:
        doc_types (ClassVar[list[Any]]): Document types to search (CommentDoc)
        fields (ClassVar[list[str]]): Fields to search with relevance weights
        facets (ClassVar[dict[str, Facet]]): Available facets for filtering
    """

    index = "comments_v1"
    doc_types: ClassVar[list[Any]] = [CommentDoc]
    fields: ClassVar[list[str]] = ["content^2", "task_title", "username"]
    facets: ClassVar[dict[str, Facet]] = {
        "task_id": TermsFacet(field="task_id"),
        "user_id": TermsFacet(field="user_id"),
        "date_created": DateHistogramFacet(field="created_at", fixed_interval="7d"),
        "parent_id": TermsFacet(field="parent_id"),
    }


class NotificationFacetedSearch(AsyncFacetedSearch):
    """Faceted search configuration for notifications.

    Provides faceted search capabilities for notifications with filtering by
    type, status, sender, recipient, and target type. Uses multi-field text
    search with weighted fields for relevance ranking.

    Attributes:
        doc_types (ClassVar[list[Any]]): Document types to search (NotificationDoc)
        fields (ClassVar[list[str]]): Fields to search with relevance weights
        facets (ClassVar[dict[str, Facet]]): Available facets for filtering
    """

    index = "notifications_v1"
    doc_types: ClassVar[list[Any]] = [NotificationDoc]
    fields: ClassVar[list[str]] = [
        "title^3",
        "message^2",
        "type",
    ]
    facets: ClassVar[dict[str, Facet]] = {
        "type": TermsFacet(field="type.keyword"),
        "status": TermsFacet(field="status.keyword"),
        "sender_id": TermsFacet(field="sender_id"),
        "recipient_id": TermsFacet(field="recipient_id"),
        "target_type": TermsFacet(field="target_type.keyword"),
        "is_read": TermsFacet(field="is_read"),
        "date_created": DateHistogramFacet(field="created_at", fixed_interval="1d"),
    }
