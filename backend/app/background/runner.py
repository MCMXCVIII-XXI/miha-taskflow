import asyncio
import time
from asyncio.exceptions import TimeoutError as AsyncTimeoutError
from collections.abc import Coroutine
from concurrent.futures import Future
from threading import Lock, Thread
from typing import Any, TypeVar

from app.core.log import logging

from .exceptions import bt_exc

T = TypeVar("T")


logger = logging.get_logger(__name__)


class AsyncRunner:
    """
    Thread-safe runner for executing async coroutines \
        from synchronous code (Celery tasks).

    Creates a dedicated asyncio event loop in a daemon thread.
    Automatically manages loop startup/shutdown.
    Protects against hangs with configurable timeout (default: 30s).

    Usage:
        runner = AsyncRunner(timeout=10.0)
        result = runner.run(fetch_data_async())
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """
        Initialize AsyncRunner.

        Args:
            timeout: Maximum wait time for async operations (seconds)
        """
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: Thread | None = None
        self._stopped = False
        self._lock = Lock()  # Thread safety
        self._timeout = timeout

    def _run_loop(self) -> None:
        """Internal: Starts asyncio event loop in daemon thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_forever()
        finally:
            loop.close()

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """
        Ensures a running event loop is available.

        Logic:
        1. If stopped → raise RuntimeError
        2. If no running loop → start new thread+loop
        3. Otherwise → return existing loop

        Returns:
            Running asyncio event loop

        Raises:
            BackgroundRuntimeError: Failed to start loop after 10s
        """
        if self._stopped:
            raise bt_exc.BackgroundRuntimeError("AsyncRunner has been stopped")

        with self._lock:
            if self._loop is None or not self._loop.is_running():
                self._thread = Thread(target=self._run_loop, daemon=True)
                self._thread.start()

                # Wait for loop startup (max 10s)
                for _ in range(1000):
                    if self._loop and self._loop.is_running():
                        return self._loop
                    time.sleep(0.01)

                raise bt_exc.BackgroundRuntimeError(
                    "Failed to start event loop after 10 seconds"
                )

            return self._loop

    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Executes async coroutine from synchronous context.

        Perfect for Celery tasks calling async DB/ES helpers.

        Args:
            coro: Async coroutine to execute

        Returns:
            Coroutine execution result

        Raises:
            BackgroundAsyncTimeoutError: Operation timed out
        """
        loop = self._ensure_loop()
        future: Future[T] = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout=self._timeout)
        except AsyncTimeoutError as e:
            future.cancel()
            raise bt_exc.BackgroundAsyncTimeoutError(
                f"Async operation timed out after {self._timeout} seconds"
            ) from e

    def stop(self) -> None:
        """Gracefully stops event loop and thread (max 5s timeout)."""
        self._stopped = True
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5.0)


# Global singleton for convenience
async_runner = AsyncRunner()


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Convenience wrapper for running async code from Celery tasks.

    Example:
        @celery.task
        def process_data():
            data = run_async(fetch_from_es())
            return process(data)

    Args:
        coro: Any async coroutine

    Returns:
        Coroutine execution result
    """
    return async_runner.run(coro)
