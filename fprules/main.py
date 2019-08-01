try:
    from pathlib import Path, PurePath
except ImportError:
    from pathlib2 import Path, PurePath


def gen_matching_files(src_pattern,  # type: Path
                       ):
    """
    Utility generator function used by `file_pattern` to yield of matching file
    elements corresponding to the provided `src_pattern`.

    If `src_pattern` contains a double wildcard `**`, each element returned by
    this generator list will be a tuple containing two elements:

     - the first element is the `Path` of the file or folder that matched the
       search
     - the second element is a string representing the part of the path
       captured by the double wildcard. Otherwise the second element is `None`.

    If no double wildcard `**` is present in `src_pattern`, only path elements
    are yielded.

    :param src_pattern: a `Path` representing the source pattern to match.
        The list returned will contain one item for each file matching
        this pattern, using `glob` to perform the match.
    :return: a generator yielding either <file_path> items, or tuples
        (<file_path>, <captured_double_wildcard_path>) depending on whether a
        `**` was present in the pattern or not.
    """
    # -- validate the source pattern
    src_double_wildcard = None
    src_glob_start = None
    for i, p in enumerate(src_pattern.parts):
        if src_glob_start is None and ('*' in p or '?' in p or '[' in p):
            src_glob_start = i
        if '**' in p:
            if p != '**':
                raise ValueError("Invalid pattern '%s': double-wildcard should"
                                 " be alone in its path element" % src_pattern)
            elif src_double_wildcard is None:
                try:
                    end_ptrn = Path(*src_pattern.parts[i+1:])
                except IndexError:
                    end_ptrn = None
                src_double_wildcard = (i, end_ptrn)
            else:
                raise ValueError("Invalid source pattern '%s': several "
                                 "double-wildcards exist." % src_pattern)

    # -- Perform the glob file search operation, using Pathlib.glob
    if src_glob_start is None:
        glob_results = (src_pattern,)
    else:
        root_path = src_pattern.parents[len(src_pattern.parts)
                                        - src_glob_start - 1]
        to_search = PurePath(*src_pattern.parts[src_glob_start:])
        glob_results = root_path.glob(str(to_search))

    # Create the appropriate generator according to presence of '**'
    if src_double_wildcard is None:
        # simply yield the matching file Path items
        for matched_file in glob_results:
            yield matched_file
    else:
        # for each matching item, find the path captured by the '**' and yield
        for matched_file in glob_results:
            # get information about the double wildcard
            src_dblwildcard_idx, src_ptrn_suffix = src_double_wildcard

            # split the path in two according to the double wildcard position
            root_path = matched_file.parents[len(matched_file.parts)
                                              - src_dblwildcard_idx - 1]
            variable_path = matched_file.parts[src_dblwildcard_idx:]

            # remove the end of the path according to what was really matched
            if src_ptrn_suffix is not None:
                src_ptrn_suffix_str = str(src_ptrn_suffix)
                for i in range(len(variable_path)):
                    s_root = (root_path / Path(*variable_path[:i]))
                    if matched_file in tuple(s_root.glob(src_ptrn_suffix_str)):
                        variable_path = variable_path[:i]
                        break
                else:
                    # nothing matched, this has to be because len is 0.
                    assert len(variable_path) == 0

            yield (matched_file, str(PurePath(*variable_path)))


class FileItem(namedtuple('FileItem',
                          ('src_path', 'has_multi_targets', 'dst_path'))):
    """
    Represents an item created by `file_pattern(...)`.
    """
    def __getattr__(self, item):
        """
        If the item has multiple targets, allow users to access them with an
        attribute style. (see `munch` for inspiration)
        """
        if self.has_multi_targets:
            try:
                return self.dst_path[item]
            except KeyError as e:
                raise AttributeError(item)
        else:
            return super(FileItem, self).__getattribute__(item)

    def __str__(self):
        if self.has_multi_targets:
            secnd_str = "{%s}" % ', '.join(["%s=%s" % (k, v.as_posix())
                                            for k, v in self.dst_path.items()])
        else:
            secnd_str = self.dst_path.as_posix()

        return "%s -> %s" % (self.src_path.as_posix(), secnd_str)


