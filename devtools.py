#!/usr/bin/env python3
# Copyright (C) 2022 Luc Ma <onion0709@gmail.com>

import subprocess
from abc import abstractmethod

from subprocess import (
    Popen,
    PIPE,
)

class DevToolDescriptor:
    """
    Describe the basic information of a dev tool
    """

    def __init__(self,
                 name,
                 cmd_name,
                 version,
                 min_version=None,
                 url=None,
                 prefix=None):
        self.name = name
        self.cmd_name = cmd_name
        self.version = version
        self.min_version = min_version
        self.url = url
        self.prefix = prefix

class DevToolDeploy:
    """
    A set of abstract operations needed to deploy a dev tool
    """

    def __init__(self, dtd, uninst=False):
        self.dtd = dtd                  # type: DevToolDescriptor
        self.uninst = uninst            # type: bool

    def deploy(self):
        if self.uninst:
            self.uninstall()
        else:
            if self.exists():
                pass
            else:
                self.download()
                self.unpack()
                self.build()
                self.install()
                self.configure()
                self.clean()

    """
    These operations have to be implemented in the subclasses.
    """

    @abstractmethod
    def install(self):
        pass

    @abstractmethod
    def uninstall(self):
        pass

    def exists(self):
        return False

    def download(self):
        """
        Implemented by SourceDevToolDeploy
        """

        print(f"Downloading ...")

    def unpack(self):
        """
        Implemented in the subclass SourceDevToolDeploy
        """

        pass

    def build(self):
        pass

    def configure(self):
        pass

    def clean(self):
        pass

class DTZsh(DevToolDeploy):
    def __init__(self, dtd, uninst=False):
        DevToolDeploy.__init__(self, dtd, uninst)


def devtool_deploy(dt):
    dt.deploy()

if __name__ == "__main__":
    devtool_deploy(DTZsh(
        DevToolDescriptor(
            "zsh",
            "zsh",
            "",
            "5.0.8"
        )
    ))
