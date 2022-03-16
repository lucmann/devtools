#!/usr/bin/env python3
# Copyright (C) 2022 Luc Ma <onion0709@gmail.com>

import argparse
import inspect
import os
import re
import shutil
import stat
import subprocess
import sys

from subprocess import (
    Popen,
    PIPE,
)


if os.geteuid() == 0:
    WHOAMI = os.getenv("SUDO_USER")
else:
    WHOAMI = os.getenv("USER")

HOME = os.path.join("/home", WHOAMI)


class bcolors:
    ENDC        = '\033[0m'
    BOLD        = '\033[1m'
    GREY        = '\033[90m'
    RED         = '\033[91m'
    GREEN       = '\033[92m'
    YELLOW      = '\033[93m'
    BLUE        = '\033[94m'
    PINK        = '\033[95m'
    TURQUOISE   = '\033[96m'

    OK          = GREEN
    WARNING     = YELLOW
    FAIL        = RED

def pr_warning(s):
    print(f"{bcolors.WARNING}{s}{bcolors.ENDC}")

def pr_failure(s):
    print(f"{bcolors.FAIL}{s}{bcolors.ENDC}")

def pr_okay(s):
    print(f"{bcolors.OK}{bcolors.BOLD}{s}{bcolors.ENDC}")


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

        parser.add_argument('dtools', metavar='TOOL', type=str, nargs='*',
                            help="tools will be installed")
        parser.add_argument('-u', '--uninst', dest='uninst',
                            action='store_true', default=False,
                            help="uninstall the tools you specified")
        parser.add_argument('-l', '--list', dest='whatprovided',
                            action='store_true', default=False,
                            help="list all of tools you can deploy by this way")

        return parser.parse_args()

    @staticmethod
    def list_all(dt_list):
        pr_okay(f"You could install the following dev tools by this way so far")
        print("\n")
        for dt in dt_list:
            pr_okay(f"\t{dt.dtd.cmd}")
        print("\n")

    @staticmethod
    def git_shallow_clone(dtd):
        try:
            if len(dtd.branch) == 0:
                proc = Popen(['git', 'clone', '--depth', '1', dtd.url,
                              dtd.prefix])
            else:
                proc = Popen(['git', 'clone', '--depth', '1', '--branch',
                              dtd.branch, dtd.url, dtd.prefix])

            (stdout, stderr) = proc.communicate()

            if proc.returncode == 0:
                return True
            else:
                pr_failure(f"Failed to git clone {dtd.url}")
                return False
        except:
            pr_failure(f"Failed to git clone {dtd.url}")
            return False


class DevToolDescriptor:
    """
    Describe the basic information of a dev tool
    """

    def __init__(self,
                 pkgname,
                 cmd,
                 version,
                 min_version='',
                 url=None,
                 branch='',
                 prefix=None,
                 platform='linux'):
        self.pkgname = pkgname              # deb file name or git repo name
        self.cmd = cmd                      # executable name as well as args
                                            # being passed into this script
        self.version = version
        self.min_version = min_version
        self.curr_version = ""
        self.url = url
        self.branch = branch                # Optional, source git branch
        self.prefix = prefix
        self.platform = platform            # 'linux' or 'win32'


