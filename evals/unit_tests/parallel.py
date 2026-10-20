from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context


def run_in_parallel[T](runs: int, task: Callable[[], T]) -> list[T]:
    """Run `task` `runs` times at once. The model calls are independent, so a
    test waits for the slowest call instead of the sum of all of them. Each call
    runs in a copy of the current context, so it stays inside the test's
    Langfuse trace and prompt cache session."""
    with ThreadPoolExecutor(max_workers=runs) as executor:
        futures = [executor.submit(copy_context().run, task) for _ in range(runs)]
        return [future.result() for future in futures]
