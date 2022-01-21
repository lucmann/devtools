#!/usr/bin/env python3
# Copyright (C) 2022 Luc Ma <onion0709@gmail.com>

import subprocess

from subprocess import (
    Popen,
    PIPE,
)

class Deployable:
    def __init__(self,
                 tool,                  # type: DevTool
                 dl_cmd=[],             # type: List[str]
                 unpack_cmd=[],         # type: List[str]
                 build_cmd=[],          # type: List[str]
                 inst_cmd=[],           # type: List[str]
                 cfg_cmd=[]             # type: List[str]
                 ):
        self.tool = tool,
        self.dl_cmd = dl_cmd,
        self.unpack_cmd = unpack_cmd;
        self.build_cmd = build_cmd;
        self.inst_cmd = inst_cmd;
        self.cfg_cmd = cfg_cmd;

class DevTool:
    def __init__(self, dest_dir, src_url=None):
        self.dest_dir = dest_dir
        self.src_url = src_url

    def clean(self):
        pass

class SourceDevTool(DevTool):
    def __init__(self, src_url, unpack_dir, dest_dir):
        DevTool.__init__(self, dest_dir, src_url)
        self.unpack_dir = unpack_dir
