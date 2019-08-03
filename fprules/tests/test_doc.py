from __future__ import print_function
import sys
from contextlib import contextmanager
from inspect import isgenerator
from os import chdir, getcwd, remove, listdir
from os.path import dirname, exists

import pytest
from wget import download

if sys.version_info >= (3, 0):
    from doit.cmd_base import ModuleTaskLoader
    from doit.doit_cmd import DoitMain

from fprules import file_pattern
from fprules.tests.resources import example_csv_ddl


@contextmanager
def cd(path):
    """
    A context manager to temporary change the current directory
    """
    previous_cwd = getcwd()
    chdir(path)
    try:
        yield
    finally:
        chdir(previous_cwd)


def test_doc1(capsys):
    print()
    with cd(dirname(example_csv_ddl.__file__)):
        # define the pattern to create a generator
        with capsys.disabled():
            ddl_task_generator = file_pattern('./defs/*.ddl', './downloaded/%.csv')

            assert isgenerator(ddl_task_generator)
            sorted_list = sorted(ddl_task_generator, key=lambda f: f.name)

        # print the contents of the to-do list
        for t in sorted_list:
            print(t)

        with capsys.disabled():
            captured = capsys.readouterr()
            assert captured.out == """
[iris] defs/iris.ddl -> downloaded/iris.csv
[wine] defs/wine.ddl -> downloaded/wine.csv
"""


@pytest.mark.skipif(sys.version_info < (3, 6), reason="latest `doit` requires python3+, and on python 3.5 the current "
                                                      "directory is not passed correctly.")
def test_doc2():
    """Tests that the example in the documentation is working correctly"""

    with cd(dirname(example_csv_ddl.__file__)):
        # empty the destination folder first
        for t in listdir('./downloaded/'):
            if t not in ('.gitignore', ):
                remove('./downloaded/%s' % t)

        def download_from_ddl_def(ddl_file, csv_path):
            """ download csv file to `csv_path` from url in `ddl_file` """
            # Read the URL from the file
            with open(ddl_file) as f:
                ddl_url = f.readline().strip('\n\r')

            # Download
            print("== Downloading file from {url} to {dst}".format(url=ddl_url, dst=csv_path))
            # attempt to fix the wget bug
            if not hasattr(sys.stdout, 'fileno'):
                setattr(sys.stdout, 'fileno', lambda: 1)
            download(str(ddl_url), str(csv_path))

        # create a doit task
        def task_download_data():
            """
            Downloads a file `./downloaded/<dataset>.csv`
            for each def file `./defs/<dataset>.ddl`.
            """
            for data in file_pattern('./defs/*.ddl', './downloaded/%.csv'):
                yield {
                    'name': data.name,
                    'file_dep': [data.src_path],
                    'actions': [(download_from_ddl_def, (),
                                 dict(ddl_file=data.src_path, csv_path=data.dst_path))],
                    'verbosity': 2,
                    'targets': [data.dst_path]
                }

        loader = ModuleTaskLoader({"task_download_data": task_download_data})

        status_code = DoitMain(loader).run(['list', '--all'])
        assert status_code == 0

        status_code = DoitMain(loader).run(['download_data'])
        assert status_code == 0

        # check that the destination folder is now full
        for t in listdir('./defs/'):
            assert exists('./downloaded/%s.csv' % t[:-4])