def file_pattern(src_pattern,  # type: Union[str, Any]
                 dst_pattern   # type: Union[str, Any]
                 ):
    # type: (...) -> List[FileItem]
    """
    Lists all source files corresponding to `src_pattern` and creates target
    file paths according to `dst_pattern`. The result is a list of `FileItem`
    objects containing both the source and destination paths, that can
    typically be used as "to-do lists" in task generators as shown in the
    example below:

    ```python
    from doit.tools import file_pattern

    ALL_DATA = file_pattern('./data/defs/**/*.ddl', './data/raw/%.csv')

    def task_download_data():
        '''
        Downloads csv file `./data/raw/<dataset>.csv`
        for each def file `./data/defs/**/<dataset>.ddl`.
        '''
        for data in ALL_DATA:
            yield {
                'name': data.name,
                'file_dep': [data.src_path, DATA_DDL_PYSCRIPT],
                'actions': ["python %s --ddl_csv %s"
                            % (DATA_DDL_PYSCRIPT, data.src_path)],
                'verbosity': 2,
                'targets': [data.dst_path]
            }
    ```

    `src_pattern` and `dst_pattern` patterns can be a string or any object - in
    which case `str()` will be applied on the object before use. For example
    you can use `Path` instances from `pathlib`.

    Source pattern `src_pattern` should follow the python `glob` syntax,
    see https://docs.python.org/3/library/glob.html.

    Destination pattern `dst_pattern` represents target paths to create. In
    this pattern, the following special expressions can be used:

     - *stem* character `%`: will be replaced with the stem of a matched file
       or the folder name of a matched folder.

     - *variable path* characters `%%`: represents the part of the path matched
       by the `**` in the source pattern. In that case the source pattern MUST
       contain a double-wildcard, and only one.

    It is possible to declare multiple destination patterns by passing a `dict`
    `dst_pattern` instead of a single element. In that case the resulting list
    will contain `FileItem` instances that have one attribute per pattern.

    This feature was inspired by GNU make 'pattern rules', see
    https://www.gnu.org/software/make/manual/html_node/Pattern-Examples.html

    :param src_pattern: a string or object representing the source pattern to
        match. The list returned will contain one item for each file matching
        this pattern, using `glob` to perform the match.
    :param dst_pattern: a string or object representing the destination
        pattern to use to create target file paths. A dictionary can also be
        provided to create several target file paths at once
    :return: a list of `FileItem` instances with at least two fields `src_path`
        and `dst_path`. When `dst_pattern` is a dictionary, the items will also
        show one attribute per key in that dictionary.
    """
    if not isinstance(src_pattern, PurePath):
        # create a pathlib.Path based on the string view of the object
        # since we will use a parent in this pattern for actual glob search,
        # we use a concrete `Path` not a `PurePath`
        src_pattern_str = str(src_pattern)
        src_has_double_wildcard = '**' in src_pattern_str
        src_pattern = Path(src_pattern_str)
    else:
        src_has_double_wildcard = '**' in str(src_pattern)

    # create the generator
    match_generator = gen_matching_files(src_pattern)

    # -- validate the destination patterns
    def _validate_dst_pattern(dst_pattern):
        """return a validated dst pattern string"""

        # convert the dest pattern
        if not isinstance(dst_pattern, str):
            dst_pattern = str(dst_pattern)

        # validate the dest pattern
        if '*' in dst_pattern:
            raise ValueError("Destination pattern can not contain star '*' "
                             "wildcards, only '%%' characters. Found '%s'"
                             % dst_pattern)
        if '%%' in dst_pattern and not src_has_double_wildcard:
            raise ValueError(
                "Destination pattern '%s' uses a folder path '%%%%' but source"
                " pattern does not include any double-wildcard: '%s'"
                % (dst_pattern, src_pattern))
        return dst_pattern

    try:
        # assume a dictionary of destination patterns
        for dst_name, _dst_pattern in dst_pattern.items():
            dst_pattern[dst_name] = _validate_dst_pattern(_dst_pattern)
        has_multi_targets = True
    except AttributeError:
        # single pattern
        dst_pattern = _validate_dst_pattern(dst_pattern)
        has_multi_targets = False

    res = []
    if not src_has_double_wildcard:
        def _create_dst_path(matching_file, dst_pattern):
            # replace % with stem and convert to Path object
            return Path(dst_pattern.replace('%', matching_file.stem))

        for f_path in match_generator:
            # create the destination path(s)
            if has_multi_targets:
                dst_paths = {dst_name: _create_dst_path(f_path, _dst_pattern)
                             for dst_name, _dst_pattern in dst_pattern.items()}
            else:
                dst_paths = _create_dst_path(f_path, dst_pattern)

            # finally create the container object and append
            item = FileItem(src_path=f_path, dst_path=dst_paths,
                            has_multi_targets=has_multi_targets)
            res.append(item)
    else:
        def _create_dst_path(matching_file, captured_subpath, dst_pattern):
            # replace %% with the **-captured sub-path
            if '%%' in dst_pattern:
                dst_path = dst_pattern.replace('%%', captured_subpath)
            else:
                dst_path = dst_pattern

            # replace % with file stem and convert to Path object
            return Path(dst_path.replace('%', matching_file.stem))

        for f_path, capt_subpath in match_generator:
            # create the destination path(s)
            if has_multi_targets:
                dst_paths = {dst_name: _create_dst_path(f_path, capt_subpath,
                                                        _dst_pattern)
                             for dst_name, _dst_pattern in dst_pattern.items()}
            else:
                dst_paths = _create_dst_path(f_path, capt_subpath, dst_pattern)

            # finally create the container object and append
            item = FileItem(src_path=f_path, dst_path=dst_paths,
                            has_multi_targets=has_multi_targets)
            res.append(item)

    return res
