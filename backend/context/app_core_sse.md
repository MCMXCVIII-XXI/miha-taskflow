# app_core_sse_context.md;

## 1. Purpose of the directory`
The `app/core/sse/` directory serves as the real-time notification infrastructure layer. It contains the SSE (Server-Sent Events) manager that provides real-time communication between the server and connected clients.

## 2. Typical contents`
- `__init__.py` - SSE module initialization and exports`
- `manager.py` - SSE connection management and event broadcasting`

## 3. How key modules work`

- `manager.py`:`
  - Input: Event data, client connections, subscription requests`
  - Output: Real-time event delivery to connected clients, connection management`
  - What it does: Manages SSE connections, broadcasts events to subscribed clients, tracks connection state`
  - How it interacts with other layers: Used by notification services in `service/`, integrates with API endpoints in `api/v1/endpoints/notification.py` for connection handling, works with configuration from `core/config/``

## 4. Request flow and integration`
A typical SSE event flow through the SSE layer:`
1. Client initiates SSE connection by requesting endpoint in `api/v1/endpoints/notification.py``
2. Endpoint creates SSE stream and registers connection with `manager.py``
3. Application events occur (task assignment, comment added, etc.)`
4. Services call notification system which uses SSE manager to broadcast events`
5. SSE manager formats events and delivers to all subscribed clients`
6. Connected clients receive real-time updates through persistent HTTP connections`

## 5. Summary`
The `app/core/sse/` directory provides real-time event streaming for live notifications. It enables responsive user experiences by pushing updates from the server to connected clients without requiring polling. This directory integrates with notification services and API endpoints to deliver real-time features.