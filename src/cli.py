import os
import subprocess
import sys

FILE_EXTENSIONS = ['xls', 'xlsx']
GIT_ATTRIBUTES_DIFFER = ['*.' + file_ext + ' diff=openl' for file_ext in FILE_EXTENSIONS]
GIT_IGNORE = ['~$*.' + file_ext for file_ext in FILE_EXTENSIONS]


class Installer():
    def __init__(self, mode='global', path=None):

        # running as bundle (aka frozen)
        if is_frozen():
            self.GIT_OPENL_DIFF = 'git-openl-diff.exe'
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

        # paths to .gitattributes and .gitignore
        self.git_attributes_path = self.get_git_attributes_path()
        self.git_ignore_path = self.get_git_ignore_path()

    def install(self):
        # 1. gitconfig: set-up diff.xl.command
        self.execute(['diff.openl.command', self.GIT_OPENL_DIFF])

        # 2. set-up gitattributes (define custom differ and merger)
        self.update_git_file(path=self.git_attributes_path, keys=GIT_ATTRIBUTES_DIFFER, operation='SET')

        # 3. set-up gitignore (define differ for Excel file formats)
        self.update_git_file(path=self.git_ignore_path, keys=GIT_IGNORE, operation='SET')

        # 4. update gitconfig (only relevent when running in `global` mode)
        if self.mode == 'global':
            # set core.attributesfile
            self.execute(['core.attributesfile', self.git_attributes_path])
            # set core.excludesfile
            self.execute(['core.excludesfile', self.git_ignore_path])

    def uninstall(self):
        # 1. gitconfig: remove diff.openl.command from gitconfig
        keys = self.execute(['--list']).split('\n')
        if [key for key in keys if key.startswith('diff.openl.command')]:
            self.execute(['--remove-section', 'diff.openl'])

        # 2. gitattributes: remove keys
        gitattributes_keys = self.update_git_file(path=self.git_attributes_path, keys=GIT_ATTRIBUTES_DIFFER,
                                                  operation='REMOVE')
        # when in global mode and gitattributes is empty, update gitconfig and delete gitattributes
        if not gitattributes_keys:
            if self.mode == 'global':
                self.execute(['--unset', 'core.attributesfile'])
            self.delete_git_file(self.git_attributes_path)

        # 3. gitignore: remove keys
        gitignore_keys = self.update_git_file(path=self.git_attributes_path, keys=GIT_IGNORE, operation='REMOVE')
        # when in global mode and gitignore is empty, update gitconfig and delete gitignore
        if not gitignore_keys:
            if self.mode == 'global':
                self.execute(['--unset', 'core.excludesfile'])
            self.delete_git_file(self.git_ignore_path)

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
        f = self.execute(['--list', '--show-origin'])
        p = self.execute(['--list'])

        f = f.split('\n')[0]
        p = p.split('\n')[0]

        return f[:f.index(p)][5:][:-11]

    def get_git_attributes_path(self):
        if self.mode == 'local':
            return os.path.join(self.path, '.git','info', 'attributes')

        # check if core.attributesfile is configured
        core_attributesfile = self.execute(['--get', 'core.attributesfile']).split('\n')[0]
        if core_attributesfile:
            return os.path.expanduser(core_attributesfile)

        # put .gitattributes into same directory as global .gitconfig
        return os.path.join(self.git_global_config_dir, '.gitattributes')

    def get_git_ignore_path(self):
        if self.mode == 'local':
            return os.path.join(self.path, '.gitignore')

        # check if core.excludesfile is configured
        core_excludesfile = self.execute(['--get', 'core.excludesfile']).split('\n')[0]
        if core_excludesfile:
            return os.path.expanduser(core_excludesfile)

        # put .gitattributes into same directory as global .gitconfig
        return os.path.join(self.git_global_config_dir, '.gitignore')

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


class CommandParser:

    def __init__(self, args):
        self.args = args

    def test_me(self):
        print('hello')

    def help(self, *args):
        print('help')

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
    command_parser = CommandParser(sys.argv[1:])
    command_parser.execute()
