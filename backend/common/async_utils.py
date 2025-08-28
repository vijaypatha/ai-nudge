# FILE: backend/common/async_utils.py
# --- NEW FILE ---

import asyncio

def run_async_in_new_loop(coro):
    """
    Runs an async coroutine in a new event loop.
    This is a utility to safely call async functions from synchronous code,
    such as within a Celery task, preventing "Event loop is closed" errors.
    """
    try:
        # Check if an event loop is already running in the current thread
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = None

    if loop and loop.is_running():
        # If a loop is running, we can't create a new one.
        # We must schedule the coroutine to run on the existing loop.
        # This is a common pattern when interfacing with async libraries from sync code.
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    else:
        # If no loop is running, we can safely create and run one.
        return asyncio.run(coro)