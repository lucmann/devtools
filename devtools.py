#!/usr/bin/env python3
# Copyright (C) 2022 Luc Ma <onion0709@gmail.com>

import argparse
import os
import re
import subprocess
import sys
from abc import abstractmethod

from subprocess import (
    Popen,
    PIPE,
)


class bcolors:
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    OK = '\033[90m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'

def pr_warning(s):
    print(f"{bcolors.WARNING}{s}{bcolors.ENDC}")

def pr_failure(s):
    print(f"{bcolors.FAIL}{s}{bcolors.ENDC}")

def pr_okay(s):
    print(f"{bcolors.OK}{s}{bcolors.ENDC}")


class DTUtils:
    """
    Set of utility functions
    """

    @staticmethod
    def version_lt(v1, v2):
        vt1 = tuple(map(int, (v1.split("."))))
        vt2 = tuple(map(int, (v2.split("."))))
        return vt1 < vt2

    @staticmethod
    def parseArgs():
        parser = argparse.ArgumentParser(description="DevTools deployment")

        parser.add_argument('-u', '--uninst', dest='uninst',
                            action='store_true', default=False)

        return parser.parse_args()


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
        self.curr_version = ""
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
                print(f"{self.dtd.name} {self.dtd.curr_version}")
            else:
                self.download()
                self.unpack()
                self.build()
                self.install()
                self.clean()

            # Note that configuration of a tool may not depend on
            # its existence. It is possible that a tool has been
            # installed but not configured at all
            self.configure()

    """
    These operations can be overrided in the subclass
    """

    def exists(self):
        try:
            # It should work for most of programs on Linux
            proc = Popen([self.dtd.cmd_name, '--version'], stdout=PIPE,
                         stderr=PIPE, text=True)
            (stdout, stderr) = proc.communicate()

            # Do not care the version of program
            if self.dtd.min_version is None:
                return True

            if proc.returncode != 0:
                # It proves the program has existed but probably does not
                # support the option `--version`.
                # A minimum version is required but the current version is
                # unresolved. In the circumstances, we are inclined to
                # reinstall
                return False
            else:
                self.dtd.curr_version = re.search(r"\d+\.\d+(\.\d+)?",
                                                  stdout).group(0)

                if DTUtils.version_lt(self.dtd.curr_version,
                                      self.dtd.min_version):
                    return False
                else:
                    return True
        except FileNotFoundError as e:
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

    def install(self):
        try:
            proc = Popen(['apt-get', 'install', '-y', self.dtd.name])
            (stdout, stderr) = proc.communicate()
        except Exception:
            pr_failure(f"Failed to apt-get install {self.dtd.name}")

    def configure(self):
        pass

    def clean(self):
        pass

    def uninstall(self):
        try:
            proc = Popen(['apt-get', 'purge', self.dtd.name])
            (stdout, stderr) = proc.communicate()
        except Exception:
            pr_failure(f"Failed to apt-get purge {self.dtd.name}")


class DTZsh(DevToolDeploy):
    def __init__(self, dtd, uninst=False):
        DevToolDeploy.__init__(self, dtd, uninst)

    def configure(self):
        """
        Now that we have zsh installed, let's use it
        """

        whoami = os.getlogin()

        try:
            first_zsh = subprocess.check_output(
                ['grep', '-m1', '/zsh', '/etc/shells'],
                universal_newlines=True).strip()

            proc = Popen(['usermod', '--shell', first_zsh, whoami])
            (stdout, stderr) = proc.communicate()

            if proc.returncode == 0:
                pr_okay(f"{whoami}'s login shell has changed to {first_zsh}\n" \
                      "You must log out from your user session and log back in " \
                      "to see this change")
        except Exception:
            pr_failure(f"Failed to change login shell for {whoami}")


def devtool_deploy(dt):
    dt.deploy()


if __name__ == "__main__":
    if os.getuid() != 0:
        pr_failure(f"You need to be root to run this application")
        sys.exit(1)

    args = DTUtils.parseArgs()

    devtool_deploy(DTZsh(
        DevToolDescriptor(
            "zsh",
            "zsh",
            "",
            "5.0.8"
        )
        , args.uninst
    ))
