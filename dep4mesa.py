#!/usr/bin/env python3
#
# Copyright (C) 2022 Luc Ma <onion0709@gmail.com>

import apt
import sys

depends = [
    "bison",
    "expat",
    "flex",
    "libx11-dev",
    "libxcb-randr0-dev",
    "libxext-dev",
    "libxrandr-dev",
    "pkgconf",
    "zlib1g",
]

ac = apt.cache.Cache()
ac.update()
ac.open()

pkgs = [ac[x] for x in depends]

for pkg in pkgs:
    if pkg.is_installed:
        print(f"{pkg.name} already installed")
    else:
        pkg.mark_install()

try:
    ac.commit()
except Exception as e:
    print(f"{str(e)} failed to install", file=sys.stderr)

