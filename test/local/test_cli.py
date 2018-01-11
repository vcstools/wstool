#!/usr/bin/env python
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
import sys
import copy
import tempfile
import unittest
import shutil
import subprocess

from mock import Mock

import wstool.cli_common
import wstool.multiproject_cmd
import wstool.multiproject_cli
from wstool.multiproject_cli import MultiprojectCLI, _get_element_diff
import wstool.config
from wstool.common import MultiProjectException
from wstool.config import MultiProjectException, Config
from wstool.config_yaml import PathSpec

from test.scm_test_base import AbstractFakeRosBasedTest, _add_to_file, \
    _nth_line_split, _create_yaml_file, _create_config_elt_dict
from test.io_wrapper import StringIO
from . import mock_client


class MockConfigElement():
    def __init__(self, local_name='', scmtype=None, path=None, uri=None, spec=None):
        self.scmtype = scmtype
        self.path = path
        self.uri = uri
        self.local_name = local_name
        self.spec = spec

    def get_path(self):
        return self.path

    def get_local_name(self):
        return self.local_name

    def get_path_spec(self):
        return self.spec

    def is_vcs_element(self):
        return True if self.scmtype else False


class GetVersionTest(unittest.TestCase):
    def test_version(self):
        self.assertFalse(None == wstool.multiproject_cmd.cmd_version())


class GetWorkspaceTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.environback = copy.copy(os.environ)
        self.new_environ = os.environ
        self.test_root_path = os.path.realpath(tempfile.mkdtemp())
        self.install_path = os.path.join(self.test_root_path, "install")
        os.makedirs(self.install_path)
        self.install_path2 = os.path.join(self.test_root_path, "install2")
        os.makedirs(self.install_path2)
        _add_to_file(os.path.join(self.install_path, "configfile"), 'content')
        path = self.install_path
        for i in range(4):
            path = os.path.join(path, "path%s" % i)
            os.makedirs(path)

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.test_root_path)
        os.environ.update(self.environback)

    def test_option_arg(self):
        argv = []
        try:
            self.assertEqual(None, wstool.cli_common.get_workspace(argv, self.test_root_path))
            self.fail("expected Exception")
        except MultiProjectException:
            pass
        argv = ["."]
        try:
            self.assertEqual(None, wstool.cli_common.get_workspace(argv, self.test_root_path))
            self.fail("expected Exception")
        except MultiProjectException:
            pass
        abspath = os.path.abspath('good')
        argv = ['bad', '-a', "foo", '-t', 'good', '-b', 'bar', '--bad']
        self.assertEqual(abspath, wstool.cli_common.get_workspace(argv, self.test_root_path))
        argv = ['bad', '-a', "foo", '--target-workspace=good', '-b', 'bar', '--bad']
        self.assertEqual(abspath, wstool.cli_common.get_workspace(argv, self.test_root_path))
        argv = ['bad', '-a', "foo", '--target-workspace', 'good', '-b', 'bar', '--bad']
        self.assertEqual(abspath, wstool.cli_common.get_workspace(argv, self.test_root_path))
        argv = ['bad', '-a', "foo", '-tgood', '-b', 'bar', '--bad']
        self.assertEqual(abspath, wstool.cli_common.get_workspace(argv, self.test_root_path))
        # not supported by OptionParser
        # argv = ['bad', '-a', "foo", '-t=good', '-b', 'bar', '--bad']
        # self.assertEqual(abspath, wstool.cli_common.get_workspace(argv, self.test_root_path))
        argv = ['bad', '-a', "foo", '-t', 'good', '-b', 'bar', '--bad']
        self.assertEqual(abspath, wstool.cli_common.get_workspace(argv, self.test_root_path))

    def test_option_env(self):
        self.new_environ["VARNAME"] = ""
        self.new_environ.pop("VARNAME")
        argv = []
        try:
            self.assertEqual(None, wstool.cli_common.get_workspace(argv, self.test_root_path, varname='VARNAME'))
            self.fail("expected Exception")
        except MultiProjectException:
            pass

        self.new_environ["VARNAME"] = ''
        argv = []
        try:
            self.assertEqual(None, wstool.cli_common.get_workspace(argv, self.test_root_path, varname='VARNAME'))
            self.fail("expected Exception")
        except MultiProjectException:
            pass

        self.new_environ["VARNAME"] = self.install_path2
        argv = []
        self.assertEqual(self.install_path2, wstool.cli_common.get_workspace(argv, self.test_root_path, varname='VARNAME'))

    def test_option_path(self):
        path = self.install_path
        self.new_environ["VARNAME"] = self.install_path2
        for i in range(4):
            path = os.path.join(path, "path%s"%i)
            argv = []
            self.assertEqual(self.install_path, wstool.cli_common.get_workspace(argv, path, config_filename="configfile"))
        try:
            self.assertEqual(self.install_path, wstool.cli_common.get_workspace(argv, path, config_filename="configfile", varname='VARNAME'))
            self.fail("expected Exception")
        except MultiProjectException:
            pass


