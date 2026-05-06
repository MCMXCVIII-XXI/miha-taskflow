# app_core_log_context.md;

## 1. Purpose of the directory
The `app/core/log/` directory serves as the logging infrastructure layer of the TaskFlow application. It contains logging configuration, utilities, and standardized logging patterns that provide consistent, structured logging across all application components.

## 2. Typical contents
- `__init__.py` - Logging module initialization and exports
- `logging.py` - Logging configuration and utility functions
- `mask.py` - Data masking utilities for sensitive information

## 3. How key modules work

- `logging.py`:
  - Input: Log messages, contextual data, log levels
  - Output: Formatted log entries in structured logging format
  - What it does: Configures logging library, provides standardized logging functions, manages log formatting
  - How it interacts: Imported by all services, models, and utilities to log operations

- `mask.py`:
  - Input: Sensitive data that needs masking (passwords, tokens)
  - Output: Masked data safe for logging
  - What it does: Masks sensitive information in log entries
  - How it interacts: Used by logging.py and middleware for data protection

## 4. Request flow and integration
A typical logging operation flows through the log layer:
1. Application component calls logging function from `logging.py`
2. Logging function formats message with contextual information
3. Masking is applied to sensitive data via `mask.py`
4. Formatted log entry is output to configured handlers (console, file, external)
5. Monitoring systems can consume logs for alerting and analysis

## 5. Summary
The `app/core/log/` directory is the logging infrastructure layer that provides consistent, structured logging. It enables effective monitoring, debugging, and auditing by ensuring all components produce logs in a standardized format with appropriate contextual information.