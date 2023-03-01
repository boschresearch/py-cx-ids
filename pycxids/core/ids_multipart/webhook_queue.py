# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

import queue
import threading


messages = {}
messages_lock = threading.Condition()

def messages_contains(key:str) -> bool:
    return key in messages

def add_message(key: str, header, payload):
    """
    This adds a message to the list with the given key.
    Every message basically is a header AND a payload.
    """
    with messages_lock:
        messages[key] = header, payload
        messages_lock.notify()


def wait_for_message(key:str) -> tuple:
    """
    Wait for a message with the ID / key.
    The message typcially arrives via the webhook.
    Messages are always tuples. Typically header, payload
    The message is also deleted from the list
    """
    with messages_lock:
        messages_lock.wait_for(lambda: messages_contains(key))
        header, payload = messages.get(key)
        del messages[key]
        return header, payload
