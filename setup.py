from setuptools import setup

import imp


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


setup(name='wstool',
      version=get_version(),
      packages=['wstool'],
      package_dir={'': 'src'},
      # rosinstall dependency to be kept in order not to break ros hydro install instructions
      install_requires=['vcstools>=0.1.34', 'pyyaml'],
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
