#!/usr/bin/env python3
"""Launcher for SteamOS ISO Mount Tool – Created by Dominic Lesina x Claude."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from isomounttool.__main__ import main  # noqa: E402

sys.exit(main())
