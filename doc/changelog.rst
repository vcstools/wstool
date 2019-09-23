Changelog
=========

0.1.18
------

- fix warnings by replacing yaml.load() with safe_load()
- Re-add snapshot command called 'export' (#117, #120)
- fix '-t' option not working for wstool remove
- upgrade vcstools library version to 0.1.41, with new fixes:

  - fix git submodule errors
  - fix export_upstream for git submodules
  - fix python3 incompatibility
  - fix git fast-forward failures
  - fix get_affected_files

0.1.17
------

- Reverted the snapshot command since it was breaking ``rosws`` until it can be fixed.

0.1.16
------

- Fixed some issues with new ``requirements.txt`` usage during the release process.

0.1.15
------

- Fixed an issue with the conditional dependency on ``ordereddict`` in the ``setup.py`` file.

0.1.14
------

- Fixed an issue which caused a traceback with invalid command line options.
- Added a feature to "snapshot" the current commit hashes in the workspace as a rosinstall file.
- Fixed option handling and documentation of the ``--untracked`` option.
- Added ``--shallow`` option to ``wstool init`` for shallow checkouts with git.
- Contributors: @cbandera, @rsinnet, @amiller27, @jayvdb, @at-wat

0.1.13
------

- Fix to avoid errors due to installing man pages with OS X's 10.11's new SIP settings.
- Added option to show a simplified version info table.
- Added the -m (timeout), -v (verbose), and -j (parallel jobs) options to each command.
- Contributors: @NikolausDemmel, @wkentaro

0.1.12
------

- Fix command line arguments of ``wstool scrape``.

0.1.11
------

- Changed the way ``.bak`` files are created when overwriting existing configurations.
- Added the Scrape command.
- Added default git branch and status to ``wstool fetch --info``.
- Added versioned dependency on vcstools ``0.1.38`` to make use of new API features.

0.1.10
------

- Fix regression which broke the -j option.
- Enable pretty printing of the ``.rosinstall`` file's YAML.

0.1.9
-----

- Fix for zsh completion.
- Fixed version dependency on vcstools for debian.

0.1.8
-----

- Fix for installation issue.

0.1.7
-----

- Added installation of generated man pages.
- Added installation of shell completion for wstool.
- Improved output of wstool info with the new get_current_version_label in vcstools.
- Added a foreach command.
- Added a ``--root`` option to wstool info.
- Enhanced the ``--update`` option for wstool set.
- Now uses multiple threads for network operations by default.
- Some other minor fixes and improvements and docs.

0.1.5
-----

- Releasing to allow changes for new platform vivid.
- Fix svn diff for change in output with svn 1.7.9.
- info command shows information about unmanaged paths.

0.1.4
-----

- Fix detection of path conflicts #24 (https://github.com/vcstools/wstool/pull/24).

0.0.3
-----

- not using ROS_WORKSPACE anymore
- fix to "wstool cmd --help"

0.0.2
-----

- fix #2 creating "wstool2 file instaed of ".rosinstall"

0.0.1
-----

- Initial creation based on functions inrosinstall