class FunctionsTest(unittest.TestCase):

    def test_get_mode(self):
        class FakeOpts:
            def __init__(self, dele, ab, back):
                self.delete_changed = dele
                self.backup_changed = back
                self.abort_changed = ab

        class FakeErrors:
            def __init__(self):
                self.rerror = None

            def error(self, foo):
                self.rerror = foo

        opts = FakeOpts(dele=False, ab=False, back='')
        ferr = FakeErrors()
        self.assertEqual("prompt", wstool.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele=True, ab=False, back='')
        ferr = FakeErrors()
        self.assertEqual("delete", wstool.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele=False, ab=True, back='')
        ferr = FakeErrors()
        self.assertEqual("abort", wstool.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele=False, ab=False, back='Foo')
        ferr = FakeErrors()
        self.assertEqual("backup", wstool.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)

        opts = FakeOpts(dele=True, ab=True, back='')
        ferr = FakeErrors()
        wstool.multiproject_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

        opts = FakeOpts(dele=False, ab=True, back='Foo')
        ferr = FakeErrors()
        wstool.multiproject_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

        opts = FakeOpts(dele=True, ab=False, back='Foo')
        ferr = FakeErrors()
        wstool.multiproject_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

    def test_list_usage(self):
        #test function exists and does not fail
        usage = wstool.multiproject_cli.list_usage('foo', 'bardesc %(prog)s', ['cmd1', None, 'cmd2'], {'cmd1': 'help1', 'cmd2': 'help2'}, {'cmd1': 'cmd1a'})
        tokens = [y.strip() for x in usage.split(' ') for y in x.splitlines()]
        self.assertEqual(['bardesc', 'foo', 'cmd1', '(cmd1a)', 'help1', '', 'cmd2', 'help2'], tokens)


class FakeConfig():
    def __init__(self, celts=[], elts=[], path=''):
        self.elts = elts
        self.celts = celts
        self.path = path

    def get_config_elements(self):
        return self.celts

    def get_source(self):
        return self.elts

    def get_base_path(self):
        return self.path


class MockVcsConfigElement(wstool.config_elements.VCSConfigElement):

    def __init__(self, scmtype, path, local_name, uri, version='',
                 actualversion='', specversion='', properties=None):
        self.scmtype = scmtype
        self.path = path
        self.local_name = local_name
        self.vcsc = mock_client.MockVcsClient(
            scmtype, actualversion=actualversion, specversion=specversion)
        self.uri = uri
        self.version = version
        self.install_success = True
        self.properties = properties

    def install(self, checkout=True, backup=False, backup_path=None,
                robust=False, verbose=False, inplace=False, timeout=None, shallow=False):
        if not self.install_success:
            raise MultiProjectException("Unittest Mock says install failed")

    def _get_vcsc(self):
        return self.vcsc


