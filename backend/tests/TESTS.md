# Miha-TaskFlow Tests

## Quick Start

```bash
make test-unit           # Unit tests (159 tests)
make test-integration    # Integration tests (pytest tests/integration/)
make test-e2e            # E2E tests with real external services
```

---

## Architecture

```
tests/
├── base_conftest.py                        # Common fixtures & helpers
├── conftest.py                             # Switcher: uses conftest_sqlite or pg_conftest
├── conftest_sqlite.py                      # SQLite fixtures
├── pg_conftest.py                          # PostgreSQL + Redis + ES fixtures (Testcontainers)
├── mock_cache.py                           # Cache mock utilities
├── unit/                                   # Service unit tests (159 tests)
│   ├── test_xp_service.py                  # XPService (27 tests)
│   ├── test_key_builder.py                 # Cache key builder
│   ├── test_permission.py                  # Permission checks
│   ├── test_schemas.py                     # Schema validation
│   ├── test_es_indexer.py                  # ElasticsearchIndexer
│   ├── test_es_search.py                   # ElasticsearchSearch
│   └── test_*_service.py                   # Service tests
├── integration/                            # API endpoint tests (~447 tests)
│   ├── test_auth_endpoints.py              # Auth: register, login, token refresh
│   ├── test_admin_endpoints.py             # Admin: users, stats, health
│   ├── test_group_endpoints.py             # Groups: CRUD, join, search
│   ├── test_task_endpoints.py              # Tasks: CRUD, assign, join request
│   ├── test_user_endpoints.py              # Users: profile, search, groups
│   ├── test_notification_endpoints.py      # Notifications: get, read, mark
│   ├── test_xp_endpoints.py                # XP: get, level, title, progress
│   ├── test_edge_cases.py                  # Edge cases: validation
│   ├── test_comprehensive_edge_cases.py    # Full edge cases
│   └── test_migrations.py                  # DB migrations
└── e2e/                                    # End-to-end tests (30 tests)
    ├── conftest.py                         # Imports pg_conftest + markers
    ├── test_full_user_flow.py              # User journey
    ├── test_es_search_cache.py             # ES + Redis caching
    ├── test_background_tasks.py            # Celery + outbox
    ├── test_auth_sessions.py               # Auth + sessions
    └── test_cli.py                         # CLI commands (create-admin, reindex)
```

---

## Fixtures

### base_conftest.py (Common)

Shared helpers used by all configs:

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

### pg_conftest.py (PostgreSQL + Redis + ES)

Uses Testcontainers for real external services:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `postgres_container` | session | PostgreSQL container |
| `redis_container` | session | Redis container |
| `es_container` | session | Elasticsearch container |
| `test_engine` | session | PostgreSQL async engine |
| `test_client` | session | HTTP client with all overrides |
| `isolated_es_client` | function | Isolated ES client per test |
| `schema_session_factory` | function | Schema-scoped session |
| `setup_celery()` | session | Celery eager mode |

Requires `POSTGRES_DB=1` env var set.

---

## Integration Tests (~447 tests)

### test_auth_endpoints.py

| Class | Tests | Description |
|-------|-------|-------------|
| `TestRegister` | 7 | Register validation, duplicates |
| `TestLogin` | 4 | Login, wrong password |
| `TestAccessToken` | 2 | Token generation |
| `TestRefreshToken` | 2 | Token refresh |
| `TestAuthMiddleware` | 8 | Auth middleware behavior |

### test_admin_endpoints.py

| Class | Tests | Description |
|-------|-------|-------------|
| `TestAdminUsers` | 4 | Get/delete users |
| `TestAdminStats` | 1 | Statistics |
| `TestAdminUnauthorized` | 2 | Unauthorized access |
| `TestHealthCheck` | 2 | Health/metrics |

### test_group_endpoints.py

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

### test_task_endpoints.py

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
| `TestJoinApproveNotifications` | 8 | Join request notifications |
| `TestTaskEdgeCases` | 11 | Edge cases |

### test_user_endpoints.py

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

### test_notification_endpoints.py

| Class | Tests | Description |
|-------|-------|-------------|
| `TestGetNotifications` | 6 | Get notifications |
| `TestGetUnreadCount` | 2 | Unread count |
| `TestMarkNotificationRead` | 2 | Mark as read |
| `TestMarkAllNotificationsRead` | 2 | Mark all read |
| `TestNotificationEdgeCases` | 5 | Edge cases |

### test_xp_endpoints.py