class DevToolDeploy:
    """
    A set of abstract operations needed to deploy a dev tool
    """

    def __init__(self, dtd):
        self.dtd = dtd                  # type: DevToolDescriptor

    def deploy(self, uninst):
        if uninst:
            if self.exists():
                self.uninstall()
            else:
                pr_warning(f"{self.dtd.cmd} not installed yet")
        else:
            if self.exists():
                pr_okay(f"{self.dtd.cmd} {self.dtd.curr_version} has existed")
            else:
                if not self.download():
                    return

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
            proc = Popen([self.dtd.cmd, '--version'], stdout=PIPE,
                         stderr=PIPE, text=True)
            (stdout, stderr) = proc.communicate()

            try:
                command_not_found = re.search(r"command not found",
                                              stderr, re.IGNORECASE)
                if command_not_found is None:
                    self.dtd.curr_version = re.search(r"\d+\.\d+(\.\d+)?",
                                                      stdout).group(0)
                else:
                    return False
            except AttributeError:
                curr_ver_unknown = True

            # Do not care the version of program
            if len(self.dtd.min_version) == 0:
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
        return True

    def unpack(self):
        pass

    def build(self):
        pass

    def install(self):
        try:
            proc = Popen(['sudo', 'apt-get', 'install', '-y', self.dtd.pkgname])
            (stdout, stderr) = proc.communicate()
        except Exception:
            pr_failure(f"Failed to apt-get install {self.dtd.pkgname}")

    def configure(self):
        pass

    def clean(self):
        pass

    def uninstall(self):
        try:
            proc = Popen(['sudo', 'apt-get', 'purge', self.dtd.pkgname])
            (stdout, stderr) = proc.communicate()
        except Exception:
            pr_failure(f"Failed to apt-get purge {self.dtd.pkgname}")


class DTAck(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)

