# TaskFlow Tests

## Quick Start

```bash
make test      # SQLite (in-memory) — fast
make test-pg   # PostgreSQL — production-like (requires Docker)
```

---

## Architecture

```
tests/
├── base_conftest.py           # Common fixtures & helpers (SQLite + PostgreSQL)
├── conftest.py                # Switcher: uses conftest_sqlite or pg_conftest
├── conftest_sqlite.py         # SQLite fixtures
├── pg_conftest.py             # PostgreSQL fixtures (Testcontainers)
├── integration/               # API endpoint tests (187 tests)
│   ├── test_auth_endpoints.py         # Auth (register, login, token)
│   ├── test_admin_endpoints.py        # Admin (users, stats)
│   ├── test_group_endpoints.py        # Groups CRUD
│   ├── test_task_endpoints.py         # Tasks CRUD
│   ├── test_user_endpoints.py         # Users (profile, search)
│   ├── test_notification_endpoints.py # Notifications
│   ├── test_xp_endpoints.py           # XP, levels, titles
│   ├── test_edge_cases.py             # Edge cases
│   ├── test_comprehensive_edge_cases.py
│   └── test_migrations.py             # DB migrations
└── unit/                      # Service unit tests (111 tests)
    ├── test_admin_service.py          # AdminService
    ├── test_auth_service.py          # AuthenticationService
    ├── test_base_service.py          # Base services
    ├── test_group_service.py         # GroupService
    ├── test_comment_service.py       # CommentService
    ├── test_notification_service.py  # NotificationService
    ├── test_rating_service.py        # RatingService
    ├── test_sse_service.py           # SSEService
    ├── test_xp_service.py           # XPService
    ├── test_permission.py            # Permission checks
    ├── test_schemas.py                # Schema validation
    ├── test_es_indexer.py            # ElasticsearchIndexer
    └── test_es_search.py             # ElasticsearchSearch
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

### conftest_sqlite.py (SQLite)

Session-scoped fixtures:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `test_engine` | session | SQLite in-memory engine |
| `session_factory` | session | Session factory |
| `init_rbac` | session | RBAC seeding (autouse) |
| `test_client` | session | HTTP client with ES mocks |
| `auth_headers` | function | Random user auth headers |
| `admin_auth_headers` | function | Random admin auth headers |
| `testuser_auth_headers` | function | Fixed "testuser" for strict tests |
| `testadmin_auth_headers` | function | Fixed "testadmin" for strict tests |
| `cleanup_test_data` | function | Cleanup after each test (autouse) |
| `mock_db` | function | AsyncMock for unit tests |
| `mock_es` | function | Mock Elasticsearch client |
| `mock_indexer` | function | Mock ElasticsearchIndexer |

### pg_conftest.py (PostgreSQL)

Same fixtures as SQLite but:
- Uses `postgresql+asyncpg://` driver
- Uses `TRUNCATE CASCADE` for cleanup
- Requires `POSTGRES_DB` env var set (e.g., `POSTGRES_DB=1 make test-pg`)

---

## Integration Tests (187 tests)

### test_auth_endpoints.py (23 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestRegister` | 7 | Register validation, duplicates |
| `TestLogin` | 4 | Login, wrong password, email/username |
| `TestAccessToken` | 2 | Token generation |
| `TestRefreshToken` | 2 | Token refresh |
| `TestAuthMiddleware` | 8 | Auth middleware behavior |

### test_admin_endpoints.py (13 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestAdminUsers` | 4 | Get/delete users |
| `TestAdminStats` | 1 | Statistics |
| `TestAdminUnauthorized` | 2 | Unauthorized access |
| `TestHealthCheck` | 2 | Health/metrics |
| `TestAdminEdgeCases` | 4 | Edge cases |

### test_group_endpoints.py (36 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestCreateGroup` | 3 | Create group, duplicates |
| `TestGetGroup` | 4 | Get owned/not-owned |
| `TestSearchGroups` | 6 | Search with filters |
| `TestJoinGroup` | 3 | Join open/closed groups |
| `TestUpdateGroup` | 3 | Update group |
| `TestDeleteGroup` | 3 | Delete group |
| `TestMemberManagement` | 6 | Add/remove members |
| `TestExitGroup` | 2 | Exit group |
| `TestGroupVisibility` | 2 | Visibility checks |
| `TestRoleAssignment` | 4 | Role management |

### test_task_endpoints.py (47 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestCreateTask` | 5 | Create, duplicates |
| `TestSearchTasks` | 8 | Search with filters |
| `TestUpdateTask` | 5 | Update task, status |
| `TestDeleteTask` | 4 | Delete task |
| `TestTaskMemberManagement` | 6 | Add/remove members |
| `TestJoinTask` | 3 | Join task |
| `TestExitTask` | 2 | Exit task |
| `TestSearchAssignedTasks` | 3 | Assigned tasks |
| `TestTaskEdgeCases` | 11 | Edge cases |

