# Copyright (c) 2023 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# https://github.com/boschresearch/py-cx-ids
#
# SPDX-License-Identifier: Apache-2.0

PRINT_COLOR_RED = '\033[91m'
PRINT_COLOR_END = '\033[0m'


def print_red(text: str):
    print(f"{PRINT_COLOR_RED}{text}{PRINT_COLOR_END}")
