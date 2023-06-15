# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

from asyncio import Task

background_tasks = set()

def fire_and_forget(task:Task):
    """
    Little helper to keep a reference to the given task and remove after finished.

    This allows to easily "fire and forget" without the task being stopped somewhere in between.

    Further details:     https://docs.python.org/3/library/asyncio-task.html#creating-tasks
    """
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard(task))
