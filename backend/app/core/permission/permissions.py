from app.models import Permission, Role

ROLES = [
    Role(name="USER", description="Basic user"),
    Role(name="MEMBER", description="Group member"),
    Role(name="ASSIGNEE", description="Task assignee"),
    Role(name="GROUP_ADMIN", description="Group administrator"),
    Role(name="ADMIN", description="Application administrator"),
]

PERM_USER = [
    Permission.create(
        resource="user", action="view", context="any", description="View any users"
    ),
    Permission.create(
        resource="user", action="view", context="own", description="View own profile"
    ),
    Permission.create(
        resource="user",
        action="update",
        context="own",
        description="Update own profile",
    ),
    Permission.create(
        resource="user",
        action="delete",
        context="own",
        description="Delete own profile",
    ),
]
# TASK
PERM_TASK = [
    Permission.create(
        resource="task", action="view", context="any", description="View any tasks"
    ),
    Permission.create(
        resource="task", action="view", context="own", description="View own tasks"
    ),
    Permission.create(
        resource="task", action="create", context="own", description="Create own tasks"
    ),
    Permission.create(
        resource="task", action="update", context="own", description="Update own tasks"
    ),
    Permission.create(
        resource="task", action="delete", context="own", description="Delete own tasks"
    ),
    Permission.create(
        resource="task",
        action="update",
        context="status",
        description="Update task status",
    ),
    Permission.create(
        resource="task", action="view", context="group", description="View group tasks"
    ),
    Permission.create(
        resource="task", action="add", context="own", description="Add task"
    ),
    Permission.create(
        resource="task", action="remove", context="own", description="Remove task"
    ),
    Permission.create(
        resource="task", action="join", context="any", description="Join task"
    ),
    Permission.create(
        resource="task", action="exit", context="assignee", description="Exit task"
    ),
]
# GROUP
PERM_GROUP = [
    Permission.create(
        resource="group", action="view", context="any", description="View any groups"
    ),
    Permission.create(
        resource="group", action="view", context="own", description="View own group"
    ),
    Permission.create(
        resource="group", action="create", context="own", description="Create own group"
    ),
    Permission.create(
        resource="group", action="update", context="own", description="Update own group"
    ),
    Permission.create(
        resource="group", action="delete", context="own", description="Delete own group"
    ),
    Permission.create(
        resource="group", action="view", context="group", description="View group tasks"
    ),
    Permission.create(
        resource="group", action="add", context="own", description="Add task"
    ),
    Permission.create(
        resource="group", action="remove", context="own", description="Remove task"
    ),
    Permission.create(
        resource="group", action="join", context="any", description="Join task"
    ),
    Permission.create(
        resource="group", action="exit", context="member", description="Exit task"
    ),
]

PERMISSIONS = PERM_USER + PERM_GROUP + PERM_TASK
