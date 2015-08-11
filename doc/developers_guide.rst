Developer's Guide
=================

Changelog
---------

.. toctree::
   :maxdepth: 1

   changelog

Bug reports and feature requests
--------------------------------

- `Submit a bug report <https://github.com/vcstools/wstool/issues>`_

Developer Setup
---------------

The wstool source can be downloaded using Mercurial::

  $ git clone https://github.com/vcstools/wstool.git

You will also need vcstools, which you can either install using pip or download using::

  $ git clone https://github.com/vcstools/vcstools.git
  $ cd vcstools
  $ python develop


wstool uses `setuptools <http://pypi.python.org/pypi/setuptools>`_,
which you will need to download and install in order to run the
packaging.  We use setuptools instead of distutils in order to be able
use ``setup()`` keys like ``install_requires``.

Configure your environment:

   $ cd wstool
   $ python develop

Testing
-------

Install test dependencies

::

   $ pip install nose
   $ pip install mock


wstool uses `Python nose
<http://readthedocs.org/docs/nose/en/latest/>`_ for testing, which is
a fairly simple and straightforward test framework.  The wstool
mainly use :mod:`unittest` to construct test fixtures, but with nose
you can also just write a function that starts with the name ``test``
and use normal ``assert`` statements.

wstool also uses `mock <http://www.voidspace.org.uk/python/mock/>`_
to create mocks for testing.

You can run the tests, including coverage, as follows:

::

   $ cd wstool
   $ make test


Documentation
-------------

Sphinx is used to provide API documentation for wstool.  The documents
are stored in the ``doc`` sub-directory.

You can build the docs as follows:

::

   $ cd wstool/doc
   $ make html

