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
import unittest
import tempfile
import shutil
import subprocess

import wstool.config_yaml
import wstool.config
from wstool.common import MultiProjectException
from wstool.config_yaml import rewrite_included_source, \
    get_path_spec_from_yaml, get_yaml_from_uri, get_path_specs_from_uri, \
    PathSpec, aggregate_from_uris, __REPOTYPES__

_test_root = os.path.dirname(os.path.dirname(__file__))


class YamlIO_Test(unittest.TestCase):

    def test_get_yaml_from_uri_from_file(self):
        filename = os.path.join(_test_root, "example.yaml")
        yamlstr = get_yaml_from_uri(filename)

        self.assertTrue("text" in yamlstr)
        self.assertTrue(yamlstr["text"] == "foobar")

        self.assertTrue("number" in yamlstr)
        self.assertTrue(yamlstr["number"] == 2)
        # invalid
        try:
            yaml = get_yaml_from_uri(
                os.path.join(_test_root, "example-broken.yaml"))
        except MultiProjectException:
            pass
        try:
            get_path_specs_from_uri(filename)
            self.fail("Expected exception")
        except MultiProjectException:
            pass

    def test_get_yaml_from_uri_from_missing_file(self):
        filename = "/asdfasdfasdfasfasdf_does_not_exist"
        try:
            get_yaml_from_uri(filename)
            self.fail("Expected exception")
        except MultiProjectException:
            pass
        try:
            get_path_specs_from_uri(filename)
            self.fail("Expected exception")
        except MultiProjectException:
            pass

    def test_get_yaml_from_uri_from_invalid_url(self):
        url = "http://invalidurl"
        try:
            get_yaml_from_uri(url)
            self.fail("Expected exception")
        except MultiProjectException:
            pass

        # valid but non-yaml
        url = "http://www.google.com"
        try:
            get_yaml_from_uri(url)
            self.fail("Expected exception")
        except MultiProjectException:
            pass


class ConfigElementYamlFunctions_Test(unittest.TestCase):

    def test_rewrite_included_source(self):
        base_path = '/foo/bar'
        version = 'common_rosdeps-1.0.2'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        # same simple
        struct = [PathSpec('local', 'hg', uri, version)]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual(PathSpec(os.path.join(base_path, "local")), struct[0])
        # absolute path
        struct = [PathSpec("/opt/poo", 'hg', uri, version)]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual([PathSpec("/opt/poo")], struct)
        # absolute path, relative basepath
        struct = [PathSpec("/opt/poo", 'hg', uri, version)]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("/opt/poo")], struct)
        # relative base path
        struct = [PathSpec("../opt/poo", 'hg', uri, version)]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("foo/opt/poo")], struct)

    def test_rewrite_included_source_setupfile(self):
        base_path = '/foo/bar'
        version = 'common_rosdeps-1.0.2'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        # same simple
        struct = [PathSpec('local', tags='setup-file')]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual(PathSpec(os.path.join(base_path, "local"), tags='setup-file'), struct[0])
        # absolute path
        struct = [PathSpec("/opt/poo", tags='setup-file')]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual([PathSpec("/opt/poo", tags='setup-file')], struct)
        # absolute path, relative basepath
        struct = [PathSpec("/opt/poo", tags='setup-file')]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("/opt/poo", tags='setup-file')], struct)
        # relative base path
        struct = [PathSpec("../opt/poo", tags='setup-file')]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("foo/opt/poo", tags='setup-file')], struct)


class UriAggregationTest(unittest.TestCase):

    def test_aggregate_from_uris(self):
        self.directory = tempfile.mkdtemp()
        config = wstool.config.Config(
            [PathSpec('ros', 'svn', 'some/uri')], self.directory)
        wstool.config_yaml.generate_config_yaml(config, 'foo', "# Hello\n")
        ryaml = aggregate_from_uris(
            [self.directory], config.get_config_filename())
        self.assertEqual(ryaml[0].get_legacy_yaml(),
                         {'other': {'local-name': self.directory}})
        self.assertRaises(MultiProjectException,
                          aggregate_from_uris,
                          [self.directory],
                          config.get_config_filename(),
                          allow_other_element=False)

    def tearDown(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)


