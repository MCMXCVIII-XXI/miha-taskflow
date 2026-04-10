from .permissions import PERMISSIONS

USER_PERMISSIONS = {
    "user:view:any",
    "user:view:own",
    "user:update:own",
    "user:delete:own",
    "group:create:own",
    "group:view:any",
    "group:join:any",
    "task:view:any",
    "task:join:any",
    "task:exit:own",
    "task:exit:assignee",
    "comment:create:own",
    "comment:view:any",
    "comment:update:own",
    "comment:delete:own",
    "rating:create:own",
    "rating:view:any",
    "rating:delete:own",
    "notification:view:own",
    "notification:respond:own",
}

MEMBER_PERMISSIONS = {
    "group:view:group",
    "group:exit:member",
    "task:view:group",
}

ASSIGNEE_PERMISSIONS = {
    "task:update:status",
}

GROUP_ADMIN_PERMISSIONS = {
    "group:view:own",
    "group:update:own",
    "group:delete:own",
    "group:add:own",
    "group:remove:own",
    "task:create:own",
    "task:view:own",
    "task:add:own",
    "task:remove:own",
    "task:update:own",
    "task:delete:own",
    "task:update:status",
    "task:exit:own",
}

ADMIN_PERMISSIONS = {p.name for p in PERMISSIONS}
