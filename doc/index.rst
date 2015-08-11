wstool
======

.. module:: wstool
.. moduleauthor:: Tully Foote <tfoote@willowgarage.com>, Thibault Kruse <kruset@in.tum.de>, Ken Conley <kwc@willowgarage.com>

Using wstool you can update several folders using a variety
of SCMs (SVN, Mercurial, git, Bazaar) with just one command.

That way you can more effectively manage source code workspaces.

The wstool package provides a Python API for interacting with a
source code workspace as well as a group of command line tools.
Rosinstall leverages the :mod:`vcstools` package for source control and
stores its state in .rosinstall files.


Command Line Tools:
===================
.. toctree::
   :maxdepth: 2

   wstool_usage


Installation
============

Ubuntu
------

On Ubuntu the recommended way to install rosinstall is to use apt.

::

    sudo apt-get install python-wstool

Other Platforms
---------------

On other platforms rosinstall is available on pypi and can be installed via ``pip``
::

    pip install -U wstool

or ``easy_install``:

::

    easy_install -U wstool vcstools




Rosinstall File Format:
=======================
.. toctree::
   :maxdepth: 2

   rosinstall_file_format


Advanced: rosinstall developers/contributors
============================================

.. toctree::
   :maxdepth: 2

   developers_guide


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