class InstallTest(unittest.TestCase):

    def test_mock_install(self):
        test_root = os.path.realpath(tempfile.mkdtemp())
        try:
            git1 = PathSpec('foo', 'git', 'git/uri', 'git.version')
            svn1 = PathSpec('foos', 'svn', 'svn/uri', '12345')
            hg1 = PathSpec('fooh', 'hg', 'hg/uri', 'hg.version')
            bzr1 = PathSpec('foob', 'bzr', 'bzr/uri', 'bzr.version')
            config = Config([git1, svn1, hg1, bzr1],
                            test_root,
                            None,
                            {"svn": MockVcsConfigElement,
                             "git": MockVcsConfigElement,
                             "hg": MockVcsConfigElement,
                             "bzr": MockVcsConfigElement})
            wstool.multiproject_cmd.cmd_install_or_update(config)
            wstool.multiproject_cmd.cmd_install_or_update(config)
            wstool.multiproject_cmd.cmd_install_or_update(config, num_threads=10)
            wstool.multiproject_cmd.cmd_install_or_update(config, num_threads=10)
            wstool.multiproject_cmd.cmd_install_or_update(config, num_threads=1)
            wstool.multiproject_cmd.cmd_install_or_update(config, num_threads=1)
        finally:
            shutil.rmtree(test_root)

    def test_mock_install_fail(self):
        test_root = os.path.realpath(tempfile.mkdtemp())
        try:
            # robust
            git1 = PathSpec('foo', 'git', 'git/uri', 'git.version')
            svn1 = PathSpec('foos', 'svn', 'svn/uri', '12345')
            hg1 = PathSpec('fooh', 'hg', 'hg/uri', 'hg.version')
            bzr1 = PathSpec('foob', 'bzr', 'bzr/uri', 'bzr.version')
            config = Config([git1, svn1, hg1, bzr1],
                            install_path=test_root,
                            config_filename=None,
                            extended_types={"svn": MockVcsConfigElement,
                                            "git": MockVcsConfigElement,
                                            "hg": MockVcsConfigElement,
                                            "bzr": MockVcsConfigElement})
            config.get_config_elements()[1].install_success = False
            wstool.multiproject_cmd.cmd_install_or_update(
                config, robust=True)
            try:
                wstool.multiproject_cmd.cmd_install_or_update(
                    config, robust=False)
                self.fail("expected Exception")
            except MultiProjectException:
                pass
        finally:
            shutil.rmtree(test_root)

