#!/usr/bin/env python3
"""Compatibility launcher. Prefer: python -m stillpoint.cli"""
from stillpoint.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
