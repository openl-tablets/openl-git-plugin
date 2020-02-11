import configparser
import os
import subprocess
import sys
import webbrowser

import requests

OPENL_GIT_SETTINGS_FILE = 'git-openl.ini'
NOT_A_REPO_MESSAGE = 'fatal: not a git repository (or any of the parent directories): .git'


def execute(args, path):
    command = ['git', 'config', '--global']
    command += args
    return subprocess.run(command, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True).stdout


def get_global_gitconfig_dir(path):
    f = execute(['--list', '--show-origin'], path)
    p = execute(['--list'], path)

    f = f.split('\n')[0]
    p = p.split('\n')[0]

    return f[:f.index(p)][5:][:-11]


def get_config_dir(path):
    global_config_dir = get_global_gitconfig_dir(path)
    global_config_file = os.path.join(global_config_dir, OPENL_GIT_SETTINGS_FILE)
    if os.path.exists(global_config_file):
        return global_config_file

    local_repo_command = \
        subprocess.Popen(['git', 'rev-parse', '--show-toplevel'], cwd=path, stdout=subprocess.PIPE).communicate()[
            0].rstrip().decode('utf-8')
    if local_repo_command == NOT_A_REPO_MESSAGE:
        print("not a git repo")
        sys.exit(0)
    local_config_dir = os.path.join(local_repo_command, '.git')
    local_config_file = os.path.join(local_config_dir, OPENL_GIT_SETTINGS_FILE)
    if os.path.exists(local_config_file):
        return local_config_file
    else:
        print('there is no local settings')
        sys.exit(0)


if __name__ == "__main__":
    if not 8 <= len(sys.argv) <= 9:
        print('Unexpected number of arguments')
        sys.exit(0)
    if len(sys.argv) == 8:
        _, workbook_name, workbook_b, _, _, workbook_a, _, _ = sys.argv
        numlines = 3
    if len(sys.argv) == 9:
        _, numlines, workbook_name, workbook_b, _, _, workbook_a, _, _ = sys.argv
        numlines = int(numlines)
    print('diff in progress...')
    config = configparser.ConfigParser()
    config_dir = get_config_dir(os.getcwd())
    config.read(config_dir)
    base_url = config['DEFAULT']['default_host']
    post_url = base_url + config['DEFAULT']['comparison_url']

    path_workbook_a = os.path.abspath(workbook_a) if workbook_a != 'nul' else None
    path_workbook_b = os.path.abspath(workbook_b) if workbook_b != 'nul' else None

    f1 = open(path_workbook_a, 'rb')
    f2 = open(path_workbook_b, 'rb')
    print(f"File names = a/{f1.name}, b/{f2.name}")

    try:
        files = {'file1': f1, 'file2': f2}
        response = requests.post(post_url, files=files)
        webbrowser.open(response.url, new=2)
    except requests.exceptions.ConnectionError as err:
        print('Server is not available')
    finally:
        f1.close()
        f2.close()
        print('comparison page in browser was opened')
