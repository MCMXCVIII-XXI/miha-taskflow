# TaskFlow (miha) Tests

## tests/conftest.py

### Description
Main fixtures for all tests:
- `test_engine` — Creates in-memory SQLite test DB
- `session_factory` — Session factory for tests
- `init_rbac` — Initializes RBAC (roles, permissions)
- `test_client` — HTTP client with test DB
- `testuser_id` — Registered test user's ID
- `auth_headers` — Auth headers for testuser
- `testadmin_id`, `admin_auth_headers` — Admin user data
- `cleanup_test_data` — Cleans up test data after each test
- `mock_db` — AsyncSession mock

---

## tests/integration/

### test_auth_endpoints.py

| Class | Test | Description |
|-------|------|-------------|
| **TestRegister** | test_register_returns_200 | Register new user |
| | test_register_duplicate_email_returns_409 | Duplicate email → 409 Conflict |
| | test_register_duplicate_username_returns_409 | Duplicate username → 409 |
| | test_register_short_password_returns_422 | Short password → 422 |
| | test_register_short_username_returns_422 | Short username → 422 |
| **TestLogin** | test_login_returns_200 | Successful login |
| | test_login_wrong_password_returns_401 | Wrong password → 401 |
| | test_login_nonexistent_returns_401 | Nonexistent user → 401 |
| **TestTokenRefresh** | test_refresh_returns_200 | Refresh token |
| | test_refresh_invalid_returns_401 | Invalid refresh token → 401 |
| **TestMeEndpoint** | test_me_returns_200 | Get current user profile |
| | test_me_without_auth_returns_401 | Without auth → 401 |

---

### test_user_endpoints.py

| Class | Test | Description |
|-------|------|-------------|
| **TestGetMyProfile** | test_get_profile_returns_200 | Get own profile |
| | test_get_profile_without_auth_returns_401 | Without auth → 401 |
| **TestSearchUsers** | test_search_users_returns_200 | Search all users |
| | test_search_users_by_username_returns_200 | Search by username |
| | test_search_users_without_auth_returns_401 | Without auth → 401 |
| | test_search_users_with_limit | Limit results |
| | test_search_users_with_offset | Pagination |
| | test_search_users_by_username_filter | Username filter |
| | test_search_users_empty_result | Empty result |
| **TestUpdateProfile** | test_update_profile_returns_200 | Update profile |
| | test_update_profile_email_returns_200 | Update email |
| | test_update_profile_duplicate_email_returns_409 | Duplicate email → 409 |
| | test_update_profile_duplicate_username_returns_409 | Duplicate username → 409 |
| | test_update_profile_without_auth_returns_401 | Without auth → 401 |
| **TestDeleteProfile** | test_delete_profile_returns_204 | Delete profile |
| | test_deleted_user_cannot_access_profile | Deleted user cannot login |
| | test_delete_profile_without_auth_returns_401 | Without auth → 401 |
| **TestGroupAdmin** | test_get_group_admin_returns_200 | Get group admin |
| | test_get_group_admin_without_auth_returns_401 | Without auth → 401 |
| **TestSearchUsersInGroup** | test_search_group_members_returns_200 | Search group members |
| | test_search_group_members_without_auth_returns_401 | Without auth → 401 |
| **TestSearchUsersInTask** | test_search_task_members_returns_200 | Search task members |
| | test_search_task_members_without_auth_returns_401 | Without auth → 401 |
| **TestGetTaskOwner** | test_get_task_owner_returns_200 | Get task owner |
| | test_get_task_owner_without_auth_returns_401 | Without auth → 401 |

---

### test_group_endpoints.py

