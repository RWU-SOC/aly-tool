#!/usr/bin/env python3
# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Entry point when running python -m aly"""

import sys
from pathlib import Path

# Allow running from source tree
if __name__ == "__main__":
    src_dir = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(src_dir))

from aly.app.main import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
