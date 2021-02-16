#!/usr/bin/env python3

import sys


def abort(msg: str) -> None:
    sys.stdout.flush()
    sys.stderr.write(f"Fatal: {msg}\n")
    sys.exit(1)
