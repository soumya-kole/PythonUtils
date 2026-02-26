import asyncio
from typing import Any, Protocol, Optional


# ============================================================
# Client Abstraction (Protocol for dependency injection)
# ============================================================

class AlloyDBClientProtocol(Protocol):
    def execute_sql(self, sql: str) -> Any:
        """
        Blocking method.
        Must be implemented by real or fake client.
        """
        ...


# ============================================================
# AlloyDBAdmin (Sequential Async Wrapper)
# ============================================================

class AlloyDBAdmin:
    """
    Sequential async wrapper over a blocking DB client.
    Safe for singleton usage.

    Guarantees:
    - Only one thread is active at a time (no concurrent DB access).
    - Async callers are queued and resolved in order.
    - Queue overflow raises QueueFullError instead of hanging.
    """

    def __init__(
        self,
        client: AlloyDBClientProtocol,
        queue_size: int = 100,
        enqueue_timeout: float = 5.0,
    ):
        self._client = client
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._started = False
        self._init_lock = asyncio.Lock()          # guards lazy startup
        self._enqueue_timeout = enqueue_timeout   # seconds to wait for a free slot

    # --------------------------------------------------------
    # Public Blocking API
    # --------------------------------------------------------

    def execute_sql(self, sql: str) -> Any:
        """Synchronous passthrough — use only outside async context."""
        return self._client.execute_sql(sql)

    # --------------------------------------------------------
    # Public Async API (Sequential Internally)
    # --------------------------------------------------------

    async def execute_sql_async(self, sql: str) -> Any:
        """
        Enqueue an SQL call for sequential execution.

        Raises:
            QueueFullError: if the queue is full after `enqueue_timeout` seconds.
        """
        await self._ensure_started()

        future = self._loop.create_future()
        try:
            await asyncio.wait_for(
                self._queue.put((sql, future)),
                timeout=self._enqueue_timeout,
            )
        except asyncio.TimeoutError:
            raise QueueFullError(
                f"DB queue is full ({self._queue.maxsize} slots). "
                f"Could not enqueue after {self._enqueue_timeout}s. "
                "Consider raising queue_size or reducing query volume."
            )

        return await future

    # --------------------------------------------------------
    # Worker Lifecycle
    # --------------------------------------------------------

    async def _ensure_started(self):
        """Thread-safe lazy startup using an asyncio.Lock."""
        if self._started:      # fast-path: no lock acquisition needed
            return
        async with self._init_lock:
            if not self._started:  # re-check inside the lock
                self._loop = asyncio.get_running_loop()
                self._worker_task = asyncio.create_task(self._worker())
                self._started = True

    async def shutdown(self):
        """Graceful shutdown — drains in-flight work before stopping."""
        if self._started:
            await self._queue.put((None, None))   # poison pill
            await self._worker_task
            self._started = False

    async def _worker(self):
        """
        Single background worker.
        Processes queue items strictly one at a time via asyncio.to_thread,
        which keeps exactly ONE thread busy at any moment.
        """
        while True:
            sql, future = await self._queue.get()

            if sql is None:  # poison pill — shutdown requested
                break

            try:
                result = await asyncio.to_thread(
                    self._client.execute_sql,
                    sql,
                )
                if not future.done():
                    future.set_result(result)
            except Exception as e:
                if not future.done():
                    future.set_exception(e)


# ============================================================
# Custom Exceptions
# ============================================================

class QueueFullError(Exception):
    """Raised when the DB queue is saturated and a caller times out waiting."""