class ConfigFile_Test(unittest.TestCase):

    def make_repo_get_uuid(self):
        repo_path = os.path.join(self.directory, self.git)
        subprocess.check_call(['git', 'init', self.git], cwd=self.directory)
        subprocess.check_call(['touch', 'test.txt'], cwd=repo_path)
        subprocess.check_call(['git', 'add', '*'], cwd=repo_path)
        subprocess.check_call(['git', 'commit', '-m', 'msg'], cwd=repo_path)
        subprocess.check_call(['git', 'remote', 'add', 'origin', self.uri],
                              cwd=repo_path)
        po = subprocess.Popen(['git', 'rev-parse', 'HEAD'], cwd=repo_path,
                              stdout=subprocess.PIPE)
        uuid = po.stdout.read().decode('UTF-8').rstrip('"\n').lstrip('"\n')
        return uuid

    def helper(self, check_config_entries, args, entries):
        assert check_config_entries.__class__.__name__ == 'function'

        header = '# Hello'
        filename = 'foo'
        uuid = self.make_repo_get_uuid()

        for entry in entries:
            self.assertTrue(isinstance(entry, PathSpec))
            if entry._scmtype:
                self.assertTrue(entry._scmtype in __REPOTYPES__)

        config = wstool.config.Config(entries, self.directory)
        wstool.config_yaml.generate_config_yaml(config, filename,
                                                header + '\n', **args)
        filepath = os.path.join(self.directory, filename)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            read_data = f.read()
        lines = read_data.splitlines()
        self.assertTrue(len(lines) > 0)
        self.assertEqual(header, lines[0])
        check_config_entries(self, lines[1:], uuid)

    def test_generate_empty(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(0, len(lines))
        self.helper(check_config_entries, {}, [])

    def test_generate_with_version(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(2, len(lines))
            self.assertEqual(self.git_el % self.version, lines[0])
            self.assertEqual(self.other_el, lines[1])
        self.helper(check_config_entries, {},
                    [PathSpec(self.git, 'git', self.uri, self.version),
                     PathSpec(self.other)])

    def test_generate_with_exact(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(2, len(lines))
            self.assertEqual(self.git_el % uuid, lines[0])
            self.assertEqual(self.other_el, lines[1])
        self.helper(check_config_entries, {'spec': False, 'exact': True},
                    [PathSpec(self.git, 'git', self.uri, self.version),
                     PathSpec(self.other)])

    def test_generate_with_vcs_only(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(1, len(lines))
            self.assertEqual(self.git_el % self.version, lines[0])
        self.helper(check_config_entries, {'vcs_only': True},
                    [PathSpec(self.git, 'git', self.uri, self.version),
                     PathSpec(self.other)])

    def test_generate_with_spec_exact(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(1, len(lines))
            self.assertEqual(self.git_el % uuid, lines[0])
        self.helper(check_config_entries,
                    {'spec': True, 'exact': 'True', 'vcs_only': True},
                    [PathSpec(self.git, 'git', self.uri, self.version),
                     PathSpec(self.other)])

    def test_generate_with_other(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(1, len(lines))
            self.assertEqual(self.other_el, lines[0])
        self.helper(check_config_entries, {}, [PathSpec(self.other)])

    def test_generate_with_stack(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(1, len(lines))
            self.assertEqual("- svn: {local-name: ros, uri: %s/some/uri}"
                             % self.directory, lines[0])
        self.helper(check_config_entries, {},
                    [PathSpec('ros', 'svn', 'some/uri')])

    def test_generate_with_pretty_format(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(3, len(lines))
            self.assertEqual('''\
- git:
    local-name: %s
    uri: %s\
''' % (self.git, self.uri), '\n'.join(lines))
        self.helper(check_config_entries, {'pretty': True},
                    [PathSpec(self.git, 'git', self.uri)])

    def test_generate_sorted_with_localname(self):
        def check_config_entries(self, lines, uuid):
            self.assertEqual(2, len(lines))
            self.assertEqual('''\
- git: {local-name: git, uri: %s/some/uri2}
- svn: {local-name: ros, uri: %s/some/uri1}\
''' % (self.directory, self.directory), "\n".join(lines[:2]))

        self.helper(check_config_entries, {'sort_with_localname': True},
                    [PathSpec('ros', 'svn', 'some/uri1'),
                     PathSpec('git', 'git', 'some/uri2')])

    def setUp(self):
        self.uri = 'http://some/uri'
        self.version = 'master'
        self.git = 'ros'
        self.git_el = '- git: {{local-name: {0}, uri: \'{1}\', version: %s}}' \
            .format(self.git, self.uri)
        self.other = 'foobar'
        self.other_el = '- other: {local-name: %s}' % self.other
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)


class ConfigElementYamlWrapper_Test(unittest.TestCase):

    def test_original_syntax_scm(self):
        # - hg: {local-name: common_rosdeps, version: common_rosdeps-1.0.2, uri: https://kforge.ros.org/common/rosdepcore}
        local_name = 'common_rosdeps'
        version = 'common_rosdeps-1.0.2'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(scmtype, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual(struct, wrap.get_legacy_yaml())

        # empty version
        local_name = 'common_rosdeps'
        version = None
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(scmtype, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual({scmtype: {'local-name': local_name, 'uri': uri}}, wrap.get_legacy_yaml())

        # no version
        local_name = 'common_rosdeps'
        version = None
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'
        struct = {scmtype: {'local-name': local_name, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(scmtype, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual({'hg': {'local-name': 'common_rosdeps', 'uri': 'https://kforge.ros.org/common/rosdepcore'}}, wrap.get_legacy_yaml())

        # other
        local_name = 'common_rosdeps'
        version = None
        uri = None
        scmtype = 'other'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(None, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual({scmtype: {'local-name': local_name}}, wrap.get_legacy_yaml())

        # properties (undocumented feature required for builds)
        local_name = 'common_rosdeps'
        version = None
        uri = None
        scmtype = 'other'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri,
                            'meta': {'repo-name': 'skynetish-ros-pkg'}}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(None, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual([{'meta': {'repo-name': 'skynetish-ros-pkg'}}], wrap.get_tags())
        self.assertEqual({scmtype: {'local-name': local_name, 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, wrap.get_legacy_yaml())

        # properties (undocumented feature required for builds)
        local_name = 'common_rosdeps'
        version = None
        uri = 'some/uri'
        scmtype = 'git'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri,
                            'meta': {'repo-name': 'skynetish-ros-pkg'}}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual('git', wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual([{'meta': {'repo-name': 'skynetish-ros-pkg'}}], wrap.get_tags())
        self.assertEqual({scmtype: {'local-name': local_name, 'uri': 'some/uri', 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, wrap.get_legacy_yaml())

    def test_original_syntax_invalids(self):
        local_name = 'common_rosdeps'
        version = '1234'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'

        try:
            struct = {}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"hello world": None}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"git": None}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"git": {}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"git": {"uri": uri}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"git": {"local-name": local_name}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"foo": {"foo": None}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"other": {"foo": None}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"other": {"uri": uri}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"other": {"version": version}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass

    def test_original_syntax_setupfile(self):
        local_name = '/opt/ros/fuerte/setup.sh'
        version = None
        uri = None
        scmtype = 'setup-file'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(None, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        version = "1234"
        uri = 'https://kforge.ros.org/common/rosdepcore'
        try:
            struct = {"setup-file": {"uri": uri}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
        try:
            struct = {"setup-file": {"version": version}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException:
            pass