### test_user_endpoints.py (29 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestGetMyProfile` | 2 | Get profile |
| `TestSearchUsers` | 6 | Search users |
| `TestUpdateProfile` | 5 | Update profile |
| `TestDeleteProfile` | 3 | Delete profile |
| `TestGroupAdmin` | 2 | Get group admin |
| `TestSearchUsersInGroup` | 3 | Group members |
| `TestSearchUsersInTask` | 3 | Task members |
| `TestGetTaskOwner` | 2 | Task owner |
| `TestUserEdgeCases` | 3 | Edge cases |

### test_notification_endpoints.py (17 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestGetNotifications` | 6 | Get notifications |
| `TestGetUnreadCount` | 2 | Unread count |
| `TestMarkNotificationRead` | 2 | Mark as read |
| `TestMarkAllNotificationsRead` | 2 | Mark all read |
| `TestNotificationEdgeCases` | 5 | Edge cases |

### test_xp_endpoints.py (16 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestGetXP` | 3 | Get XP |
| `TestGetLevel` | 3 | Get level |
| `TestGetTitle` | 2 | Get title |
| `TestGetProgress` | 3 | Progress to next level |
| `TestXPEdgeCases` | 5 | Edge cases |

### test_edge_cases.py (6 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestGroupVisibility` | 1 | Visibility edge cases |
| `TestGroupMembers` | 2 | Member edge cases |
| `TestUserSearchEdgeCases` | 3 | Search validation |

---

## Unit Tests (111 tests)

### test_es_indexer.py (18 tests)

| Tests | Description |
|-------|-------------|
| 9 | ElasticsearchIndexer (index, delete) |
| 7 | ElasticsearchSearch (faceted search) |
| 2 | ElasticsearchHelper (es_helper) |

### test_es_search.py (17 tests)

| Tests | Description |
|-------|-------------|
| 8 | ElasticsearchSearch |
| 3 | ElasticsearchHelper |
| 5 | FacetedSearch classes |
| 1 | Private helpers |

### test_xp_service.py (19 tests)

| Tests | Description |
|-------|-------------|
| 3 | Base XP calculation |
| 3 | Time bonus |
| 5 | Streak bonus |
| 2 | Distribute XP |
| 1 | Calculate task XP |
| 2 | Level from XP |
| 1 | Get title |
| 1 | XP to next level |
| 1 | Progress percent |

### test_rating_service.py (8 tests)

| Tests | Description |
|-------|-------------|
| 3 | Create rating |
| 3 | Delete rating |
| 2 | Get ratings |

### test_sse_service.py (5 tests)

| Tests | Description |
|-------|-------------|
| 1 | SSE connect |
| 1 | SSE disconnect |
| 1 | Send notification |
| 1 | Event generator |
| 1 | Get SSE service |

### test_permission.py (4 tests)

| Tests | Description |
|-------|-------------|
| 4 | Permission checks (require_permissions_db) |

### test_schemas.py (15 tests)

| Tests | Description |
|-------|-------------|
| 3 | Task schemas |
| 5 | User schemas |
| 7 | Edge cases |

### test_comment_service.py (5 tests)

| Tests | Description |
|-------|-------------|
| 5 | Comment CRUD operations |

### test_notification_service.py (3 tests)

| Tests | Description |
|-------|-------------|
| 3 | Notification send operations |

### test_admin_service.py (5 tests)

| Tests | Description |
|-------|-------------|
| 5 | Admin operations (delete user, stats) |

### test_auth_service.py (2 tests)

| Tests | Description |
|-------|-------------|
| 2 | Register operations |

### test_base_service.py (6 tests)

| Tests | Description |
|-------|-------------|
| 6 | Base service operations |

### test_group_service.py (6 tests)

| Tests | Description |
|-------|-------------|
| 6 | Group service operations |

---

## Test Coverage

| Category | Tests | Coverage |
|----------|-------|----------|
| Integration | 187 | API endpoints |
| Unit | 111 | Services |
| **Total** | **298** | |

Run with coverage:
```bash
make test-coverage
```

Or manually:
```bash
uv run pytest --cov=app --cov-report=term-missing tests/
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `taskflow_test` | PostgreSQL database name (set for test-pg) |
| `POSTGRES_USER` | `user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `pass` | PostgreSQL password |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |

---

## Testing Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Fixtures**: Use fixtures for common setup (auth, test data)
3. **Cleanup**: Tests clean up after themselves (`cleanup_test_data`)
4. **Mock ES**: Elasticsearch is mocked in tests (no real ES connection needed)
5. **Deterministic**: Use fixed users (`testuser`, `testadmin`) for strict assertions
6. **Random data**: Use `uuid` for unique data in flexible tests

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests with SQLite |
| `make test-pg` | Run all tests with PostgreSQL |
| `make test-coverage` | Run tests with coverage |
| `make lint` | Run ruff and mypy |
| `make format` | Auto-format code |