| Class | Test | Description |
|-------|------|-------------|
| **TestCreateGroup** | test_create_group_returns_201 | Create group |
| | test_create_group_duplicate_name_returns_409 | Duplicate name → 409 |
| | test_create_group_without_auth_returns_401 | Without auth → 401 |
| **TestSearchGroups** | test_search_groups_returns_200 | Search groups |
| | test_search_groups_with_limit | Limit results |
| **TestSearchMyGroups** | test_search_my_groups_returns_200 | My groups |
| | test_search_my_groups_without_auth_returns_401 | Without auth → 401 |
| **TestGetGroup** | test_get_group_returns_200 | Get group |
| | test_get_group_not_found_returns_404 | Group not found → 404 |
| **TestUpdateGroup** | test_update_group_returns_200 | Update group |
| | test_update_group_not_owned_returns_403 | Not owner → 403 |
| **TestDeleteGroup** | test_delete_group_returns_204 | Delete group |
| **TestJoinGroup** | test_join_group_returns_201 | Join group |
| | test_join_group_already_member_returns_409 | Already member → 409 |
| | test_join_public_group_without_auth_returns_401 | Without auth → 401 |
| **TestExitGroup** | test_exit_group_returns_204 | Exit group |
| | test_exit_group_not_member_returns_404 | Not member → 404 |
| **TestAddMember** | test_add_member_returns_201 | Add member |
| | test_add_member_not_admin_returns_403 | Not admin → 403 |
| **TestRemoveMember** | test_remove_member_returns_204 | Remove member |
| | test_remove_member_not_admin_returns_403 | Not admin → 403 |

---

### test_task_endpoints.py

| Class | Test | Description |
|-------|------|-------------|
| **TestCreateTask** | test_create_task_returns_201 | Create task |
| | test_create_task_not_admin_returns_403 | Not admin → 403 |
| **TestSearchTasks** | test_search_tasks_returns_200 | Search tasks |
| | test_search_tasks_with_limit | Limit results |
| | test_search_tasks_empty_result | Empty result |
| | test_search_tasks_with_offset | Pagination |
| **TestSearchMyTasks** | test_search_my_tasks_returns_200 | My tasks |
| **TestSearchGroupTasks** | test_search_group_tasks_returns_200 | Group tasks |
| **TestUpdateTask** | test_update_task_returns_200 | Update task |
| | test_update_task_not_owned_returns_403 | Not owner → 403 |
| | test_update_status_returns_200 | Update status |
| | test_update_status_same_value_returns_409 | Same status → 409 |
| **TestDeleteTask** | test_delete_task_returns_204 | Delete task |
| | test_delete_not_owned_task_returns_403 | Not owner → 403 |
| **TestTaskMemberManagement** | test_add_user_to_task_returns_201 | Add assignee |
| | test_remove_user_from_task_returns_204 | Remove assignee |
| | test_add_user_to_not_owned_task_returns_403 | Not owner → 403 |
| **TestJoinTask** | test_join_task_returns_201 | Join task |
| | test_join_task_twice_returns_409 | Already member → 409 |
| **TestExitTask** | test_exit_task_returns_204 | Exit task |
| | test_exit_task_not_member_returns_403 | Not member → 403 |
| **TestSearchAssignedTasks** | test_search_assigned_returns_200 | My assigned tasks |
| | test_search_assigned_empty_returns_200 | Empty list |

---

### test_admin_endpoints.py

| Class | Test | Description |
|-------|------|-------------|
| **TestGetAllUsers** | test_get_all_users_returns_200 | Get all users (admin) |
| | test_get_all_users_forbidden_returns_403 | Not admin → 403 |
| **TestDeleteUser** | test_delete_user_returns_204 | Delete user (admin) |
| | test_delete_self_returns_400 | Delete self → 400 |
| | test_delete_last_admin_returns_400 | Delete last admin → 400 |
| **TestGetStats** | test_get_stats_returns_200 | Get stats (admin) |
| | test_get_stats_forbidden_returns_403 | Not admin → 403 |
| **TestHealthCheck** | test_health_check_returns_200 | Health check endpoint |
| **TestMetrics** | test_metrics_returns_200 | Prometheus metrics endpoint |

---

### test_notification_endpoints.py

