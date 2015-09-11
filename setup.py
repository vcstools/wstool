from setuptools import setup
from distutils.command.build import build
from distutils.command.build_py import build_py

import os
import sys
import imp
import argparse


def get_version():
    ver_file = None
    try:
        ver_file, pathname, description = imp.find_module('__version__', ['src/wstool'])
        vermod = imp.load_module('__version__', ver_file, pathname, description)
        version = vermod.version
        return version
    finally:
        if ver_file is not None:
            ver_file.close()


def _resolve_prefix(prefix, type):
    osx_system_prefix = '/System/Library/Frameworks/Python.framework/Versions'
    if type == 'man':
        if prefix == '/usr':
            return '/usr/share'
        if sys.prefix.startswith(osx_system_prefix):
            return '/usr/share'
    elif type == 'bash_comp':
        if prefix == '/usr':
            return '/'
        if sys.prefix.startswith(osx_system_prefix):
            return '/'
    elif type == 'zsh_comp':
        if sys.prefix.startswith(osx_system_prefix):
            return '/usr'
    else:
        raise ValueError('not supported type')
    return prefix


def get_data_files(prefix):
    data_files = []
    bash_comp_dest = os.path.join(_resolve_prefix(prefix, 'bash_comp'),
                                  'etc/bash_completion.d')
    data_files.append((bash_comp_dest, ['completion/wstool-completion.bash']))
    zsh_comp_dest = os.path.join(_resolve_prefix(prefix, 'zsh_comp'),
                                 'share/zsh/site-functions')
    data_files.append((zsh_comp_dest, ['completion/_wstool',
                                       'completion/wstool-completion.bash']))
    return data_files


parser = argparse.ArgumentParser()
parser.add_argument('--prefix', default='',
                    help='prefix to install data files')
opts, _ = parser.parse_known_args(sys.argv)
prefix = opts.prefix

data_files = get_data_files(prefix)

# At present setuptools has no methods to resolve dependencies at build time,
# so we need to check if sphinx is installed.
# See: https://github.com/pypa/pip/issues/2381
try:
    from sphinx.setup_command import BuildDoc
    HAVE_SPHINX = True
except:
    HAVE_SPHINX = False

if HAVE_SPHINX:
    class WstoolBuildMan(BuildDoc):
        def initialize_options(self):
            BuildDoc.initialize_options(self)
            self.builder = 'man'

    class WstoolBuild(build):
        """Run additional commands before build command"""
        def run(self):
            self.run_command('build_man')
            build.run(self)

    class WstoolBuildPy(build_py):
        """Run additional commands before build_py command"""
        def run(self):
            self.run_command('build_man')
            build_py.run(self)
    cmdclass = dict(
        build=WstoolBuild,
        build_py=WstoolBuildPy,
        build_man=WstoolBuildMan,
    )
    man_dest = os.path.join(_resolve_prefix(prefix, 'man'), 'man/man1')
    data_files.append((man_dest, ['build/sphinx/man/wstool.1']))
else:
    cmdclass = {}

setup(name='wstool',
      version=get_version(),
      packages=['wstool'],
      package_dir={'': 'src'},
      data_files=data_files,
      cmdclass=cmdclass,
      # rosinstall dependency to be kept in order not to break ros hydro install instructions
      install_requires=['vcstools>=0.1.37', 'pyyaml'],
      scripts=["scripts/wstool"],
      author="Tully Foote",
      author_email="tfoote@osrfoundation.org",
      url="http://wiki.ros.org/wstool",
      download_url="http://download.ros.org/downloads/wstool/",
      keywords=["ROS"],
      classifiers=["Programming Language :: Python",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 3",
                   "License :: OSI Approved :: BSD License"],
      description="workspace multi-SCM commands",
      long_description="""\
A tool for managing a workspace of multiple heterogenous SCM repositories
""",
      license="BSD")
