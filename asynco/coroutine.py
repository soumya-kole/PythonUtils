import asyncio
import time


async def countdown(name, number):
    print(f"{name} starting countdown from {number}")
    while number > 0:
        print(f"{name}: {number}")
        await asyncio.sleep(1)  # Simulate work
        number -= 1
    print(f"{name} done!")

async def main():
    # Create multiple countdown tasks
    # tasks = [
    #     asyncio.create_task(countdown("Task A", 5)),
    #     asyncio.create_task(countdown("Task B", 6)),
    # ]
    # tasks = [countdown("Task A", 5), countdown("Task B", 6)]
    await countdown("Task A", 5)
    await countdown("Task B", 6)
    await asyncio.sleep(2)  # Let tasks run for a bit before waiting
    print("Main is done with sleeping.")
    # Wait for all tasks to complete
    # await asyncio.gather(*tasks)

if __name__ == "__main__":
    #measure total execution time
    start = time.time()
    asyncio.run(main())
    total_time = time.time() - start
    print(f"Total execution time: {total_time:.1f} seconds")