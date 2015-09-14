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
