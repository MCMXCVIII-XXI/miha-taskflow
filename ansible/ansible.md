# Miha-TaskFlow Ansible Infrastructure

This repository contains a modular Ansible setup for TaskFlow. It keeps environment-specific inventory data separate from reusable automation logic, so the same codebase can manage development and production consistently without duplicating playbook logic.

## What this project does

This Ansible layout configures hosts and deploys the application stack in a predictable way:

- Installs the base dependencies needed for container-based deployment.
- Prepares Docker and Docker Compose on target machines.
- Renders environment-specific compose files from templates.
- Pulls and starts the required application services.
- Splits responsibilities across reusable roles instead of one large playbook.

The current architecture is organized around these roles:

- `common`
- `app`
- `db`
- `redis`
- `workers`
- `monitoring`
- `search`
- `edge`

`common` handles baseline machine setup, while the other roles deploy the service-specific stacks.

## Repository structure

```text
.
├── ansible.cfg
├── ansible.md
├── group_vars
│   └── vault.yml
├── inventories
│   ├── dev
│   │   ├── group_vars
│   │   │   └── all.yml
│   │   ├── host_vars
│   │   │   ├── backend.yml
│   │   │   ├── db.yml
│   │   │   ├── edge.yml
│   │   │   ├── monitoring.yml
│   │   │   ├── redis.yml
│   │   │   ├── search.yml
│   │   │   └── workers.yml
│   │   └── hosts.yml
│   └── prod
│       ├── group_vars
│       │   └── all.yml
│       ├── host_vars
│       │   ├── backend.yml
│       │   ├── db.yml
│       │   ├── edge.yml
│       │   ├── monitoring.yml
│       │   ├── redis.yml
│       │   ├── search.yml
│       │   └── workers.yml
│       └── hosts.yml
├── playbooks
│   └── site.yml
├── requirements.yml
└── roles
    ├── app
    ├── common
    ├── db
    ├── edge
    ├── monitoring
    ├── redis
    ├── search
    └── workers
```

`playbooks/site.yml` is the main entry point. `roles/*` contain reusable automation logic, and `inventories/dev` plus `inventories/prod` define environment-specific host data and variables.

## How the roles are organized

## `roles/common`

This role installs the base packages needed for the rest of the deployment. It prepares the machine for Docker-based workflows and sets up the system dependencies used by the other roles.

## `roles/app`

This role renders the application compose file and starts the backend stack. It also handles registry login when credentials are provided and pulls the backend image before starting the service.

## `roles/db`

This role creates the database compose file and starts the database stack. It keeps database deployment logic separate from application and edge concerns.

## `roles/redis`

This role deploys Redis through its own compose template and stack startup task. It stays isolated so the cache layer can be managed independently.

## `roles/workers`

This role renders the worker compose file, pulls the worker image, and starts the worker stack. It is responsible for background job execution.

## `roles/monitoring`

This role creates the monitoring compose file and starts the monitoring stack. It is intended for observability services such as Prometheus and node exporters.

## `roles/search`

This role renders the search stack compose file and starts the search service. It keeps search infrastructure separate from application runtime services.

## `roles/edge`

This role creates the edge compose file and starts the edge stack. It is the externally reachable layer that typically handles traffic entry and routing.

## Security model

SSH should not be open to everyone. Access should be limited to trusted IP ranges, VPN addresses, or other controlled sources.

Only machines that need external reachability should expose public access. In this project that is usually the `edge` host, while backend services should stay private.

Secrets should be kept out of plain text inventory files. Sensitive values belong in vault-encrypted files or another secure secret storage workflow.

## Prerequisites

Before running this project, make sure you have:

- Ansible installed.
- Access to the target hosts.
- SSH connectivity to the inventory machines.
- Docker and Docker Compose support available on the managed systems after bootstrap.
- A valid Ansible Vault password if you use encrypted variables.

## Configuration

Each environment has its own inventory directory.

That inventory should contain values such as:

- host addresses,
- host-specific connection settings,
- environment-wide compose variables,
- image names and tags,
- registry values,
- sensitive secrets stored through vault.

Before deploying, verify that placeholders are replaced with real values and that the hostnames in `hosts.yml` match the names referenced by your playbooks and roles.

## Quick start

## 1. Select the environment

```bash
cd inventories/dev
```

Use `inventories/prod` if you want to deploy production hosts.

## 2. Check the syntax

```bash
ansible-playbook -i inventories/dev/hosts.yml playbooks/site.yml --syntax-check
```

This validates the playbook structure before any real changes are made.

## 3. Review the dry run

```bash
ansible-playbook -i inventories/dev/hosts.yml playbooks/site.yml --check -vvv
```

This shows what Ansible would change without applying it.

## 4. Apply the configuration

```bash
ansible-playbook -i inventories/dev/hosts.yml playbooks/site.yml
```

Ansible will connect to the hosts, install prerequisites, render compose files, and start the required stacks.

## Outputs and result

After a successful run, the managed hosts should have:

- Docker installed.
- The compose project directory created.
- Environment-specific compose files rendered.
- The requested service stacks running.
- Backend, database, cache, search, edge, monitoring, and worker roles deployed according to inventory.

## Learning path behind this layout

This project follows a practical progression:

1. Learn Ansible inventory and variable scoping.
2. Build a `common` bootstrap role for base machine setup.
3. Add service-specific roles for each deployment target.
4. Render Docker Compose files from templates instead of maintaining static copies.
5. Separate dev and prod inventories while keeping the structure aligned.

That progression makes the project easier to understand and maintain than one large unstructured playbook.

## Notes for contributors

- Do not hardcode secrets in inventory files.
- Keep shared bootstrap logic in `roles/common`.
- Keep service deployment logic in separate roles.
- Keep `dev` and `prod` structurally aligned whenever possible.
- Prefer templates and variables over duplicated static deployment files.

## Future work

The structure is intentionally simple and can grow later without becoming messy. Additional services, more hosts, or tighter security policies can be added by extending the same pattern: small roles, clear inventories, and environment-specific variables.