import configparser
import os
import subprocess
import sys

import colorama
from termcolor import colored

DEFAULT_COMPARISON_URL = 'http://mnsopenl:9999/web/public/compare/xls'
GIT_OPENL_VERSION = 1.0

FILE_EXTENSIONS = ['xls', 'xlsx']
GIT_ATTRIBUTES_DIFFER = ['*.' + file_ext + ' diff=openl' for file_ext in FILE_EXTENSIONS]
OPENL_GIT_SETTINGS_FILE = 'git-openl.config'


def executable_name():
    if os.name == 'nt':
        return 'git-openl-diff.exe'
    if os.name == 'posix':
        return 'git-openl-diff'


def git_info_folder(local_config_dir):
    path_info = os.path.join(local_config_dir, 'info')
    if not os.path.exists(path_info):
        os.makedirs(path_info)
    return path_info


class Installer():
    def __init__(self, mode='global', path=None):

        # running as bundle (aka frozen)
        if is_frozen():
            self.GIT_OPENL_DIFF = executable_name()
        else:
            executable_path = sys.executable.replace('\\', '/')
            differ_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diff.py').replace('\\', '/')
            self.GIT_OPENL_DIFF = f'{executable_path} {differ_path}'

        if mode == 'global' and path:
            raise ValueError('must not specify repository path when installing globally')

        if mode == 'local' and not path:
            raise ValueError('must specify repository path when installing locally')

        if mode == 'local' and not is_git_repository(path):
            raise ValueError('not a Git repository')

        self.mode = mode
        self.path = path

        # global config dir (only set when running in `global` mode)
        self.git_global_config_dir = self.get_global_gitconfig_dir() if self.mode == 'global' else None
        # local config dir (only set when running in `local` mode)
        self.git_local_config_dir = self.get_local_gitconfig_dir() if self.mode == 'local' else None

        # path to gitattributes folder
        self.git_attributes_path = self.get_git_attributes_path()
        # path to git-openl settings file folder
        self.openl_settings_path = self.get_openl_settings_path()

    def install(self):
        try:
            # 1. gitconfig: set-up diff.openl.command
            self.execute(['diff.openl.command', self.GIT_OPENL_DIFF])

            # 2. set-up openl-git settings file
            self.create_openl_git_settings()

            # 3. set-up gitattributes (define custom differ and merger)
            self.update_git_file(path=self.git_attributes_path, keys=GIT_ATTRIBUTES_DIFFER, operation='SET')

            # 4. update gitconfig (only relevent when running in `global` mode)
            if self.mode == 'global':
                # set core.attributesfile
                self.execute(['core.attributesfile', self.git_attributes_path])

            print(colored('Installation has been successfully completed', color='green'))
        except Exception as e:
            print(colored('Something went wrong, reason:', color='red'))
            print(e)

    def uninstall(self):
        try:
            # 1. gitconfig: remove diff.openl.command from gitconfig
            keys = self.execute(['--list']).split('\n')
            if [key for key in keys if key.startswith('diff.openl.command')]:
                self.execute(['--remove-section', 'diff.openl'])
            # 2. delete openl-git settings
            self.delete_openl_git_settings()

            # 3. gitattributes: remove keys
            gitattributes_keys = self.update_git_file(path=self.git_attributes_path, keys=GIT_ATTRIBUTES_DIFFER,
                                                      operation='REMOVE')
            # when in global mode and gitattributes is empty, update gitconfig and delete gitattributes
            if not gitattributes_keys:
                if self.mode == 'global':
                    self.execute(['--unset', 'core.attributesfile'])
                self.delete_git_file(self.git_attributes_path)
            print(colored(f"git-openl extension was successfully removed {self.mode}ly", color='green'))
        except Exception as e:
            print(colored("Something went wrong, reason:", color='red'))
            print(e)

    def execute(self, args):
        command = ['git', 'config']
        if self.mode == 'global':
            command.append('--global')
        command += args
        return subprocess.run(command, cwd=self.path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True).stdout

    def get_global_gitconfig_dir(self):
        # put .gitattributes in same folder as global .gitconfig
        # determine .gitconfig path
        # this requires Git 2.8+ (March 2016)
        t = self.execute(['--list', '--show-origin'])
        if not t:
            self.execute(['diff.openl.command', 'template'])
            f = self.execute(['--list', '--show-origin'])
        else:
            f = t

        p = self.execute(['--list'])
        f = f.split('\n')[0]
        p = p.split('\n')[0]

        return f[:f.index(p)][5:][:-11]

    def get_local_gitconfig_dir(self):
        local_repo_command = \
            subprocess.Popen(['git', 'rev-parse', '--show-toplevel'], cwd=self.path,
                             stdout=subprocess.PIPE).communicate()[
                0].rstrip().decode('utf-8')
        return os.path.join(local_repo_command, '.git')

    def get_git_attributes_path(self):
        # search for gitattributes file in default location, if path doesn't exist - make it
        if self.mode == 'local':
            info_path = git_info_folder(self.git_local_config_dir)
            return os.path.join(info_path, 'attributes')

        # check if core.attributesfile is configured
        core_attributesfile = self.execute(['--get', 'core.attributesfile']).split('\n')[0]
        if core_attributesfile:
            return os.path.expanduser(core_attributesfile)

        # put .gitattributes into same directory as global .gitconfig
        return os.path.join(self.git_global_config_dir, '.gitattributes')

    def get_openl_settings_path(self):
        p = None
        if self.mode == 'global':
            p = self.git_global_config_dir
        if self.mode == 'local':
            p = self.git_local_config_dir
        return os.path.join(p, OPENL_GIT_SETTINGS_FILE)

    def update_git_file(self, path, keys, operation):
        assert operation in ('SET', 'REMOVE')
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = [line for line in f.read().split('\n') if line]
        else:
            content = []

        if operation == 'SET':
            # create union set: keys + existing content
            content = sorted(list(set(content).union(set(keys))))
        else:
            # remove keys from content
            content = [line for line in content if line and line not in keys]

        if content:
            with open(path, 'w') as f:
                f.writelines('\n'.join(content))

        return content

    def delete_git_file(self, path):
        if os.path.exists(path):
            os.remove(path)

    def create_openl_git_settings(self):
        if os.path.exists(self.openl_settings_path):
            return
        config = configparser.ConfigParser()
        url_config = DEFAULT_COMPARISON_URL
        if os.name == 'nt':
            url_config = ''
        config['DEFAULT'] = {
            'comparison_url': url_config
        }
        with open(self.openl_settings_path, 'w') as f:
            config.write(f)

    def delete_openl_git_settings(self):
        if os.path.exists(self.openl_settings_path):
            os.remove(self.openl_settings_path)


