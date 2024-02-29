import asyncio
import time


async def say_after(timeout, text):
    await asyncio.sleep(timeout)
    print(text)
    return text


def callback(task):
    print("Callback", task.result())


async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(say_after(1, "hello"))

        task2 = tg.create_task(say_after(3, "world"))

        print(f"started at {time.strftime('%X')}")
        timeout = 2
        await asyncio.sleep(timeout)
        task1.add_done_callback(callback)

        print(f"After {timeout} sec timeout: {task1.done()}, {task2.done()}")
    print(f"Both tasks have completed now: {task1.result()}, {task2.result()}")

    # The await is implicit when the context manager exits.

    print(f"finished at {time.strftime('%X')}")


if __name__ == "__main__":
    asyncio.run(main())
