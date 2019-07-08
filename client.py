import aiohttp
import argparse
import asyncio
import multiprocessing as mp


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def make_requests(path: str, n: int) -> None:
    class Result:
        def __init__(self):
            self.n_successes = 0
            self.n_done = 0

    result = Result()

    def on_done(t):
        try:
            t.result()
        except (asyncio.CancelledError, aiohttp.ClientError):
            pass
        else:
            result.n_successes += 1
        finally:
            result.n_done += 1
            success_ratio = result.n_successes / result.n_done
            print(
                f'\r{result.n_done} / {n} ({success_ratio * 100:.0f}% ok)',
                end=''
            )

    async with aiohttp.ClientSession() as session:
        tasks = []
        print('Preparing requests')
        for _ in range(n):
            task = asyncio.create_task(
                fetch(session, path)
            )
            task.add_done_callback(on_done)
            tasks.append(task)

        print('Running requests.')
        for task in tasks:
            await asyncio.wait_for(task, 60)


def run(path: str, n: int):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(make_requests(path, n))
    print('\nDone!')


def run_in_parallel(path: str, n: int, j: int):
    assert j > 1

    n_per = int(n / j)
    processes = []
    for _ in range(j - 1):
        processes.append(mp.Process(target=run, args=(path, n_per)))

    for p in processes:
        p.start()

    run(path, n_per)

    print('\n Waiting for other processes.')
    for p in processes:
        p.join()

    print('Done!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--number', '-n', type=int, default=10000)
    parser.add_argument('--processes', '-j', type=int, default=1)
    parser.add_argument('--path', '-p', default='http://localhost:1234/hi')
    user_args = parser.parse_args()

    if user_args.processes == 1:
        run(user_args.path, user_args.number)
    else:
        run_in_parallel(user_args.path, user_args.number, user_args.processes)