class GetStatusDiffInfoCmdTest(unittest.TestCase):

    def test_status(self):
        self.mock_config = FakeConfig()
        result = wstool.multiproject_cmd.cmd_status(self.mock_config)
        self.assertEqual(len(result), 0)
        self.mock_config = FakeConfig(
            [MockVcsConfigElement('git', 'gitpath', 'gitname', None)])
        result = wstool.multiproject_cmd.cmd_status(self.mock_config)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['status'] is not None)
        self.assertTrue(result[0]['entry'] is not None)
        self.mock_config = FakeConfig(
            [MockVcsConfigElement('git', 'gitpath', 'gitname', None),
             MockVcsConfigElement(
             'svn', 'svnpath', 'svnname', None),
             MockVcsConfigElement(
             'hg', 'hgpath', 'hgname', None),
             MockVcsConfigElement('bzr', 'bzrpath', 'bzrname', None)])
        result = wstool.multiproject_cmd.cmd_status(self.mock_config)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['status'].count('git'), 1)
        self.assertEqual(result[1]['status'].count('svn'), 1)
        self.assertEqual(result[2]['status'].count('hg'), 1)
        self.assertEqual(result[3]['status'].count('bzr'), 1)

    def test_diff(self):
        self.mock_config = FakeConfig()
        result = wstool.multiproject_cmd.cmd_diff(self.mock_config)
        self.assertEqual(len(result), 0)
        self.mock_config = FakeConfig(
            [MockVcsConfigElement('git', 'gitpath', 'gitname', None)])
        result = wstool.multiproject_cmd.cmd_diff(self.mock_config)
        self.assertEqual(1, len(result))
        self.assertTrue(result[0]['diff'] is not None)
        self.assertTrue(result[0]['entry'] is not None)
        self.mock_config = FakeConfig(
            [MockVcsConfigElement('git', 'gitpath', 'gitname', None),
             MockVcsConfigElement(
             'svn', 'svnpath', 'svnname', None),
             MockVcsConfigElement(
             'hg', 'hgpath', 'hgname', None),
             MockVcsConfigElement('bzr', 'bzrpath', 'bzrname', None)])
        result = wstool.multiproject_cmd.cmd_diff(self.mock_config)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['diff'].count('git'), 1)
        self.assertEqual(result[1]['diff'].count('svn'), 1)
        self.assertEqual(result[2]['diff'].count('hg'), 1)
        self.assertEqual(result[3]['diff'].count('bzr'), 1)

    def test_info(self):
        self.mock_config = FakeConfig([], [], 'foopath')
        result = wstool.multiproject_cmd.cmd_info(self.mock_config)
        self.assertEqual(len(result), 0)
        self.mock_config = FakeConfig(
            [MockVcsConfigElement(
                'git', 'gitpath', 'gitname', None, version='version')],
            [],
            'foopath')
        result = wstool.multiproject_cmd.cmd_info(self.mock_config)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['scm'], 'git')
        self.assertEqual(result[0]['version'], 'version')

        self.mock_config = FakeConfig(
            [MockVcsConfigElement('git', 'gitpath', 'gitname', None),
             MockVcsConfigElement(
             'svn', 'svnpath', 'svnname', None),
             MockVcsConfigElement(
             'hg', 'hgpath', 'hgname', None),
             MockVcsConfigElement(
             'bzr', 'bzrpath', 'bzrname', None)],
            [],
            'foopath')
        result = wstool.multiproject_cmd.cmd_info(self.mock_config)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['scm'], 'git')
        self.assertEqual(result[1]['scm'], 'svn')
        self.assertEqual(result[2]['scm'], 'hg')
        self.assertEqual(result[3]['scm'], 'bzr')

    def test_unmanaged(self):
        root_path = os.path.realpath(tempfile.mkdtemp())
        ws_path = os.path.join(root_path, "ws")
        os.makedirs(ws_path)

        self.mock_config = FakeConfig([], [], ws_path)
        # empty folder
        result = wstool.multiproject_cmd.cmd_find_unmanaged_repos(self.mock_config)
        self.assertEqual(len(result), 0)
        # subfolders no vcs
        gitrepo_path = os.path.join(ws_path, "gitrepo")
        os.makedirs(gitrepo_path)
        svnrepo_path = os.path.join(ws_path, "svnrepo")
        os.makedirs(svnrepo_path)
        bzrrepo_path = os.path.join(ws_path, "bzrrepo")
        os.makedirs(bzrrepo_path)
        hgrepo_path = os.path.join(ws_path, "sub/hgrepo")
        os.makedirs(hgrepo_path)
        result = wstool.multiproject_cmd.cmd_find_unmanaged_repos(self.mock_config)
        self.assertEqual(len(result), 0)
        # vcs folders
        os.makedirs(os.path.join(gitrepo_path, ".git"))
        os.makedirs(os.path.join(hgrepo_path, ".hg"))
        os.makedirs(os.path.join(svnrepo_path, ".svn"))
        os.makedirs(os.path.join(bzrrepo_path, ".bzr"))
        result = wstool.multiproject_cmd.cmd_find_unmanaged_repos(self.mock_config)
        self.assertEqual(len(result), 4)
        # vcs folders covered
        mock = MockVcsConfigElement('git',
                                    gitrepo_path,
                                    'gitrepo',
                                    None,
                                    version='version',
                                    actualversion='actual',
                                    specversion='spec')
        self.mock_config = FakeConfig([mock], [], ws_path)
        # empty folder
        result = wstool.multiproject_cmd.cmd_find_unmanaged_repos(self.mock_config)
        self.assertEqual(len(result), 3)

    def test_info_real_path(self):
        root_path = os.path.realpath(tempfile.mkdtemp())
        el_path = os.path.join(root_path, "ros")
        os.makedirs(el_path)
        try:
            self.mock_config = FakeConfig([], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_info(self.mock_config)
            self.assertEqual(len(result), 0)
            mock = MockVcsConfigElement('git',
                                        el_path,
                                        'gitname',
                                        None,
                                        version='version',
                                        actualversion='actual',
                                        specversion='spec')
            self.mock_config = FakeConfig([mock], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_info(self.mock_config)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['scm'], 'git')
            self.assertEqual(result[0]['version'], 'version')
            self.assertEqual(result[0]['specversion'], 'spec')
            self.assertEqual(result[0]['actualversion'], 'actual')
            mock = MockVcsConfigElement('git',
                                        el_path,
                                        'gitname',
                                        None,
                                        version='version',
                                        actualversion='actual',
                                        specversion=None)  # means scm does not know version
            self.mock_config = FakeConfig([mock], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_info(self.mock_config)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['scm'], 'git')
            self.assertEqual(result[0]['version'], 'version')
            self.assertEqual(result[0]['specversion'], '"version"')
            self.assertEqual(result[0]['actualversion'], 'actual')

        finally:
            shutil.rmtree(root_path)

    def test_get_status(self):
        self.test_root_path = os.path.realpath(tempfile.mkdtemp())
        try:
            basepath = '/foo/path'
            entry = {}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'exists': False}
            self.assertEqual('x', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'exists': False, 'modified': True}
            self.assertEqual('x', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'exists': True, 'modified': True}
            self.assertEqual('M', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'modified': True}
            self.assertEqual('M', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'actualversion': 'foo', 'specversion': 'bar'}
            self.assertEqual('V', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'actualversion': 'foo', 'specversion': 'foo'}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': 'foo', 'curr_uri': 'foo'}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': 'foo', 'curr_uri': 'bar'}
            self.assertEqual('V', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': self.test_root_path, 'curr_uri': self.test_root_path}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': self.test_root_path, 'curr_uri': self.test_root_path + '/foo/..'}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'actualversion': 'foo', 'specversion': 'bar', 'modified': True}
            self.assertEqual('MV', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'version': 'foo', 'default_remote_label': 'bar'}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'version': None, 'default_remote_label': 'bar', 'curr_version': 'bar'}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'version': None, 'default_remote_label': 'bar', 'curr_version': 'foo'}
            self.assertEqual('C', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'remote_revision': 'a1b2c3d4', 'actualversion': 'a1b2c3d4'}
            self.assertEqual('', wstool.cli_common._get_status_flags(basepath, entry))
            entry = {'remote_revision': 'a1b2c3d4', 'actualversion': '999999'}
            self.assertEqual('C', wstool.cli_common._get_status_flags(basepath, entry))
        finally:
            shutil.rmtree(self.test_root_path)

    def test_info_table(self):
        basepath = '/foo/path'
        entries = []
        self.assertEqual('', wstool.cli_common.get_info_table(basepath, entries))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'uri',
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "scm", "version", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'uri',
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': 'specversion',
                    'actualversion': 'actualversion'}]
        self.assertEqual(["localname", 'V', "scm", "version", "actualversion", "(specversion)", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'curr_uri',
                    'version': 'version',
                    'localname': 'localname'}]
        self.assertEqual(["localname", 'V', "scm", "version", "curr_uri", "(uri)"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'version': 'version',
                    'localname': 'localname',
                    'exists': False}]
        self.assertEqual(["localname", 'x', "scm", "version", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        # shorten SHAIDs for git
        entries = [{'scm': 'git',
                    'uri': 'uri',
                    'actualversion': '01234567890123456789012345678',
                    'localname': 'localname',
                    'exists': False}]
        self.assertEqual(["localname", 'x', "git", "012345678901", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'git',
                    'uri': 'uri',
                    'actualversion': '01234567890123456789012345678',
                    'specversion': '1234567890123456789012345678',
                    'localname': 'localname'}]
        self.assertEqual(["localname", 'V', "git", "012345678901", "(123456789012)", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        # recompute svn startdard layout
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/tags/tagname',
                    'curr_uri': None,
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "version", "(tags/tagname)", "some.svn.tags.server/some/"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/branches/branchname',
                    'curr_uri': None,
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "version", "(branches/branchname)", "some.svn.tags.server/some/"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/trunk',
                    'curr_uri': None,
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "version", "(trunk)", "some.svn.tags.server/some/"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/branches/branchname',
                    'curr_uri': 'https://some.svn.tags.server/some/tags/tagname',
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "tags/tagname", "(branches/branchname)", "some.svn.tags.server/some/"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/branches/branchname',
                    'curr_uri': 'https://some.svn.tags.server/some/tags/tagname',
                    'version': None,
                    'localname': 'localname',
                    'specversion': 'broken',
                    'actualversion': 'version'}]
        self.assertEqual(["localname", "V", "svn", "tags/tagname", "(branches/branchname)", "version", "(broken)", "some.svn.tags.server/some/"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'uri',
                    'localname': 'localname',
                    'actualversion': 'actualversion',
                    'default_remote_label': 'default_remote_label',
                    'curr_version': 'curr_version'}]
        self.assertEqual(["localname", "C", "scm", "curr_version", "(default_remote_label)", "actualversion", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'uri',
                    'localname': 'localname',
                    'actualversion': 'actualversion',
                    'default_remote_label': 'curr_version',
                    'curr_version': 'curr_version'}]
        self.assertEqual(["localname", "scm", "curr_version", "(=)", "actualversion", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'uri',
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': 'specversion',
                    'actualversion': 'actualversion'}]
        self.assertEqual(["localname", "scm", "uri"], _nth_line_split(-1, wstool.cli_common.get_info_table(basepath, entries, unmanaged=True)))

    def test_info_list(self):
        basepath = '/foo/path'
        entry = {'scm': 'somescm',
                 'uri': 'someuri',
                 'curr_uri': 'somecurr_uri',
                 'version': 'someversion',
                 'specversion': 'somespecversion',
                 'actualversion': 'someactualversion',
                 'localname': 'somelocalname',
                 'path': 'somepath'}
        result = wstool.cli_common.get_info_list(basepath, entry).split()
        for x in ['somepath', 'somelocalname', 'someactualversion', 'somespecversion', 'someversion', 'somecurr_uri', 'someuri', 'somescm']:
            self.assertTrue(x in result)

class MultiprojectCLITest(AbstractFakeRosBasedTest):

    def test_cmd_init(self):
        self.local_path = os.path.join(self.test_root_path, "ws30")
        os.makedirs(self.local_path)

        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall')
        self.assertEqual(0, cli.cmd_init([self.local_path]))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))

        # self.assertEqual(0, cli.cmd_merge(self.local_path, [self.ros_path, "-y"]))
        # self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        # self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        # self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        # self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))

    def test_init_parallel(self):
        self.local_path = os.path.join(self.test_root_path, "ws31")
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall')
        self.assertEqual(0, cli.cmd_init([self.local_path, self.simple_rosinstall, "--parallel=5"]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'gitrepo')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'hgrepo')))
        self.assertEqual(0, cli.cmd_merge(self.local_path, [self.simple_changed_vcs_rosinstall, "-y"]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'gitrepo')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'hgrepo')))
        self.assertEqual(0, cli.cmd_update(self.local_path, ["--parallel=5"]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'gitrepo')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'hgrepo')))

    def test_cmd_info(self):
        self.local_path = os.path.join(self.test_root_path, "ws_test_cmd_info")
        cli = MultiprojectCLI(progname='multi_cli',
                              config_filename='.rosinstall')
        self.assertEqual(0, cli.cmd_info(self.local_path, []))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['--root']))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['--yaml']))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['--untracked']))
        self.assertEqual(0, cli.cmd_init([self.local_path, self.simple_rosinstall, "--parallel=5"]))
        self.assertEqual(0, cli.cmd_merge(self.local_path, [self.simple_changed_vcs_rosinstall, "-y"]))
        self.assertEqual(0, cli.cmd_info(self.local_path, []))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['gitrepo']))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['hgrepo']))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['--fetch']))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['gitrepo', '--fetch']))
        self.assertEqual(0, cli.cmd_info(self.local_path, ['hgrepo', '--fetch']))

    def test_cmd_set(self):
        self.local_path = os.path.join(self.test_root_path, "ws31b")
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall')
        self.assertEqual(0, cli.cmd_init([self.local_path, self.simple_rosinstall, "--parallel=5"]))
        self.assertEqual(0, cli.cmd_set(self.local_path,
                                        [os.path.join(self.local_path, 'hgrepo'),
                                         "--hg",
                                         'http://some_uri',
                                         '-y']))
        cli.cmd_set(self.local_path,
                    [os.path.join(self.local_path, 'hgrepo'), self.hg_path,
                     '--hg', '--update', '-y'])
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'hgrepo')))
        self.assertRaises(SystemExit, cli.cmd_set, self.local_path,
                          [os.path.join(self.local_path, 'hgrepo'),
                           "--detached",
                           '-y'])
        cli = MultiprojectCLI(progname='multi_cli',
                              config_filename='.rosinstall',
                              allow_other_element=True)
        self.assertEqual(0, cli.cmd_set(self.local_path,
                                        [os.path.join(self.local_path, 'hgrepo'),
                                         "--detached",
                                         '-y']))

    def test_cmd_foreach(self):
        self.local_path = os.path.join(self.test_root_path, 'foreach')
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall')
        cli.cmd_init([self.local_path, self.simple_rosinstall])
        # specified localname
        sys.stdout = f = StringIO()
        cli.cmd_foreach(self.local_path, argv=['gitrepo', 'pwd'])
        sys.stdout = sys.__stdout__
        repo_path = lambda localname: os.path.join(self.local_path, localname)
        self.assertEqual('[gitrepo] %s' % repo_path('gitrepo'),
                         f.getvalue().strip())
        # --git option
        sys.stdout = f = StringIO()
        cli.cmd_foreach(self.local_path, argv=['--git', 'pwd'])
        sys.stdout = sys.__stdout__
        expected_output = '[ros] %s\n[gitrepo] %s' % (repo_path('ros'),
                                                      repo_path('gitrepo'))
        self.assertEqual(expected_output, f.getvalue().strip())

    def test_cmd_remove(self):
        # wstool to create dir
        self.local_path = os.path.join(self.test_root_path, "ws32")
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall', allow_other_element=False)
        self.assertEqual(0, cli.cmd_init([self.local_path]))
        self.assertRaises(MultiProjectException, cli.cmd_merge, self.local_path, [self.git_path, "-y"])
        self.assertRaises(MultiProjectException, cli.cmd_merge, self.local_path, [self.hg_path, "-y"])
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall', allow_other_element=True)
        self.assertEqual(0, cli.cmd_merge(self.local_path, [self.git_path, "-y"]))
        self.assertEqual(0, cli.cmd_merge(self.local_path, [self.hg_path, "-y"]))
        config = wstool.multiproject_cmd.get_config(basepath=self.local_path,
                                                        config_filename='.rosinstall')
        self.assertEqual(len(config.get_config_elements()), 2)
        self.assertEqual(0, cli.cmd_remove(self.local_path, [self.git_path]))
        config = wstool.multiproject_cmd.get_config(basepath=self.local_path,
                                                        config_filename='.rosinstall')
        self.assertEqual(len(config.get_config_elements()), 1)

    def test_cmd_add_uris(self):
        # wstool to create dir
        self.local_path = os.path.join(self.test_root_path, "ws33")
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall')
        simple_rel_rosinstall = os.path.join(self.test_root_path, "simple_rel3.rosinstall")
        _create_yaml_file([_create_config_elt_dict(scmtype="git",
                                                   uri=os.path.join(self.test_root_path, "ros"),
                                                   localname='ros')],
                          simple_rel_rosinstall)
        self.assertEqual(0, cli.cmd_init([self.local_path, simple_rel_rosinstall]))
        config = wstool.multiproject_cmd.get_config(basepath=self.local_path,
                                                        config_filename='.rosinstall')
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('git', config.get_config_elements()[0].get_path_spec().get_scmtype())

        wstool.multiproject_cmd.add_uris(config, [self.local_path])
        self.assertEqual(len(config.get_config_elements()), 1, config)
        self.assertEqual('git', config.get_config_elements()[0].get_path_spec().get_scmtype())

        wstool.multiproject_cmd.add_uris(config, [os.path.join(self.local_path, '.rosinstall')])
        self.assertEqual(len(config.get_config_elements()), 1, config)
        self.assertEqual('git', config.get_config_elements()[0].get_path_spec().get_scmtype())

    def test_get_element_diff(self):
        self.assertEqual('', _get_element_diff(None, None))
        self.assertEqual('', _get_element_diff(None, 42))
        self.assertEqual('', _get_element_diff(42, None))

        spec = PathSpec('foolocalname',
                        scmtype='fooscm',
                        uri='foouri',
                        version='fooversion',
                        path='foopath')

        spec2 = PathSpec('foolocalname')
        element2 = MockConfigElement(local_name='foolocalname', spec=spec2)

        elements = [element2]
        config = FakeConfig(celts=elements)

        output = _get_element_diff(spec, config)
        self.assertEqual(' foolocalname', output)

        output = _get_element_diff(spec, config, extra_verbose=True)
        snippets = [' foolocalname',
                    'version = fooversion',
                    'specified uri = foouri',
                    'scmtype = fooscm']
        for s in snippets:
            self.assertTrue(s in output, "missing snippet: '%s' in '%s'" % (s, output))

    def test_merge_dash(self):
        self.local_path = os.path.join(self.test_root_path, "ws35")
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall')
        self.assertEqual(0, cli.cmd_init([self.local_path, self.simple_rosinstall, "--parallel=5"]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'gitrepo')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'hgrepo')))
        try:
            backup = sys.stdin
            with open(self.simple_changed_vcs_rosinstall, 'r') as fhand:
                contents = fhand.read()
            sys.stdin = Mock()
            sys.stdin.readlines.return_value = contents
            self.assertEqual(0, cli.cmd_merge(self.local_path, ["-"]))
        finally:
            sys.stdin = backup

        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'gitrepo')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'hgrepo')))
        self.assertEqual(0, cli.cmd_update(self.local_path, ["--parallel=5"]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'gitrepo')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'hgrepo')))

    def test_export(self):
        root_path = os.path.realpath(tempfile.mkdtemp())
        el_path = os.path.join(root_path, "ros")
        os.makedirs(el_path)
        try:
            # default test
            self.mock_config = FakeConfig([], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_snapshot(self.mock_config)
            self.assertEqual(0, len(result))
            mock = MockVcsConfigElement('git',
                                        el_path,
                                        'gitname',
                                        None,
                                        version='version',
                                        actualversion='actual',
                                        specversion='spec')
            self.mock_config = FakeConfig([mock], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_snapshot(self.mock_config)
            self.assertEqual(1, len(result))
            self.assertEqual('actual', result[0]['git']['version'])
            # test other is discarded
            mock2 = wstool.config_elements.OtherConfigElement(el_path,
                                                                  'othername')
            self.mock_config = FakeConfig([mock, mock2], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_snapshot(self.mock_config)
            self.assertEqual(1, len(result))
            # test fallbacks on specs if actual version is not known
            mock = MockVcsConfigElement('git',
                                        el_path,
                                        'gitname',
                                        None,
                                        version='version',
                                        actualversion=None,
                                        specversion='spec')
            self.mock_config = FakeConfig([mock], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_snapshot(self.mock_config)
            self.assertEqual(1, len(result))
            self.assertEqual('spec', result[0]['git']['version'])
            mock = MockVcsConfigElement('git',
                                        el_path,
                                        'gitname',
                                        None,
                                        version='version',
                                        actualversion=None,
                                        specversion=None)
            self.mock_config = FakeConfig([mock], [], 'foopath')
            result = wstool.multiproject_cmd.cmd_snapshot(self.mock_config)
            self.assertEqual(1, len(result))
            self.assertEqual('version', result[0]['git']['version'])
        finally:
            shutil.rmtree(root_path)

    def test_scrape(self):
        self.local_path = os.path.join(self.test_root_path, "ws37")
        cli = MultiprojectCLI(progname='multi_cli', config_filename='.rosinstall')
        self.assertEqual(0, cli.cmd_init([self.local_path, self.simple_rosinstall, "--parallel=5"]))
        config = wstool.multiproject_cmd.get_config(basepath=self.local_path,
                                                    config_filename='.rosinstall')
        try:
            cli.cmd_scrape(self.local_path, [], config)
            self.fail("expected Exception")
        except MultiProjectException:
            pass
        git_repo_path = os.path.join(self.local_path, 'gitrepo')
        hg_repo_path = os.path.join(self.local_path, 'hgrepo')
        subprocess.check_call(["git", "init", git_repo_path])
        subprocess.check_call(["hg", "init", hg_repo_path])
        for cmd in [["touch", "foo.txt"],
                    ["hg", "add", hg_repo_path],
                    ["hg", "commit", "-m", "foo"]]:
            subprocess.check_call(cmd, cwd=hg_repo_path)
        self.assertEqual(0, cli.cmd_scrape(self.local_path,
                                           ['-y'],
                                           config))
        config = wstool.multiproject_cmd.get_config(basepath=self.local_path,
                                                        config_filename='.rosinstall')
        # initial config has 1 element, "ros"
        self.assertEqual(len(config.get_config_elements()), 3, config.get_config_elements())
