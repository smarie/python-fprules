import sys
from contextlib import contextmanager
from functools import partial
from inspect import isgenerator
from os import chdir, getcwd, remove, listdir
from os.path import dirname, exists

import pytest

if sys.version_info >= (3, 0):
    from doit.cmd_base import ModuleTaskLoader
    from doit.doit_cmd import DoitMain

from fprules import file_pattern
from fprules.tests.resources import example_csv_ddl
from fprules.tests.ddl_data import download_from_ddl_def


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
        ddl_task_generator = file_pattern('./defs/*.ddl', './downloaded/%.csv')

        assert isgenerator(ddl_task_generator)

        # print the contents of the to-do list
        for t in sorted(ddl_task_generator, key=lambda f: f.name):
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

        # create a doit task
        def task_download_data():
            """
            Downloads file `./downloaded/<dataset>.csv` for each def file `./defs/<dataset>.ddl`.
            """
            for data in file_pattern('./defs/*.ddl', './downloaded/%.csv'):
                yield {
                    'name': data.name,
                    'file_dep': [data.src_path],
                    'actions': [partial(download_from_ddl_def, ddl_file=data.src_path, csv_path=data.dst_path)],
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
