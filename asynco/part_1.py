"""
Python Async/Await Tutorial - Part 1: Fundamentals

Understanding async from the ground up for Python developers.
"""

import asyncio
import time


# ============================================================================
# CHAPTER 1: SYNC vs ASYNC - The Core Concept
# ============================================================================

print("=" * 80)
print("CHAPTER 1: SYNC vs ASYNC - Understanding the Difference")
print("=" * 80)

# Example 1: Synchronous (Blocking) Code
print("\n--- Example 1: SYNCHRONOUS (Normal Python) ---")

def make_coffee():
    """Make coffee - takes 3 seconds"""
    print("  ☕ Starting to make coffee...")
    time.sleep(3)  # Blocking! Nothing else can run
    print("  ☕ Coffee ready!")
    return "Coffee"

def make_toast():
    """Make toast - takes 2 seconds"""
    print("  🍞 Starting to make toast...")
    time.sleep(2)  # Blocking! Nothing else can run
    print("  🍞 Toast ready!")
    return "Toast"

print("\nSynchronous execution:")
start = time.time()
coffee = make_coffee()  # Wait for coffee (3s)
toast = make_toast()    # Then wait for toast (2s)
total_time = time.time() - start
print(f"✓ Got {coffee} and {toast}")
print(f"⏱️  Total time: {total_time:.1f} seconds")
print("   (Coffee: 3s + Toast: 2s = 5s total)")

# Example 2: Asynchronous (Non-blocking) Code
print("\n--- Example 2: ASYNCHRONOUS (Async Python) ---")


async def make_coffee_async():
    """Make coffee asynchronously"""
    print("  ☕ Starting to make coffee...")
    await asyncio.sleep(3)  # Non-blocking! Other tasks can run
    print("  ☕ Coffee ready!")
    return "Coffee"


async def make_toast_async():
    """Make toast asynchronously"""
    print("  🍞 Starting to make toast...")
    await asyncio.sleep(2)  # Non-blocking! Other tasks can run
    print("  🍞 Toast ready!")
    return "Toast"


async def make_breakfast():
    """Make breakfast with both tasks running concurrently"""
    print("\nAsynchronous execution:")
    start = time.time()

    # Run both tasks at the same time!
    coffee, toast = await asyncio.gather(
        make_coffee_async(),
        make_toast_async()
    )
    # await make_coffee_async()
    # await make_toast_async()

    total_time = time.time() - start
    print(f"✓ Got {coffee} and {toast}")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print("   (Coffee and Toast made simultaneously = 3s total!)")


# Run the async function
asyncio.run(make_breakfast())

print("\n--- Example 3: ASYNCHRONOUS To SYNCHRONOUS (Wrong) ---")

async def  async_to_sync():
    """Convert async function to sync for demonstration purposes"""
    start = time.time()
    coffee  = await make_coffee_async()
    toast = await make_toast_async()
    total_time = time.time() - start
    print(f"✓ Got {coffee} and {toast}")
    print(f"⏱️  Total time: {total_time:.1f} seconds")


asyncio.run(async_to_sync())
