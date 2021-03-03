#!/usr/bin/env python3

import sys


def abort(msg: str) -> None:
    sys.stdout.flush()
    sys.stderr.write(f"FATAL: {msg}\n")
    sys.exit(1)


def warn(msg: str) -> None:
    sys.stdout.flush()
    sys.stderr.write(f"WARNING: {msg}\n")
