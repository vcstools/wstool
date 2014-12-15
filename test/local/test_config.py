# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import tempfile
import shutil
import unittest

import wstool.config
from wstool.config import MultiProjectException, Config
from wstool.config_yaml import PathSpec

from . import mock_client

_test_root = os.path.dirname(os.path.dirname(__file__))


class MockVcsConfigElement(wstool.config_elements.VCSConfigElement):

    def __init__(self, scmtype, path, local_name, uri, version='', installed=False, install_success=True, properties=None):
        self.scmtype = scmtype
        self.path = path
        self.local_name = local_name
        self.uri = uri
        self.version = version
        self.vcsc = mock_client.MockVcsClient()
        self.installed = installed
        self.install_success = install_success

    def install(self, backup_path=None, arg_mode='abort', robust=False):
        if not self.install_success:
            raise MultiProjectException("Unittest Mock says exception failed")
        self.installed = True


class ConfigMock_Test(unittest.TestCase):

    def test_mock_vcs_element(self):
        yaml = []
        install_path = 'install/path'
        config_filename = '.filename'
        config = Config(yaml, install_path, config_filename)
        try:
            config._create_vcs_config_element('mock', None, None, None)
            fail("expected Exception")
        except MultiProjectException: pass
        config = Config(yaml, install_path, config_filename, {"mock": MockVcsConfigElement})
        self.assertTrue(config._create_vcs_config_element('mock', None, None, None))



