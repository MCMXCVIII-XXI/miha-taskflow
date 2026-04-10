# app_core_sse_context.md

## 1. Purpose of the directory
The `app/core/sse/` directory serves as the real-time notification infrastructure layer of the TaskFlow application. It contains Server-Sent Events (SSE) implementation and management utilities that provide real-time communication between the server and connected clients. This directory represents the event streaming layer that enables live updates and notifications without requiring clients to poll for changes.

## 2. Typical contents
- `manager.py` - SSE connection management and event broadcasting
- `__init__.py` - SSE module initialization and exports
- Connection tracking and lifecycle management utilities
- Event formatting and delivery mechanisms
- Client subscription and filtering logic

## 3. How key modules work
- `manager.py`:
  - Input: Event data, client connections, subscription requests
  - Output: Real-time event delivery to connected clients, connection management
  - What it does: Manages SSE connections, broadcasts events to subscribed clients, tracks connection state
  - How it interacts with other layers: Used by notification services in `service/` to deliver real-time updates, integrates with FastAPI endpoints in `api/v1/endpoints/notification.py` for connection handling, works with configuration from `core/config.py` for SSE settings

## 4. Request flow and integration
A typical SSE event flow through the SSE layer:
1. Client initiates SSE connection by requesting endpoint in `api/v1/endpoints/notification.py`
2. Endpoint creates SSE stream and registers connection with manager in `manager.py`
3. Application events occur (task assignment, comment added, etc.) in various services
4. Services call notification system which uses SSE manager to broadcast events
5. SSE manager formats events and delivers to all subscribed clients
6. Connected clients receive real-time updates through persistent HTTP connections
7. Connection lifecycle is managed (heartbeats, cleanup, error handling) by SSE manager
8. All SSE operations are logged through `core/log/` for monitoring purposes

## 5. Summary
The `app/core/sse/` directory is the real-time event streaming layer that provides Server-Sent Events functionality for the TaskFlow application. It enables live notifications and updates to be pushed from the server to connected clients without requiring polling. This directory integrates with the notification services and API endpoints to deliver real-time user experiences. It serves as an essential component for creating responsive, interactive application features that require immediate feedback to users.