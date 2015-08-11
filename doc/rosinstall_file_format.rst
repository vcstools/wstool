rosinstall file format
======================

Format
------

The rosinstall file format is a yaml document. It is a list of
top level dictionaries. Each top level dictionary is expected to have one of the vcs type keys and no other keys.

Inside every top level dictionary there is one required key, ``local-name`` this represents the path where to install files.  It will support both workspace relative paths as well as absolute paths.

Each of the vcs type keys requires a ``uri`` key, and optionally takes a ``version`` key.

Top Level Keys
--------------
The valid keys are ``svn``, ``hg``, ``git``, ``bzr``.

Each key represents a form of version control system to use.  These are supported from the vcstools module.

Example rosinstall syntax:
--------------------------

Below is an example rosinstall syntax with examples of most of the
possible permutations:

::

 - svn: {local-name: some/local/path2, uri: /some/local/uri}
 - hg: {local-name: some/local/path3, uri: http://some/uri, version: 123}
 - git: {local-name: /some/local/aboslute/path, uri: http://some/uri, version: 123}
 - bzr: {local-name: some/local/path4, uri: http://some/uri, version: 123}

Things to note are:

 - ``version`` is optional though recommended.
 - Absolute or relative paths are valid for ``local-name``
 - ``uri`` can be a local file path to a repository.
