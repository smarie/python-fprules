from fprules import file_pattern

try:
    from pathlib import Path, PurePath
except ImportError:
    from pathlib2 import Path, PurePath


def test_stem_only_simplest():
    # locate the resources folder
    resources = Path(__file__).parent / "resources"

    # use the file_pattern and assert results
    res = file_pattern(resources / "foo/*.y*ml",  "./target/%.toto")
    expected = [
        '%s/foo/xfile.yml -> target/xfile.toto' % resources.as_posix()
    ]
    assert [str(r) for r in res] == expected


def test_stem_with_multifolder_not_dst():
    # locate the resources folder
    resources = Path(__file__).parent / "resources"

    # use the file_pattern and assert results
    res = file_pattern(resources / "foo/**/*.y*ml", "./target/%.toto")
    expected = [
        '%s/foo/xfile.yml -> target/xfile.toto' % resources.as_posix(),
        '%s/foo/bar/file3.yaml -> target/file3.toto' % resources.as_posix()
    ]
    assert [str(r) for r in res] == expected


def test_stem_with_multifolder_in_dst():
    # locate the resources folder
    resources = Path(__file__).parent / "resources"

    # use the file_pattern and assert results
    res = file_pattern(str(resources) + "/foo/**/*.y*ml",  "./%%/target/%")
    expected = [
        '%s/foo/xfile.yml -> target/xfile' % resources.as_posix(),
        '%s/foo/bar/file3.yaml -> bar/target/file3' % resources.as_posix()
    ]
    assert [str(r) for r in res] == expected


def test_stem_multifolder_multi_dst():
    # locate the resources folder
    resources = Path(__file__).parent / "resources"

    # use the file_pattern and assert results
    res = file_pattern(str(resources) + "/foo/**/*.y*ml",
                             dst_pattern=dict(flat="./target/%.toto", nested="./%%/target2/%"))
    expected = [
        "%s/foo/xfile.yml -> {flat=target/xfile.toto, nested=target2/xfile}" % resources.as_posix(),
        '%s/foo/bar/file3.yaml -> {flat=target/file3.toto, nested=bar/target2/file3}' % resources.as_posix()
    ]
    assert [str(r) for r in res] == expected


def test_nostem_nofolder():
    # locate the resources folder
    resources = Path(__file__).parent / "resources"

    # use the file_pattern and assert results
    res = file_pattern(str(resources) + "/foo/", "./target/")
    expected = [
        "%s/foo -> target" % resources.as_posix(),
    ]
    assert [str(r) for r in res] == expected


def test_nostem_folders():
    # locate the resources folder
    resources = Path(__file__).parent / "resources"

    # use the file_pattern and assert results
    res = file_pattern(str(resources) + "/foo/**/[!x]*", "./target/%%")
    expected = [
        # Warning: these first 2 are not intuitive but are actually correct answers.
        "%s/foo/bar -> target" % resources.as_posix(),     # since /bar matches [!x]*
        "%s/foo/barbar -> target" % resources.as_posix(),  # since /barbar matches [!x]*
        "%s/foo/bar/file2 -> target/bar" % resources.as_posix(),
        "%s/foo/bar/file3.yaml -> target/bar" % resources.as_posix(),
    ]
    assert [str(r) for r in res] == expected