| Class | Tests | Description |
|-------|-------|-------------|
| `TestGetXP` | 3 | Get XP |
| `TestGetLevel` | 3 | Get level |
| `TestGetTitle` | 2 | Get title |
| `TestGetProgress` | 3 | Progress to next level |
| `TestXPEdgeCases` | 5 | Edge cases |

---

## Unit Tests (159 tests)

### test_xp_service.py (27 tests)

| Tests | Description |
|-------|-------------|
| 5 | Base XP calculation |
| 8 | Time bonus (early/late/zero) |
| 9 | Streak bonus |
| 5 | Integration scenarios |

### test_key_builder.py (25 tests)

| Tests | Description |
|-------|-------------|
| 5 | normalize_params |
| 4 | build_key |
| 11 | _infer_* methods |
| 5 | Constants |

### test_permission.py (11 tests)

| Tests | Description |
|-------|-------------|
| 7 | Permission granted/denied |
| 4 | Multiple permissions |

### test_es_indexer.py

| Tests | Description |
|-------|-------------|
| 9 | ElasticsearchIndexer |
| 7 | ElasticsearchSearch |

### test_es_search.py

| Tests | Description |
|-------|-------------|
| 8 | ElasticsearchSearch |
| 5 | FacetedSearch classes |

### test_schemas.py

| Tests | Description |
|-------|-------------|
| 3 | Task schemas |
| 5 | User schemas |
| 7 | Edge cases |

### Service Tests

| File | Tests | Description |
|------|-------|-------------|
| `test_rating_service.py` | 8 | Rating operations |
| `test_sse_service.py` | 5 | SSE operations |
| `test_comment_service.py` | 5 | Comment CRUD |
| `test_notification_service.py` | 3 | Notify operations |
| `test_admin_service.py` | 5 | Admin operations |
| `test_auth_service.py` | 2 | Auth operations |
| `test_base_service.py` | 6 | Base operations |
| `test_group_service.py` | 6 | Group operations |

---

## E2E Tests (30 tests)

Full stack tests with real external services (PostgreSQL + Redis + ES + Celery).

### test_full_user_flow.py (2 tests)

| Tests | Description |
|------|-------------|
| 1 | Complete user journey (register → group → task → complete) |
| 1 | Task with deadline bonus |

### test_es_search_cache.py (4 tests)

| Tests | Description |
|------|-------------|
| 3 | ES search + Redis caching |
| 1 | Celery → ES indexing (@celery_real) |

### test_background_tasks.py (3 tests)

| Tests | Description |
|------|-------------|
| 1 | Outbox processing |
| 2 | Celery real broker (@celery_real) |

### test_auth_sessions.py (4 tests)

| Tests | Description |
|------|-------------|
| 4 | Auth + sessions + token validation |

### test_cli.py (15 tests)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestCreateAdmin` | 3 | CLI create-admin command |
| `TestReindexAll` | 2 | reindex-all command |
| `TestReindexTasks` | 1 | reindex-tasks command |
| `TestReindexUsers` | 1 | reindex-users command |
| `TestReindexServiceE2E` | 5 | ReindexService with real DB + ES |
| `TestCliEdgeCases` | 3 | Edge cases |

Run E2E tests:
```bash
POSTGRES_DB=1 make test-e2e
# Or with real Celery broker:
POSTGRES_DB=1 python -m pytest tests/e2e/ -m celery_real -v
```

---

## Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| Integration | 411 | API endpoints |
| Unit | 159 | Services |
| E2E | 30 | Full stack |
| **Total** | **600** | |

Run with coverage:
```bash
make test-coverage
```

Or manually:
```bash
POSTGRES_DB=1 python -m pytest --cov=app --cov-report=term-missing tests/
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `taskflow_test` | Set for test-pg / e2e |
| `POSTGRES_USER` | `user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `pass` | PostgreSQL password |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |

---

## Testing Best Practices

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use fixtures for common setup
3. **Cleanup**: Tests clean up after themselves
4. **External Services**: Use Testcontainers for real Redis/ES in E2E
5. **Deterministic**: Use fixed users for strict assertions
6. **Random data**: Use `uuid` for unique test data

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make test-unit` | Unit tests (159 tests) |
| `make test-integration` | Integration tests (pytest tests/integration/) |
| `make test-e2e` | E2E tests (30 tests) |
| `make test-coverage` | Tests with coverage |
| `make test-unit-coverage` | Unit tests with coverage (pytest --cov) |
| `make test-integration-coverage` | Integration tests with coverage (pytest --cov) |
| `make test-integration-coverage-before-fall` | Integration tests with coverage before fall |
| `make test-e2e-coverage` | E2E tests with coverage (pytest --cov) |
| `make test-backend` | pytest all tests (unit + integration + e2e) |
