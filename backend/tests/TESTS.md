# TaskFlow (miha) Tests

## Quick Start

```bash
make test-sqlite  # SQLite (in-memory) — fast
make test-pg      # PostgreSQL — production-like
```

---

## Architecture

```
tests/
├── base_conftest.py           # Common fixtures & helpers
├── conftest.py                # SQLite-specific fixtures
├── conftest_pg.py             # PostgreSQL-specific fixtures
├── integration/               # API endpoint tests
│   ├── test_auth_endpoints.py
│   ├── test_admin_endpoints.py
│   ├── test_group_endpoints.py
│   ├── test_task_endpoints.py
│   ├── test_user_endpoints.py
│   ├── test_notification_endpoints.py
│   └── test_edge_cases.py
└── unit/                      # Service unit tests
    ├── test_admin_service.py
    ├── test_auth_service.py
    ├── test_base_service.py
    ├── test_group_service.py
    ├── test_permission.py
    └── test_schemas.py
```

---

## Fixtures

### base_conftest.py (Common)

Shared helpers used by both SQLite and PostgreSQL configs:

| Function | Description |
|----------|-------------|
| `seed_rbac()` | Seed RBAC data (roles, permissions) |
| `create_test_client()` | Create HTTP client with DB overrides |
| `cleanup_db()` | Clean up test data between tests |
| `register_user()` | Register or login user, return auth headers |
| `create_group_and_task()` | Create group + task, return IDs |
| `create_mock_db()` | Create AsyncMock for unit tests |

### conftest.py (SQLite)

Session-scoped fixtures:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `test_engine` | session | SQLite in-memory engine |
| `session_factory` | session | Session factory |
| `init_rbac` | session | RBAC seeding (autouse) |
| `test_client` | session | HTTP client |
| `auth_headers` | function | Random user auth headers |
| `admin_auth_headers` | function | Random admin auth headers |
| `testuser_auth_headers` | function | Fixed "testuser" for strict tests |
| `testadmin_auth_headers` | function | Fixed "testadmin" for strict tests |
| `cleanup_test_data` | function | Cleanup after each test (autouse) |
| `mock_db` | function | AsyncMock for unit tests |

### conftest_pg.py (PostgreSQL)

Same fixtures but:
- Uses `postgresql+asyncpg://` driver
- Uses `TRUNCATE CASCADE` for cleanup
- Requires `POSTGRES_DB` env var

---

## Integration Tests

### test_auth_endpoints.py

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestRegister` | 7 | Register with various inputs |
| `TestLogin` | 4 | Login by username/email, wrong password |
| `TestAccessToken` | 2 | Token generation |
| `TestRefreshToken` | 2 | Token refresh |

### test_admin_endpoints.py

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestAdminUsers` | 4 | Get/delete users as admin |
| `TestAdminStats` | 1 | Admin statistics |
| `TestAdminUnauthorized` | 2 | Unauthorized admin access |
| `TestHealthCheck` | 2 | Health/metrics endpoints |

### test_group_endpoints.py

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestCreateGroup` | 3 | Create group, duplicate name |
| `TestGetGroup` | 4 | Get owned/not-owned group |
| `TestSearchGroups` | 5 | Search with filters |
| `TestJoinGroup` | 2 | Join group |
| `TestUpdateGroup` | 3 | Update group |
| `TestDeleteGroup` | 3 | Delete group |
| `TestMemberManagement` | 6 | Add/remove members |
| `TestExitGroup` | 2 | Exit group |

### test_task_endpoints.py

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestCreateTask` | 5 | Create task, duplicates |
| `TestSearchTasks` | 6 | Search with filters |
| `TestUpdateTask` | 5 | Update task, status |
| `TestDeleteTask` | 4 | Delete task |
| `TestTaskMemberManagement` | 6 | Add/remove members |
| `TestJoinTask` | 2 | Join task |
| `TestExitTask` | 2 | Exit task |
| `TestSearchAssignedTasks` | 3 | Search assigned tasks |

### test_user_endpoints.py

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestGetMyProfile` | 2 | Get own profile |
| `TestSearchUsers` | 5 | Search users |
| `TestUpdateProfile` | 5 | Update profile |
| `TestDeleteProfile` | 3 | Delete profile |
| `TestGroupAdmin` | 2 | Get group admin |
| `TestSearchUsersInGroup` | 2 | Search group members |
| `TestSearchUsersInTask` | 2 | Search task members |
| `TestGetTaskOwner` | 2 | Get task owner |

### test_notification_endpoints.py

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestGetNotifications` | 6 | Get notifications, filters |
| `TestGetUnreadCount` | 2 | Unread count |
| `TestGetNotification` | 1 | Get notification (401) |
| `TestMarkNotificationRead` | 1 | Mark as read (401) |
| `TestMarkAllNotificationsRead` | 2 | Mark all as read |
| `TestRespondToNotification` | 1 | Respond (401) |

### test_edge_cases.py

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestGroupVisibility` | 1 | Group visibility edge cases |
| `TestGroupMembers` | 2 | Member management edge cases |
| `TestUserSearchEdgeCases` | 2 | User search validation |
| `TestTokenEdgeCases` | 2 | Token validation |
| `TestLoginEdgeCases` | 2 | Login validation |
| `TestProfileUpdateEdgeCases` | 2 | Profile update validation |

---

## Unit Tests

### test_admin_service.py

| Tests | Coverage |
|-------|----------|
| 5 | Admin service operations |

### test_auth_service.py

| Tests | Coverage |
|-------|----------|
| 2 | Auth service operations |

### test_base_service.py

| Tests | Coverage |
|-------|----------|
| 6 | Base service operations |

### test_group_service.py

| Tests | Coverage |
|-------|----------|
| 6 | Group service operations |

### test_permission.py

| Tests | Coverage |
|-------|----------|
| 4 | Permission checks |

### test_schemas.py

| Tests | Coverage |
|-------|----------|
| 15 | Schema validation |

---

## Coverage

Current coverage: **78%**

Run with coverage:
```bash
make test-coverage
```

Or manually:
```bash
uv run pytest --cov=app --cov-report=term-missing
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `taskflow_test` | PostgreSQL database name |
| `POSTGRES_USER` | `user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `pass` | PostgreSQL password |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
