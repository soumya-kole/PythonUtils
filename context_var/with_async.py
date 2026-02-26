import asyncio
import itertools
import random
from contextvars import ContextVar
from rich import print


# ==========================================
# Context Variables
# ==========================================

request_id: ContextVar[int] = ContextVar("request_id")
current_user: ContextVar[str] = ContextVar("current_user")
current_color: ContextVar[str] = ContextVar("current_color")

# Global incremental counter (safe in asyncio single-threaded loop)
request_counter = itertools.count(1)


def next_request_id() -> int:
    return next(request_counter)


# ==========================================
# Logger
# ==========================================

def log(message: str):
    rid = request_id.get("NO-REQ")
    user = current_user.get("anonymous")
    color = current_color.get("white")
    print(f"[{color}]\\[req-{rid}] \\[user={user}] {message} [/{color}]")


# ==========================================
# Simulated External Systems
# ==========================================

async def fetch_user_orders():
    log("Fetching user orders from DB...")
    await asyncio.sleep(random.uniform(1, 3))  # Simulate variable DB latency
    log("Orders fetched.")


async def call_payment_service():
    log("Calling payment provider...")
    await asyncio.sleep(random.uniform(2, 4))  # Simulate variable network latency
    log("Payment confirmed.")


# ==========================================
# Background Task
# ==========================================

async def send_email_notification():
    await asyncio.sleep(random.uniform(0.5, 1.5))  # Simulate email sending time
    log("Email notification sent.")

async def send_sms_notification():
    await asyncio.sleep(random.uniform(0.5, 1.5))  # Simulate SMS sending time
    log("SMS notification sent.")

# ==========================================
# Request Handler (Structured Concurrency)
# ==========================================

async def handle_request(user: str, color: str):
    rid_token = request_id.set(next_request_id())
    user_token = current_user.set(user)
    color_token = current_color.set(color)

    try:
        log("Request received.")

        await fetch_user_orders()
        await call_payment_service()
        # Send notifications concurrently using taskgroup
        async with asyncio.TaskGroup() as tg:
            tg.create_task(send_email_notification())
            tg.create_task(send_sms_notification())

        log("Request finished successfully.")

    finally:
        request_id.reset(rid_token)
        current_user.reset(user_token)
        current_color.reset(color_token)


# ==========================================
# Main Entrypoint
# ==========================================

async def main():
    colors = ["red", "green", "blue", "yellow"]
    users = ["alice", "bob", "carol", "dave"]

    async with asyncio.TaskGroup() as tg:
        for user, color in list(zip(users, colors)):
            tg.create_task(handle_request(user, color))


if __name__ == "__main__":
    asyncio.run(main())