HELP_GENERIC = f"""Version: {GIT_OPENL_VERSION}
git openl <command> [<args>]\n
Git Openl is a system for managing Excel workbook files in
association with a Git repository. Git Openl:
* installs a special git-diff for Excel workbook files\n
Commands
--------\n
* git openl install:
    Install Git Openl globally.
* git openl install --local:
    Install Git Openl locally.
* git openl uninstall:
    Uninstall Git Openl.
* git openl uninstall --local:
    Uninstall Git Openl locally."""


class CommandParser:

    def __init__(self, args):
        self.args = args

    def help(self, *args):
        print(HELP_GENERIC)

    def install(self, *args):
        if not args or args[0] == '--global':
            installer = Installer(mode='global')
        elif args[0] == '--local':
            installer = Installer(mode='local', path=os.getcwd())
        else:
            return print(
                f"""Invalid option "{args[0]}" for "git-openl install"\nRun 'git-openl --help' for usage.""")
        installer.install()

    def uninstall(self, *args):
        if args:
            if args[0] == '--local':
                installer = Installer(mode='local', path=os.getcwd())
            else:
                return print(
                    f"""Invalid option "{args[0]}" for "git-openl install"\nRun 'git-openl --help' for usage.""")
        else:
            installer = Installer(mode='global')
        installer.uninstall()

    def execute(self):
        if not self.args:
            return self.help()
        command = self.args[0].replace('-', '_')
        if command == '__help':
            command = 'help'

        if not self.args:
            return self.help()

        args = self.args[1:]

        # do not process if command does not exist
        if not hasattr(self, command):
            return print(
                f"""Error: unknown command "{command}" for "git-openl"\nRun 'git-openl --help' for usage.""")

        # execute command
        getattr(self, command)(*args)


def is_git_repository(path):
    cmd = subprocess.run(['git', 'rev-parse'], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    if not cmd.stderr.split('\n')[0]:
        return True
    return False


def is_frozen():
    return getattr(sys, 'frozen', False)


if __name__ == '__main__':
    colorama.init()
    command_parser = CommandParser(sys.argv[1:])
    command_parser.execute()