# the silver searcher ag
class DTAg(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTAutojump(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)

    def configure(self):
        oh_my_zsh_root = os.path.join(HOME, ".oh-my-zsh")
        zshrc = os.path.join(HOME, ".zshrc")

        # Nothing to do if oh-my-zsh not installed
        if not os.path.exists(oh_my_zsh_root):
            return

        test_j = Popen(['grep', '-E', '^plugins=(.*autojump.*)', zshrc],
                       stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = test_j.communicate()

        if test_j.returncode == 0:
            pr_okay(f"{self.dtd.cmd} has existed among zsh plugins")
            return

        try:
            add_zsh_plugin = Popen(['sed', '-i', 's/plugins=(/&autojump /', zshrc])
            (stdout, stderr) = add_zsh_plugin.communicate()

            if add_zsh_plugin_proc.returncode == 0:
                pr_okay(f"{zshrc} updated, please open a new terminal")
        except:
            pr_failure(f"Failed to add {self.dtd.cmd} to zsh plugins")


class DTCmake(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTCscope(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTCtags(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)
        self.conf = os.path.join(HOME, ".ctags")

    def configure(self):
        config = """
            --recurse=yes
            --exclude=.git
            --exclude=build
            --exclude=.idea
            --exclude=\*.swp
            --exclude=\*.bak
            --exclude=\*.pyc
        """

        try:
            with open(self.conf, 'w+') as f:
                f.write(inspect.cleandoc(config))

            shutil.chown(self.conf, WHOAMI, WHOAMI)
        except:
            pass


class DTFzf(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)

    def download(self):
        return DTUtils.git_shallow_clone(self.dtd)

    def install(self):
        fzf_installer = os.path.join(self.dtd.prefix, "install")

        try:
            inst_proc = Popen([fzf_installer], shell=True)
            (stdout, stderr) = inst_proc.communicate()
        except:
            pr_failure(f"Failed to install {self.dtd.cmd}")

    def uninstall(self):
        fzf_uninstaller = os.path.join(self.dtd.prefix, "uninstall")

        try:
            proc = Popen([fzf_uninstaller], shell=True)
            (stdout, stderr) = proc.communicate()
        except:
            pr_failure(f"Failed to exec {fzf_uninstaller}")
        finally:
            shutil.rmtree(self.dtd.prefix, ignore_errors=True)

    def configure(self):
        vimrc = os.path.join(HOME, ".vimrc")
        appended_line = "set runtimepath+=~/.fzf"

        try:
            with open(vimrc, 'r') as f:
                for line in f:
                    if appended_line in line:
                        return

            with open(vimrc, 'a+') as f:
                f.write(appended_line)
        except:
            pr_failure(f"Failed to install fzf.vim plugin")


class DTGcc(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTGpp(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTGdb(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTGit(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTMeson(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTPip3(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTTmux(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)


class DTZsh(DevToolDeploy):
    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)

    def configure(self):
        """
        Now that we have zsh installed, let's use it
        """

        curr_shell = subprocess.check_output(
            ['grep', '^' + WHOAMI, '/etc/passwd'], universal_newlines=True).strip()

        if curr_shell.endswith("/zsh"):
            # User's login shell has been zsh
            return

        try:
            first_zsh = subprocess.check_output(
                ['grep', '-m1', '/zsh', '/etc/shells'],
                universal_newlines=True).strip()

            proc = Popen(['usermod', '--shell', first_zsh, WHOAMI])
            (stdout, stderr) = proc.communicate()

            if proc.returncode == 0:
                pr_okay(f"{WHOAMI}'s login shell has changed to {first_zsh}\n" \
                      "You must log out from your user session and log back in " \
                      "to see this change")
        except Exception:
            pr_failure(f"Failed to change login shell for {WHOAMI}")


class DTOhMyZsh(DevToolDeploy):
    """
    Oh My Zsh for managing your zsh configuration
    """

    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)

    def exists(self):
        if os.path.exists(self.dtd.prefix):
            return True
        else:
            return False

    def download(self):
        return DTUtils.git_shallow_clone(self.dtd)

    def install(self):
        pass

    def configure(self):
        zshrc_template = os.path.join(self.dtd.prefix,
                                      'templates', 'zshrc.zsh-template')
        zshrc = os.path.join(HOME, '.zshrc')
        zshrc_bak = os.path.join(HOME, '.zshrc.orig')

        # Optionally backup your existing ~/.zshrc file
        if os.path.exists(zshrc):
            shutil.copyfile(zshrc, zshrc_bak)

        if os.path.exists(zshrc_template):
            shutil.copyfile(zshrc_template, zshrc)

    def uninstall(self):
        try:
            oh_my_zsh_root = os.environ["ZSH"]
            oh_my_zsh_uninst = os.path.join(oh_my_zsh_root,
                                            "tools", "uninstall.sh")
            os.chmod(oh_my_zsh_uninst, 0o764)

            yes_p = Popen(['yes'], stdout=PIPE)
            uninst_proc = Popen([oh_my_zsh_uninst], stdin=yes_p.stdout,
                                shell=True, universal_newlines=True)
            (stdout, stderr) = uninst_proc.communicate()
        except (KeyError, FileNotFoundError):
            # No oh-my-zsh to uninstall
            pass


class DTTpm(DevToolDeploy):
    """
    Tmux Plugin Manager
    """

    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)
        self.conf = os.path.join(HOME, ".tmux.conf")

    def exists(self):
        if os.path.exists(self.dtd.prefix):
            return True
        else:
            return False

    def download(self):
        return DTUtils.git_shallow_clone(self.dtd)

    def install(self):
        pass

    def configure(self):
        config = """
            set -g @plugin 'tmux-plugins/tpm'
            set -g @plugin 'tmux-plugins/tmux-sensible'
            set -g @plugin 'tmux-plugins/tmux-resurrect'

            run '~/.tmux/plugins/tpm/tpm'
        """

        try:
            with open(self.conf, 'a+') as f:
                f.write(inspect.cleandoc(config))
        except:
            pr_failure(f"No such file or directory {self.conf}")

    def uninstall(self):
        shutil.rmtree(self.dtd.prefix, ignore_errors=True)
        shutil.rmtree(os.path.join(HOME, ".tmux"), ignore_errors=True)
        os.remove(self.conf)


class DTVimrc(DevToolDeploy):
    """
    The ultimate Vim configuration
    """

    def __init__(self, dtd):
        DevToolDeploy.__init__(self, dtd)
        self.rc = os.path.join(HOME, ".vimrc")
        self.rc_bak = os.path.join(HOME, '.vimrc.orig')

    def exists(self):
        if os.path.exists(self.dtd.prefix):
            return True
        else:
            return False

    def download(self):
        return DTUtils.git_shallow_clone(self.dtd)

    def install(self):
        vimrc_installer = os.path.join(self.dtd.prefix,
                                       "install_awesome_vimrc.sh")

        # Optionally backup your existing ~/.vimrc file
        if os.path.exists(self.rc):
            shutil.copyfile(self.rc, self.rc_bak)

        try:
            inst_proc = Popen([vimrc_installer], shell=True)
            (stdout, stderr) = inst_proc.communicate()
        except:
            pr_failure(f"Failed to install {self.dtd.cmd}")

    def configure(self):
        pass

    def uninstall(self):
        shutil.rmtree(self.dtd.prefix, ignore_errors=True)

        if os.path.exists(self.rc_bak):
            shutil.move(self.rc_bak, self.rc)
        else:
            os.remove(self.rc)


def devtool_deploy(dt, uninst):
    dt.deploy(uninst)


if __name__ == "__main__":
    args = DTUtils.parseArgs()

    dt_list = [
        DTAck(DevToolDescriptor(
            "ack",
            "ack",
            ""
        )),

        DTAg(DevToolDescriptor(
            "silversearcher-ag",
            "ag",
            ""
        )),

        DTAutojump(DevToolDescriptor(
            "autojump",
            "autojump",
            ""
        )),

        DTCmake(DevToolDescriptor(
            "cmake",
            "cmake",
            ""
        )),

        DTCscope(DevToolDescriptor(
            "cscope",
            "cscope",
            ""
        )),

        DTCtags(DevToolDescriptor(
            "universal-ctags",
            "ctags",
            ""
        )),

        DTFzf(DevToolDescriptor(
            "fzf",
            "fzf",
            "",
            "",
            "git@github.com:junegunn/fzf.git",
            "",
            os.path.join(HOME, ".fzf")
        )),

        DTGcc(DevToolDescriptor(
            "gcc",
            "gcc",
            ""
        )),

        DTGpp(DevToolDescriptor(
            "g++",
            "g++",
            ""
        )),

        DTGdb(DevToolDescriptor(
            "gdb",
            "gdb",
            ""
        )),

        DTGit(DevToolDescriptor(
            "git",
            "git",
            ""
        )),

        DTMeson(DevToolDescriptor(
            "meson",
            "meson",
            ""
        )),

        # it is kind of weird to add pip to the list, but anyway
        # love python, love pip
        DTPip3(DevToolDescriptor(
            "python3-pip",
            "pip3",
            ""
        )),

        DTZsh(DevToolDescriptor(
            "zsh",
            "zsh",
            "",
            "5.0.8"
        )),

        DTOhMyZsh(DevToolDescriptor(
            "ohmyzsh",
            "ohmyzsh",
            "",
            "",
            "git@github.com:ohmyzsh/ohmyzsh.git",
            "",
            os.path.join(HOME, ".oh-my-zsh")
        )),

        DTTmux(DevToolDescriptor(
            "tmux",
            "tmux",
            ""
        )),

        DTTpm(DevToolDescriptor(
            "tpm",
            "tpm",
            "",
            "",
            "git@github.com:tmux-plugins/tpm.git",
            "",
            os.path.join(HOME, ".tmux", "plugins", "tpm")
        )),

        DTVimrc(DevToolDescriptor(
            "vimrc",
            "vimrc",
            "",
            "",
            "git@github.com:lucmann/vimrc.git",
            "cscope-maps",
            os.path.join(HOME, ".vim_runtime")
        )),
    ]

    if args.whatprovided:
        DTUtils.list_all(dt_list)

    for dt in dt_list:
        if dt.dtd.cmd in args.dtools:
            devtool_deploy(dt, args.uninst)
