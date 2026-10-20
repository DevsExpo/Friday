# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.


import os
import random
import string
import asyncio
import multiprocessing
import time
from functools import wraps
from concurrent.futures.thread import ThreadPoolExecutor


_max_workers = min(16, (multiprocessing.cpu_count() or 1) * 2 + 2)
executor = ThreadPoolExecutor(max_workers=_max_workers, thread_name_prefix="friday_file_worker")


def run_in_exc(func_):
    @wraps(func_)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(executor, lambda: func_(*args, **kwargs))

    return wrapper


@run_in_exc
def make_file_from_text(input_: str, file_name=None, file_suffix=".txt"):
    letters = string.ascii_lowercase
    file_name = file_name or "".join(random.choice(letters) for _ in range(5)) + file_suffix

    if os.path.exists(file_name):
        os.remove(file_name)
    open(file_name, "w", encoding="utf-8").write(input_)
    return file_name


@run_in_exc
def rename_file(file_name, new_file_name):
    if not os.path.exists(file_name):
        return False
    os.rename(file_name, new_file_name)
    if not os.path.exists(new_file_name):
        return False
    return True


@run_in_exc
def make_folder(folder_name=None):
    letters = string.ascii_letters
    folder_name = folder_name or "".join(random.choice(letters) for _ in range(5))
    if os.path.exists(folder_name):
        os.remove(folder_name)
    os.makedirs(folder_name)
    return os.path.exists(folder_name)


def purge_stale_files(
    directories: list[str] | None = None,
    max_age_seconds: int = 3600,
    exclude: set[str] | None = None,
) -> int:
    """
    Safely purges temporary and cached files older than max_age_seconds.
    Explicitly protects user assets like 'thumb.jpg'.
    """
    if directories is None:
        directories = ["./temp", "./cache"]
    if exclude is None:
        exclude = {"thumb.jpg", ".gitkeep"}

    now = time.time()
    deleted_count = 0

    for d in directories:
        dir_path = os.path.abspath(d)
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            continue
        try:
            for root, _, files in os.walk(dir_path):
                for f in files:
                    if f in exclude:
                        continue
                    full_path = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(full_path)
                        if now - mtime > max_age_seconds:
                            os.remove(full_path)
                            deleted_count += 1
                    except Exception:
                        pass
        except Exception:
            pass

    return deleted_count

