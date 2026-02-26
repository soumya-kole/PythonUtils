import asyncio

async def fetch_data_async(i):
    print(f"Fetching {i}")
    await asyncio.sleep(2)
    print(f"Done {i}")

# async def main():
#     task = asyncio.create_task(fetch_data_async("a"))
#     await task  # Wait for the task to complete

async def main():
    tasks = [fetch_data_async(i) for i in ['a']]
    await asyncio.gather(*tasks)

asyncio.run(main())
