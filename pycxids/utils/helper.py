# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

PRINT_COLOR_RED = '\033[91m'
PRINT_COLOR_END = '\033[0m'


def print_red(text: str):
    print(f"{PRINT_COLOR_RED}{text}{PRINT_COLOR_END}")

def dict_diff(dict1: dict, dict2: dict) -> dict:
    """
    Compare 2 dict and return delta
    """
    set1 = dict1.items()
    set2 = dict2.items()
    dict_diff = set1 ^ set2
    return dict(dict_diff)
