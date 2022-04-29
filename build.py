#!/usr/bin/env python3

import PyInstaller.__main__

MAIN = "cpyleste.py"

options = [
    MAIN,
    "-n=cpyleste",
    "-y",
    "--clean",
    "--windowed",
    "--onefile",
    "-i=hagia_data/celeste.png"
]

PyInstaller.__main__.run(options)
