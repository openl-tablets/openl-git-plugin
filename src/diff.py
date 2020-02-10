import configparser
import os
import sys
import webbrowser

import requests


def is_frozen():
    return getattr(sys, 'frozen', False)


if is_frozen():
    # running as bundle (aka frozen)
    bundle_dir = sys._MEIPASS
else:
    # running live
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    print(sys.argv)
    if not 8 <= len(sys.argv) <= 9:
        print('Unexpected number of arguments')
        sys.exit(0)
    if len(sys.argv) == 8:
        _, workbook_name, workbook_b, _, _, workbook_a, _, _ = sys.argv
        numlines = 3
    if len(sys.argv) == 9:
        _, numlines, workbook_name, workbook_b, _, _, workbook_a, _, _ = sys.argv
        numlines = int(numlines)

    config = configparser.ConfigParser()
    config.read(os.path.join(bundle_dir, 'config.properties'))
    base_url = config['DEFAULT']['DEFAULT_HOST']
    post_url = base_url + config['DEFAULT']['COMPARISON_URL']

    path_workbook_a = os.path.abspath(workbook_a) if workbook_a != 'nul' else None
    path_workbook_b = os.path.abspath(workbook_b) if workbook_b != 'nul' else None

    f1 = open(path_workbook_a, 'rb')
    f2 = open(path_workbook_b, 'rb')

    try:
        files = {'file1': f1, 'file2': f2}
        response = requests.post(post_url, files=files)
        webbrowser.open(response.url, new=2)
    except requests.exceptions.ConnectionError as err:
        print('Server is not available')
    finally:
        f1.close()
        f2.close()
        print('done')
