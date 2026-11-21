#!/usr/bin/env python3
"""news-image-20261121-v3 entrypoint.

Copies the finished broadsheet (entry.png, drawn from scratch by draw.py
from the verified 21 Nov 2026 news brief) to the output directory.
Deterministic: the same bytes every run, no network, stdlib only.
"""
import os
import shutil


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    shutil.copyfile(os.path.join(here, "entry.png"),
                    os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