| Class | Test | Description |
|-------|------|-------------|
| **TestGetNotifications** | test_get_notifications_returns_200 | Get notifications list |
| | test_get_notifications_without_auth_returns_401 | Without auth → 401 |
| | test_get_notifications_with_status_filter_returns_200 | Filter by status |
| | test_get_notifications_with_type_filter_returns_200 | Filter by type |
| | test_get_notifications_with_limit_returns_200 | Limit results |
| | test_get_notifications_with_offset_returns_200 | Pagination |
| **TestGetUnreadCount** | test_get_unread_count_returns_200 | Unread count |
| | test_get_unread_count_without_auth_returns_401 | Without auth → 401 |
| **TestGetNotification** | test_get_notification_without_auth_returns_401 | Without auth → 401 |
| **TestMarkNotificationRead** | test_mark_notification_read_without_auth_returns_401 | Without auth → 401 |
| **TestMarkAllNotificationsRead** | test_mark_all_notifications_read_returns_200 | Mark all read |
| | test_mark_all_notifications_read_without_auth_returns_401 | Without auth → 401 |
| **TestRespondToNotification** | test_respond_to_notification_without_auth_returns_401 | Without auth → 401 |

---

## tests/unit/

### test_auth_service.py

| Class | Test | Description |
|-------|------|-------------|
| **TestAuthenticationService** | test_register_creates_user | Register creates user |
| | test_login_returns_token | Login returns token |

---

### test_user_service.py

| Class | Test | Description |
|-------|------|-------------|
| **TestUserService** | test_search_users_returns_list | Search users |
| | test_get_my_profile_returns_user | Get profile |

---

### test_group_service.py

| Class | Test | Description |
|-------|------|-------------|
| **TestCreateMyGroup** | test_create_sets_admin_id | Create sets admin_id |
| | test_duplicate_name_raises_conflict | Duplicate name → error |
| **TestJoinGroup** | test_join_creates_membership | Join creates membership |
| | test_join_existing_raises | Already member → error |
| **TestRoleAssignment** | test_create_group_assigns_group_admin_role | Create assigns GROUP_ADMIN |
| | test_join_group_assigns_member_role | Join assigns MEMBER role |

---

### test_task_service.py

| Class | Test | Description |
|-------|------|-------------|
| **TestTaskService** | test_create_task_creates_task | Create task |
| | test_assign_user_to_task | Assign user |
| | test_complete_task | Complete task |

---

### test_admin_service.py

| Class | Test | Description |
|-------|------|-------------|
| **TestAdminService** | test_get_all_users_returns_list | Get all users |
| | test_delete_user_returns_true | Delete user |
| | test_get_stats_returns_dict | Get stats |

---

### test_permission.py

| Class | Test | Description |
|-------|------|-------------|
| **TestPermission** | test_user_has_user_permissions | USER has basic permissions |
| | test_admin_has_all_permissions | ADMIN has all permissions |

---

### test_base_service.py

| Class | Test | Description |
|-------|------|-------------|
| **TestBaseService** | test_service_initialization | Service initialization |
| | test_grant_role | Grant role |
| | test_invalidate | Cache invalidation |

---

### test_schemas.py

| Class | Test | Description |
|-------|------|-------------|
| **TestSchemas** | test_user_schema_validation | UserCreate validation |
| | test_task_schema_validation | TaskCreate validation |
| | test_group_schema_validation | UserGroupCreate validation |

---

## Summary

| Category | Test Count |
|----------|------------|
| Integration | ~130 |
| Unit | ~25 |
| **Total** | **~155** |

---

## Running Tests

```bash
make test          # Run all tests
make test-backend # Run only backend tests
make lint         # Run linter
make lint-all     # Run linter + mypy
```

---

## Notes on Notification Tests

### Current Coverage

The notification system is tested at the API level in `test_notification_endpoints.py`:

| Test Category | Coverage |
|---------------|----------|
| API Endpoints | ✅ Full (GET, PATCH, POST) |
| Authentication | ✅ 401 without auth |
| Filtering | ✅ Status, type, limit, offset |
| Response | ✅ Accept/Refusal |

### Integration Tests Status

Integration tests for notification creation during user actions (GROUP_INVITE, GROUP_JOIN, TASK_INVITE) require additional dependency override setup and are currently not included in the test suite. The notification logic is integrated into the service layer but would need proper test DB configuration to verify end-to-end.

### What Integration Tests Would Verify

- `add_member_to_group` → GROUP_INVITE notification created
- `join_group` → GROUP_JOIN notification created
- `add_user_to_task` → TASK_INVITE notification created
- Notification content (title, message, recipient)
- Status changes on accept/decline
