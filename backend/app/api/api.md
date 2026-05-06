# TaskFlow API

Full API documentation for TaskFlow task management system with RPG elements.

---

## Authentication

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/api/v1/auth` | Register new user |
| POST | `/api/v1/auth/token` | Login (username/password) |
| POST | `/api/v1/auth/access-token` | Get access token from refresh token |
| POST | `/api/v1/auth/refresh-token` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout |

---

## Users

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/users/me` | Get current user profile |
| GET | `/api/v1/users/{user_id}` | Get user by ID |
| PATCH | `/api/v1/users/me` | Update current user profile |
| DELETE | `/api/v1/users/me` | Delete current user profile |
| GET | `/api/v1/users/groups/{group_id}/admin` | Get group admin |
| GET | `/api/v1/users/tasks/{task_id}/owner` | Get task owner |
| GET | `/api/v1/users/search` | Search users |

---

## Tasks

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/api/v1/tasks/groups/{group_id}` | Create task in group |
| GET | `/api/v1/tasks/` | List tasks (with filters) |
| GET | `/api/v1/tasks/{task_id}` | Get task by ID |
| PATCH | `/api/v1/tasks/{task_id}` | Update task |
| DELETE | `/api/v1/tasks/{task_id}` | Leave/unassign from task |
| POST | `/api/v1/tasks/{task_id}/join-requests` | Request to join task |
| GET | `/api/v1/tasks/{task_id}/join-requests` | Get task join requests |
| POST | `/api/v1/tasks/{task_id}/join-requests/{request_id}/approve` | Approve join request |
| POST | `/api/v1/tasks/{task_id}/join-requests/{request_id}/reject` | Reject join request |
| POST | `/api/v1/tasks/{task_id}/status` | Update task status |
| POST | `/api/v1/tasks/{task_id}/assign` | Assign user to task |
| DELETE | `/api/v1/tasks/{task_id}/assign/{user_id}` | Unassign user from task |
| GET | `/api/v1/tasks/{task_id}/assignees` | Get task assignees |
| POST | `/api/v1/tasks/{task_id}/spheres` | Update task spheres |
| GET | `/api/v1/tasks/{task_id}/history` | Get task history |

---

## Groups

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/api/v1/groups` | Create group |
| GET | `/api/v1/groups/` | List groups (with filters) |
| GET | `/api/v1/groups/{group_id}` | Get group by ID |
| PATCH | `/api/v1/groups/{group_id}` | Update group |
| DELETE | `/api/v1/groups/{group_id}` | Delete group |
| POST | `/api/v1/groups/{group_id}/join` | Join group |
| POST | `/api/v1/groups/{group_id}/leave` | Leave group |
| POST | `/api/v1/groups/{group_id}/members/{user_id}` | Add member to group |
| DELETE | `/api/v1/groups/{group_id}/members/{user_id}` | Remove member from group |
| GET | `/api/v1/groups/{group_id}/members` | Get group members |
| GET | `/api/v1/groups/{group_id}/join-requests` | Get group join requests |
| POST | `/api/v1/groups/{group_id}/join-requests/{request_id}/approve` | Approve join request |
| POST | `/api/v1/groups/{group_id}/join-requests/{request_id}/reject` | Reject join request |
| GET | `/api/v1/groups/{group_id}/tasks` | Get group tasks |
| GET | `/api/v1/groups/{group_id}/subgroups` | Get subgroups |

---

## Comments

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/api/v1/comments/tasks/{task_id}/comments` | Create comment |
| GET | `/api/v1/comments/tasks/{task_id}/comments` | Get task comments |
| GET | `/api/v1/comments/comments/{comment_id}` | Get comment by ID |
| PATCH | `/api/v1/comments/comments/{comment_id}` | Update comment |
| DELETE | `/api/v1/comments/comments/{comment_id}` | Delete comment |

---

## Notifications

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/notifications/` | List notifications |
| GET | `/api/v1/notifications/unread-count` | Get unread count |
| PUT | `/api/v1/notifications/{notification_id}/read` | Mark as read |
| PUT | `/api/v1/notifications/read-all` | Mark all as read |
| GET | `/api/v1/notifications-events/` | SSE stream for real-time notifications |

---

## Search

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/search/users` | Search users |
| GET | `/api/v1/search/tasks` | Search tasks |
| GET | `/api/v1/search/groups` | Search groups |

---

## XP and Ratings

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/xp/` | Get XP statistics |
| GET | `/api/v1/xp/level` | Get current level |
| GET | `/api/v1/xp/title` | Get title |
| GET | `/api/v1/xp/progress` | Get progress to next level |
| GET | `/api/v1/xp/{user_id}/xp` | Get user XP by sphere |
| POST | `/api/v1/xp/{user_id}/xp` | Add XP to user |
| GET | `/api/v1/ratings/leaderboard` | Get leaderboard |

---

## Admin

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/admin/users/` | List all users |
| DELETE | `/api/v1/admin/users/{user_id}` | Delete user (admin) |
| GET | `/api/v1/admin/stats` | Get system statistics |
| POST | `/api/v1/admin/create-admin` | Create admin user |

---

## Groups (by user)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/user-groups/` | Get user groups |
| GET | `/api/v1/user-groups/{group_id}` | Get user group by ID |

---

## Notes

- All endpoints require authentication except `/api/v1/auth` (register, login)
- Permission system uses RBAC with context-specific roles
- Full documentation available at `/docs` (Swagger UI)