class ConfigSimple_Test(unittest.TestCase):

    def _get_mock_config(self, yaml, install_path='/install/path', merge_strategy="KillAppend"):
        config_filename = '.filename'
        return Config(yaml, install_path, config_filename, {"mock": MockVcsConfigElement}, merge_strategy=merge_strategy)

    def test_init_fail(self):
        try:
            Config(None, "path", None)
            self.fail("expected Exception")
        except MultiProjectException:
            pass
        try:
            Config([PathSpec('foo', 'bar')], "path", None)
            self.fail("expected Exception")
        except MultiProjectException:
            pass

    def test_init(self):
        yaml = []
        install_path = '/install/path'
        config_filename = '.filename'
        config = Config(yaml, install_path, config_filename)
        self.assertEqual(install_path, config.get_base_path())
        self.assertEqual([], config.get_config_elements())
        config = Config([PathSpec("foo"),
                         PathSpec(os.path.join(_test_root, "example_dirs", "ros_comm")),
                         PathSpec(os.path.join(_test_root, "example_dirs", "ros")),
                         PathSpec(os.path.join(_test_root, "example_dirs", "roscpp")),
                         PathSpec("bar")],
                        ".",
                        None)
        self.assertEqual(os.path.abspath('.'), config.get_base_path())


    def test_config_simple1(self):
        mock1 = PathSpec('foo')
        config = self._get_mock_config([mock1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('foo', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/install/path/foo', config.get_config_elements()[0].get_path())

    def test_config_simple1_with_setupfile(self):
        mock1 = PathSpec('setup.sh', tags='setup-file')
        config = self._get_mock_config([mock1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('setup.sh', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/install/path/setup.sh', config.get_config_elements()[0].get_path())

        mock1 = PathSpec('/foo')
        mock2 = PathSpec('/opt/setup.sh', tags='setup-file')
        mock3 = PathSpec('/bar')
        config = self._get_mock_config([mock1, mock2, mock3])
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('/opt/setup.sh', config.get_config_elements()[1].get_local_name())
        self.assertEqual('/opt/setup.sh', config.get_config_elements()[1].get_path())


    def test_config_simple2(self):
        git1 = PathSpec('foo', 'git', 'git/uri')
        svn1 = PathSpec('foos', 'svn', 'svn/uri')
        hg1 = PathSpec('fooh', 'hg', 'hg/uri')
        bzr1 = PathSpec('foob', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1])
        self.assertEqual(4, len(config.get_config_elements()))
        self.assertEqual('foo', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/install/path/foo', config.get_config_elements()[0].get_path())
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())
        self.assertEqual('svn', config.get_source()[1].get_scmtype())
        self.assertEqual('/install/path/svn/uri', config.get_source()[1].get_uri())
        self.assertEqual('hg', config.get_source()[2].get_scmtype())
        self.assertEqual('/install/path/hg/uri', config.get_source()[2].get_uri())
        self.assertEqual('bzr', config.get_source()[3].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[3].get_uri())


    def test_config_simple3(self):
        git1 = PathSpec('foo', 'git', 'git/uri', 'git.version')
        svn1 = PathSpec('foos', 'svn', 'svn/uri', '12345')
        bzr1 = PathSpec('foob', 'bzr', 'bzr/uri', 'bzr.version')
        hg1 = PathSpec('fooh', 'hg', 'hg/uri', 'hg.version')
        config = self._get_mock_config([git1, svn1, hg1, bzr1])
        self.assertEqual(4, len(config.get_config_elements()))

    def test_config_realfolders(self):
        try:
            root_path = tempfile.mkdtemp()
            share_path = os.path.join(root_path, "share")
            os.makedirs(share_path)
            ros_path = os.path.join(share_path, "ros")
            os.makedirs(ros_path)

            p1 = PathSpec('share')
            p2 = PathSpec('share/ros')
            config = self._get_mock_config([p1, p2])
            self.assertEqual(2, len(config.get_config_elements()))
            try:
                p1 = PathSpec('share', 'git', 'git/uri', 'git.version')
                p2 = PathSpec('share/ros', 'hg', 'hg/uri', 'hg.version')
                config = self._get_mock_config([p1, p2])
                self.fail("expected overlap Exception")
            except MultiProjectException:
                pass
            try:
                p1 = PathSpec('share', 'git', 'git/uri', 'git.version')
                p2 = PathSpec('share/ros', 'hg', 'hg/uri', 'hg.version')
                config = self._get_mock_config([p2, p1])
                self.fail("expected overlap Exception")
            except MultiProjectException:
                pass
            try:
                p1 = PathSpec('share', 'git', 'git/uri', 'git.version')
                p2 = PathSpec('share/ros')
                config = self._get_mock_config([p2, p1])
                self.fail("expected overlap Exception")
            except MultiProjectException:
                pass
            try:
                p1 = PathSpec('share', 'git', 'git/uri', 'git.version')
                p2 = PathSpec('share/ros')
                config = self._get_mock_config([p1, p2])
                self.fail("expected overlap Exception")
            except MultiProjectException:
                pass
        finally:
            shutil.rmtree(root_path)

    def test_config_merging_kill_append(self):
        git1 = PathSpec('foo', 'git', 'git/uri')
        svn1 = PathSpec('foo', 'svn', 'svn/uri')
        hg1 = PathSpec('foo', 'hg', 'hg/uri')
        bzr1 = PathSpec('foo', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('bzr', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[0].get_uri())
        config = self._get_mock_config([git1, svn1, hg1, bzr1, git1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())
        bzr1 = PathSpec('bar', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1])
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('hg', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/hg/uri', config.get_source()[0].get_uri())
        self.assertEqual('bzr', config.get_source()[1].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[1].get_uri())
        config = self._get_mock_config([git1, svn1, hg1, bzr1, git1])
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('bzr', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[0].get_uri())
        self.assertEqual('git', config.get_source()[1].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[1].get_uri())

    def test_config_merging_keep(self):
        git1 = PathSpec('foo', 'git', 'git/uri')
        svn1 = PathSpec('foo', 'svn', 'svn/uri')
        hg1 = PathSpec('foo', 'hg', 'hg/uri')
        bzr1 = PathSpec('foo', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1], merge_strategy="MergeKeep")
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())
        config = self._get_mock_config([git1, svn1, hg1, bzr1, git1], merge_strategy="MergeKeep")
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())

        bzr1 = PathSpec('bar', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1], merge_strategy="MergeKeep")
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())
        self.assertEqual('bzr', config.get_source()[1].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[1].get_uri())
        config = self._get_mock_config([git1, svn1, hg1, bzr1, git1], merge_strategy="MergeKeep")
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())
        self.assertEqual('bzr', config.get_source()[1].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[1].get_uri())

    def test_config_merging_replace(self):
        git1 = PathSpec('foo', 'git', 'git/uri')
        svn1 = PathSpec('foo', 'svn', 'svn/uri')
        hg1 = PathSpec('foo', 'hg', 'hg/uri')
        bzr1 = PathSpec('foo', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1], merge_strategy="MergeReplace")
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('bzr', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[0].get_uri())
        config = self._get_mock_config([git1, svn1, hg1, bzr1, git1], merge_strategy="MergeReplace")
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())

        bzr1 = PathSpec('bar', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1], merge_strategy="MergeReplace")
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('hg', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/hg/uri', config.get_source()[0].get_uri())
        self.assertEqual('bzr', config.get_source()[1].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[1].get_uri())
        config = self._get_mock_config([git1, svn1, hg1, bzr1, git1], merge_strategy="MergeReplace")
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('/install/path/git/uri', config.get_source()[0].get_uri())
        self.assertEqual('bzr', config.get_source()[1].get_scmtype())
        self.assertEqual('/install/path/bzr/uri', config.get_source()[1].get_uri())

    def test_remove(self):
        git1 = PathSpec('foo', 'git', 'git/uri', 'git.version')
        svn1 = PathSpec('foos', 'svn', 'svn/uri', '12345')
        hg1 = PathSpec('fooh', 'hg', 'hg/uri', 'hg.version')
        bzr1 = PathSpec('foob', 'bzr', 'bzr/uri', 'bzr.version')
        config = self._get_mock_config([git1, svn1, hg1, bzr1])
        self.assertEqual(4, len(config.get_config_elements()))
        self.assertFalse(config.remove_element(None))
        self.assertFalse(config.remove_element('bar'))
        self.assertEqual(4, len(config.get_config_elements()))
        self.assertTrue(config.remove_element('foo'))
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('/install/path/foos', config.get_config_elements()[0].get_path())
        self.assertEqual('/install/path/fooh', config.get_config_elements()[1].get_path())
        self.assertEqual('/install/path/foob', config.get_config_elements()[2].get_path())
        self.assertTrue(config.remove_element('fooh'))
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('/install/path/foos', config.get_config_elements()[0].get_path())
        self.assertEqual('/install/path/foob', config.get_config_elements()[1].get_path())
        self.assertTrue(config.remove_element('foos'))
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertTrue(config.remove_element('foob'))
        self.assertEqual(0, len(config.get_config_elements()))

    def test_absolute_localname(self):
        mock1 = PathSpec('/foo/bim')
        config = self._get_mock_config([mock1], install_path='/foo/bar/ba/ra/baz/bam')
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('/foo/bim', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/foo/bim', config.get_config_elements()[0].get_path())

    def test_unnormalized_localname(self):
        "Should source normalize local-name"
        mock1 = PathSpec('foo/bar/..')
        config = self._get_mock_config([mock1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('foo', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/install/path/foo', config.get_config_elements()[0].get_path())

    def test_long_localname(self):
        "Should source choose shorter local-name"
        mock1 = PathSpec("/foo/bar/boo/far/bim")
        config = self._get_mock_config([mock1], '/foo/bar/boo/far')
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('/foo/bar/boo/far/bim', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/foo/bar/boo/far/bim', config.get_config_elements()[0].get_path())

    def test_double_entry(self):
        "Should source be rewritten without duplicates"
        mock1 = PathSpec('foo')
        mock2 = PathSpec('foo')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))

    def test_equivalent_entry(self):
        "Should source be rewritten without duplicates"
        mock1 = PathSpec('foo')
        mock2 = PathSpec('./foo')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))

    def test_double_localname(self):
        "Entries have same local name"
        mock1 = PathSpec('foo', 'git', 'git/uri')
        mock2 = PathSpec('foo', 'hg', 'hg/uri')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))

    def test_equivalent_localname(self):
        "Entries have equivalent local name"
        mock1 = PathSpec('foo', 'git', 'git/uri')
        mock2 = PathSpec('./foo/bar/..', 'hg', 'hg/uri')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))
