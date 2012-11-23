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
      # rosinstall dependency to be removed later when code has moved to this project
      install_requires=['vcstools', 'pyyaml', 'rosinstall'],
      scripts=["scripts/wstool"],
      author="Tully Foote",
      author_email="tfoote@willowgarage.com",
      url="http://www.ros.org/wiki/wstool",
      download_url="http://pr.willowgarage.com/downloads/wstool/",
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
