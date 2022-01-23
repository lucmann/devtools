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

    def __init__(self, dtd):
        self.dtd = dtd                  # type: DevToolDescriptor

    def deploy(self, uninst):
        if uninst:
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
        curr_ver_unknown = False
        try:
            # It should work for most of programs on Linux
            proc = Popen([self.dtd.cmd_name, '--version'], stdout=PIPE,
                         stderr=PIPE, text=True)
            (stdout, stderr) = proc.communicate()

            try:
                self.dtd.curr_version = re.search(r"\d+\.\d+(\.\d+)?",
                                                  stdout).group(0)
            except AttributeError:
                curr_ver_unknown = True

            # Do not care the version of program
            if self.dtd.min_version is None:
                return True

            if proc.returncode != 0 or curr_ver_unknown:
                # It proves the program has existed but probably does not
                # support the option `--version`.
                # A minimum version is required but the current version is
                # unresolved. In the circumstances, we are inclined to
                # reinstall
                return False
            else:
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


class DTGit(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTZsh(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)

    def configure(self):
        """
        Now that we have zsh installed, let's use it
        """

        whoami = os.getlogin()
        curr_shell = subprocess.check_output(
            ['grep', '^' + whoami, '/etc/passwd'], universal_newlines=True).strip()

        if curr_shell.endswith("/zsh"):
            # User's login shell has been zsh
            return

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


class DTOmz(DevToolDeploy):
    """
    Oh My Zsh for managing your zsh configuration
    """

    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)

    def download(self):
        try:
            pass
        except:
            pass


def devtool_deploy(dt, uninst):
    dt.deploy(uninst)


if __name__ == "__main__":
    if os.getuid() != 0:
        pr_failure(f"You need to be root to run this application")
        sys.exit(1)

    args = DTUtils.parseArgs()

    dt_list = [
        DTGit(DevToolDescriptor(
            "git",
            "git",
            ""
        )),

        DTZsh(DevToolDescriptor(
            "zsh",
            "zsh",
            "",
            "5.0.8"
        )),
    ]

    for dt in dt_list:
        devtool_deploy(dt, args.uninst);
