# Changelog

### 0.3.0 - Support for several double wildcards

 - You can now use several double wildcards in the source pattern, as in `glob`. Fixes [#9](https://github.com/smarie/python-fprules/issues/9)

### 0.2.3 - packaging improvements

 - packaging improvements: set the "universal wheel" flag to 1, and cleaned up the `setup.py`. In particular removed dependency to `six` for setup and added `py.typed` file, as well as set the `zip_safe` flag to False. Removed tests folder from package. Fixes [#8](https://github.com/smarie/python-fprules/issues/8)

### 0.2.2 - `pyproject.toml`

Added `pyproject.toml`.

### 0.2.1 - `setup.py` Bugfix

Dependency `makefun` was not correctly declared into `setup.py`. Fixes [#6](https://github.com/smarie/python-fprules/issues/6).

### 0.2.0 - First public version

`file_pattern` now returns a generator. Fixed [#1](https://github.com/smarie/python-fprules/issues/1).

Improved `__repr__` of `FileItem`. Fixes [#3](https://github.com/smarie/python-fprules/issues/2)

New `names` parameter to improve configurability. Fixed [#2](https://github.com/smarie/python-fprules/issues/2).

### 0.1.0 - Internal version

First version extracted from `doit` pull request [#328](https://github.com/pydoit/doit/pull/328).
