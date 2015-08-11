wstool: A tool for managing source code workspaces
==================================================

wstool allows manipulation of a set of version-controlled folders as
specified in a workspace definition file.

.. contents:: Contents
   :depth: 3


Usage
-----

::

  wstool is a command to manipulate multiple version controlled folders.

  Official usage:
    wstool CMD [ARGS] [OPTIONS]

  wstool will try to infer install path from context

  Type 'wstool help' for usage.
  Options:
    help            provide help for commands
    init            set up a directory as workspace
    set             add or changes one entry from your workspace config
    merge           merges your workspace with another config set
    remove (rm)     remove an entry from your workspace config, without deleting files
    update (up)     update or check out some of your config elements
    info            Overview of some entries
    status (st)     print the change status of files in some SCM controlled entries
    diff (di)       print a diff over some SCM controlled entries


init
~~~~

set up a directory as workspace

wstool init does the following:

 1. Reads folder/file/web-uri SOURCE_PATH looking for a rosinstall yaml
 2. Creates new .rosinstall file at TARGET-PATH configured

SOURCE_PATH can e.g. be a folder like /opt/ros/electric
If PATH is not given, uses current folder.

::

  Usage: wstool init [TARGET_PATH [SOURCE_PATH]]?

  Options::

    -h, --help            show this help message and exit
    --continue-on-error   Continue despite checkout errors
    -j JOBS, --parallel=JOBS
                          How many parallel threads to use for installing

Examples::

  $ wstool init ~/jade /opt/ros/jade


set
~~~

add or changes one entry from your workspace config
The command will infer whether you want to add or modify an entry. If
you modify, it will only change the details you provide, keeping
those you did not provide. if you only provide a uri, will use the
basename of it as localname unless such an element already exists.

The command only changes the configuration, to checkout or update
the element, run wstool update afterwards.

::

  Usage: wstool set [localname] [SCM-URI]?  [--(detached|svn|hg|git|bzr)] [--version=VERSION]]

  Options:
    -h, --help            show this help message and exit
    --detached            make an entry unmanaged (default for new element)
    -v VERSION, --version-new=VERSION
                          point SCM to this version
    --git                 make an entry a git entry
    --svn                 make an entry a subversion entry
    --hg                  make an entry a mercurial entry
    --bzr                 make an entry a bazaar entry
    -y, --confirm         Do not ask for confirmation
    -u, --update          update repository after set
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use

Examples::

  $ wstool set robot_model --hg https://kforge.ros.org/robotmodel/robot_model
  $ wstool set robot_model --version robot_model-1.7.1
  $ wstool set robot_model --detached



merge
~~~~~

The command merges config with given other rosinstall element sets, from files
or web uris.

The default workspace will be inferred from context, you can specify one using
-t.

By default, when an element in an additional URI has the same
local-name as an existing element, the existing element will be
replaced. In order to ensure the ordering of elements is as
provided in the URI, use the option ``--merge-kill-append``.

::

  Usage: wstool merge [URI] [OPTIONS]

  Options:
    -h, --help            show this help message and exit
    -a, --merge-kill-append
                          merge by deleting given entry and appending new one
    -k, --merge-keep      (default) merge by keeping existing entry and
                          discarding new one
    -r, --merge-replace   merge by replacing given entry with new one
                          maintaining ordering
    -y, --confirm-all     do not ask for confirmation unless strictly necessary
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use

Examples::

  $ wstool merge someother.rosinstall

You can use '-' to pipe in input, as an example::

  $ roslocate info robot_mode | wstool merge -


update
~~~~~~

update or check out some of your config elements

This command calls the SCM provider to pull changes from remote to
your local filesystem. In case the url has changed, the command will
ask whether to delete or backup the folder.

::

  Usage: wstool update [localname]*

  Options:
    -h, --help            show this help message and exit
    --delete-changed-uris
                          Delete the local copy of a directory before changing
                          uri.
    --abort-changed-uris  Abort if changed uri detected
    --continue-on-error   Continue despite checkout errors
    --backup-changed-uris=BACKUP_CHANGED
                          backup the local copy of a directory before changing
                          uri to this directory.
    -j JOBS, --parallel=JOBS
                          How many parallel threads to use for installing
    -v, --verbose         Whether to print out more information
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use


Examples::

  $ wstool update -t ~/jade
  $ wstool update robot_model geometry



info
~~~~

Overview of some entries

The Status (S) column shows
 x  for missing
 L  for uncommited (local) changes
 V  for difference in version and/or remote URI
 C  for difference in local and remote versions

The 'Version-Spec' column shows what tag, branch or revision was given
in the .rosinstall file. The 'UID' column shows the unique ID of the
current (and specified) version. The 'URI' column shows the configured
URL of the repo.

If status is V, the difference between what was specified and what is
real is shown in the respective column. For SVN entries, the url is
split up according to standard layout (trunk/tags/branches).  The
ROS_PACKAGE_PATH follows the order of the table, earlier entries
overlay later entries.

When given one localname, just show the data of one element in list
form.
This also has the generic properties element which is usually empty.

The ``--only`` option accepts keywords: ['path', 'localname', 'version',
'revision', 'cur_revision', 'uri', 'cur_uri', 'scmtype']

::

  Usage: wstool info [localname]* [OPTIONS]


  Options:
    -h, --help            show this help message and exit
    --root                Show workspace root path
    --data-only           Does not provide explanations
    --only=ONLY           Shows comma-separated lists of only given comma-
                          separated attribute(s).
    --yaml                Shows only version of single entry. Intended for
                          scripting.
    --fetch               When used, retrieves version information from remote
                          (takes longer).
    -u, --untracked       Also show untracked files as modifications
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use
    -m, --managed-only    only show managed elements

Examples::

  $ wstool info -t ~/ros/jade
  $ wstool info robot_model
  $ wstool info --yaml
  $ wstool info --only=path,cur_uri,cur_revision robot_model geometry




status
~~~~~~

print the change status of files in some SCM controlled entries. The status
columns meanings are as the respective SCM defines them.

::

  Usage: wstool status [localname]*

  Options:
    -h, --help            show this help message and exit
    --untracked           Also shows untracked files
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use

diff
~~~~

print a diff over some SCM controlled entries

::

  Usage: wstool diff [localname]*

  Options:
    -h, --help            show this help message and exit
    --untracked           Also shows untracked files
    -t WORKSPACE, --target-workspace=WORKSPACE
                        which workspace to use
