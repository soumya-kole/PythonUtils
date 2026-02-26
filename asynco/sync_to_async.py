import asyncio
import time
import threading
import random
from alloy_admin import AlloyDBAdmin, QueueFullError


# ============================================================
# Fake Client  (simulates a blocking DB driver)
# ============================================================

class FakeAlloyDBClient:
    """
    Simulates a slow, blocking DB client.

    Behaviour driven by SQL content:
      - "FAIL"  → raises RuntimeError
      - "SLOW"  → sleeps 8s (longer than enqueue_timeout to test backpressure)
      - "FAST"  → sleeps 0.2s
      - default → sleeps random 1–3s
    """

    def execute_sql(self, sql: str):
        thread_name = threading.current_thread().name
        print(f"  [{thread_name}] START  → {sql}")

        if "SLOW" in sql:
            delay = 8.0
        elif "FAST" in sql:
            delay = 0.2
        else:
            delay = random.uniform(1, 3)

        time.sleep(delay)

        if "FAIL" in sql:
            print(f"  [{thread_name}] ERROR  → {sql}")
            raise RuntimeError(f"Simulated DB error for: {sql}")

        result = f"RESULT({sql})"
        print(f"  [{thread_name}] END    → {sql}  [{delay:.1f}s]")
        return result


# ============================================================
# Helper
# ============================================================

async def run_query(admin: AlloyDBAdmin, name: str, sql: str):
    try:
        result = await admin.execute_sql_async(sql)
        print(f"  {name} → SUCCESS: {result}")
    except QueueFullError as e:
        print(f"  {name} → QUEUE FULL: {e}")
    except Exception as e:
        print(f"  {name} → EXCEPTION: {e}")


# ============================================================
# Test Scenarios
# ============================================================

async def test_sequential_ordering(admin: AlloyDBAdmin):
    """
    Confirms calls execute one at a time despite being launched concurrently.
    """
    print("\n── Test 1: Sequential ordering ──")
    await asyncio.gather(
        run_query(admin, "W1", "SLOW SELECT 1"),
        run_query(admin, "W2", "FAST SELECT 2"),
        run_query(admin, "W3", "FAST SELECT 3"),
    )


async def test_error_isolation(admin: AlloyDBAdmin):
    """
    A FAIL query should reject only its own caller; neighbours succeed.
    """
    print("\n── Test 2: Error isolation ──")
    await asyncio.gather(
        run_query(admin, "W1", "FAST SELECT A"),
        run_query(admin, "W2", "FAIL SELECT B"),
        run_query(admin, "W3", "FAST SELECT C"),
    )


async def test_queue_backpressure(admin: AlloyDBAdmin):
    """
    Flood the queue while a SLOW query occupies the worker.
    Callers that cannot enqueue within `enqueue_timeout` get QueueFullError.

    Uses a tiny queue (size=2) and very short timeout to trigger overflow fast.
    """
    print("\n── Test 3: Queue backpressure ──")

    # Dedicated admin with a tiny queue and a tight enqueue timeout
    small_admin = AlloyDBAdmin(
        FakeAlloyDBClient(),
        queue_size=2,
        enqueue_timeout=1.0,
    )

    await asyncio.gather(
        run_query(small_admin, "W1", "SLOW SELECT hold"),  # occupies worker for 8s
        run_query(small_admin, "W2", "FAST SELECT slot1"),  # fills queue slot 1
        run_query(small_admin, "W3", "FAST SELECT slot2"),  # fills queue slot 2
        run_query(small_admin, "W4", "FAST SELECT overflow"),  # should be rejected
        run_query(small_admin, "W5", "FAST SELECT overflow2"),  # should be rejected
    )

    await small_admin.shutdown()


async def test_concurrent_startup_safety(admin: AlloyDBAdmin):
    """
    Hammer execute_sql_async before the worker has started to verify
    the asyncio.Lock prevents double-worker creation.
    """
    print("\n── Test 4: Concurrent startup safety ──")

    fresh_admin = AlloyDBAdmin(FakeAlloyDBClient())

    # Launch many callers simultaneously against an un-started admin
    await asyncio.gather(*[
        run_query(fresh_admin, f"W{i}", f"FAST SELECT {i}")
        for i in range(5)
    ])

    await fresh_admin.shutdown()


# ============================================================
# Entry Point
# ============================================================

async def main():
    client = FakeAlloyDBClient()
    admin = AlloyDBAdmin(client, queue_size=100, enqueue_timeout=5.0)

    await test_sequential_ordering(admin)
    await test_error_isolation(admin)
    await test_queue_backpressure(admin)
    await test_concurrent_startup_safety(admin)

    await admin.shutdown()
    print("\nAll tests complete.")


if __name__ == "__main__":
    asyncio.run(main())