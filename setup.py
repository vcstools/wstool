from setuptools import setup
from distutils.command.build import build
from distutils.command.build_py import build_py

import os
import sys
import imp
import argparse


with open('README.rst') as readme_file:
    README = readme_file.read()


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
    # install to outside of system if OS X to avoid issues caused by
    # System Integrity Protection on El Caption
    # issue: https://github.com/vcstools/wstool/issues/81
    osx_system_prefix = '/System/Library/Frameworks/Python.framework/Versions'
    if type == 'man':
        if prefix == '/usr':
            return '/usr/share'
        if sys.prefix.startswith(osx_system_prefix):
            return '/usr/local/share'
    elif type == 'bash_comp':
        if prefix == '/usr':
            return '/'
        if sys.prefix.startswith(osx_system_prefix):
            return '/usr/local'
    elif type == 'zsh_comp':
        if sys.prefix.startswith(osx_system_prefix):
            return '/usr/local'
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
parser.add_argument('--prefix', default=None,
                    help='prefix to install data files')
opts, _ = parser.parse_known_args(sys.argv)
prefix = sys.prefix if opts.prefix == None else opts.prefix

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

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as requirements:
    install_requires = requirements.read().splitlines()

with open(os.path.join(os.path.dirname(__file__), 'requirements-test.txt')) as requirements:
    test_required = requirements.read().splitlines()

setup(name='wstool',
      version=get_version(),
      packages=['wstool'],
      package_dir={'': 'src'},
      data_files=data_files,
      cmdclass=cmdclass,
      # rosinstall dependency to be kept in order not to break ros hydro install instructions
      install_requires=install_requires,
      # extras_require allow pip install .[test]
      extras_require={
        'test': test_required
      },
      # tests_require automatically installed when running python setup.py test
      tests_require=test_required,
      scripts=["scripts/wstool"],
      author="Tully Foote",
      author_email="tfoote@osrfoundation.org",
      url="http://wiki.ros.org/wstool",
      keywords=["ROS"],
      classifiers=["Programming Language :: Python",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 3",
                   "Development Status :: 7 - Inactive",
                   "License :: OSI Approved :: BSD License",
                   "Topic :: Software Development :: Version Control"
      ],
      description="workspace multi-SCM commands",
      long_description=README,
      license="BSD")
