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

from __future__ import unicode_literals

import os
import copy
import unittest
import subprocess
import tempfile
import shutil


def _add_to_file(path, content):
    """Util function to append to file to get a modification"""
    with open(path, 'ab') as fhand:
        fhand.write(content.encode('UTF-8'))


def _create_fake_ros_dir(root_path):
    """setup fake ros root within root_path/ros"""
    ros_path = os.path.join(root_path, "ros")
    os.makedirs(ros_path)
    bin_path = os.path.join(ros_path, "bin")
    os.makedirs(bin_path)
    subprocess.check_call(["git", "init"], cwd=ros_path)
    _add_to_file(os.path.join(ros_path, "stack.xml"), '<stack></stack>')
    _add_to_file(os.path.join(ros_path, "setup.sh"), 'export FOO_BAR=`pwd`')
    _add_to_file(os.path.join(bin_path, "rosmake"), '#!/usr/bin/env sh')
    _add_to_file(os.path.join(bin_path, "rospack"), '#!/usr/bin/env sh')
    # even faking rosmake
    subprocess.check_call(["chmod", "u+x", os.path.join(bin_path, "rosmake")])
    subprocess.check_call(["chmod", "u+x", os.path.join(bin_path, "rospack")])
    subprocess.check_call(["git", "add", "*"], cwd=ros_path)
    subprocess.check_call(["git", "commit", "-m", "initial"], cwd=ros_path)


def _create_yaml_file(config_elements, path):
    content = ''
    for elt in list(config_elements):
        content += "- %s:\n" % elt["type"]
        if elt["uri"] is not None:
            content += "    uri: '%s'\n" % elt["uri"]
        content += "    local-name: '%s'\n" % elt["local-name"]
        if elt["version"] is not None:
            content += "    version: '%s'\n" % elt["version"]
    _add_to_file(path, content)


def _create_config_elt_dict(scmtype, localname, uri=None, version=None):
    element = {}
    element["type"]       = scmtype
    element["uri"]        = uri
    element["local-name"] = localname
    element["version"]    = version
    return element


def _create_git_repo(git_path):
    os.makedirs(git_path)
    subprocess.check_call(["git", "init"], cwd=git_path)
    subprocess.check_call(["touch", "gitfixed.txt"], cwd=git_path)
    subprocess.check_call(["git", "add", "*"], cwd=git_path)
    subprocess.check_call(["git", "commit", "-m", "initial"], cwd=git_path)


def _create_tar_file(tar_file):
    parent_path = os.path.dirname(tar_file)
    tar_path = os.path.join(parent_path, 'temptar')
    os.makedirs(tar_path)
    subprocess.check_call(["touch", "tarfixed.txt"], cwd=tar_path)
    subprocess.check_call(["tar", "-czf", os.path.basename(tar_file), 'temptar'], cwd=parent_path)


def _create_hg_repo(hg_path):
    os.makedirs(hg_path)
    subprocess.check_call(["hg", "init"], cwd=hg_path)
    subprocess.check_call(["touch", "hgfixed.txt"], cwd=hg_path)
    subprocess.check_call(["hg", "add", "hgfixed.txt"], cwd=hg_path)
    subprocess.check_call(["hg", "commit", "-m", "initial"], cwd=hg_path)


def _nth_line_split(n, output):
    """returns the last line as list of non-blank tokens"""
    lines = output.splitlines()
    if len(lines) > 0:
        return lines[n].split()
    else:
        return []


def get_git_hash(git_path):
    po = subprocess.Popen(["git", "rev-parse", "HEAD"], cwd=git_path,
                          stdout=subprocess.PIPE)
    return po.stdout.read().decode('UTF-8').rstrip('"\n').lstrip('"\n')


# ROSINSTALL_CMD = os.path.join(os.getcwd(), 'scripts/rosinstall')
# ROSWS_CMD = os.path.join(os.getcwd(), 'scripts/rosws')


class AbstractRosinstallCLITest(unittest.TestCase):

    """Base class for cli tests"""
    @classmethod
    def setUpClass(self):
        os.environ['GIT_AUTHOR_NAME'] = 'Your Name'
        os.environ['GIT_COMMITTER_NAME'] = 'Your Name'
        os.environ['GIT_AUTHOR_EMAIL'] = 'name@example.com'
        os.environ['EMAIL'] = 'Your Name <name@example.com>'
        self.new_environ = copy.copy(os.environ)
        self.new_environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
        if "ROS_WORKSPACE" in self.new_environ:
            self.new_environ.pop("ROS_WORKSPACE")


class AbstractRosinstallBaseDirTest(AbstractRosinstallCLITest):
    """test class where each test method get its own fresh tempdir named self.directory"""

    def setUp(self):
        self.directories = {}
        self.directory = tempfile.mkdtemp()
        self.directories["base"] = self.directory
        self.wstool_fn = ["wstool"]

    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        self.directories = {}


class AbstractFakeRosBasedTest(AbstractRosinstallBaseDirTest):
    """
    creates some larger infrastructure for testing locally:
    a root folder containing all other folders in self.test_root_path
    a fake ros folder in self.ros_path
    a git repo in self.git_path
    a hg repo in self.hg_path
    a file named self.simple_rosinstall with ros and gitrepo
    a file named self.simple_changed_vcs_rosinstall with ros and hgrepo
    """

    @classmethod
    def setUpClass(self):
        AbstractRosinstallBaseDirTest.setUpClass()
        # create a dir mimicking ros
        self.test_root_path = os.path.realpath(tempfile.mkdtemp())
        _create_fake_ros_dir(self.test_root_path)
        # create a repo in git
        self.ros_path = os.path.join(self.test_root_path, "ros")
        self.git_path = os.path.join(self.test_root_path, "gitrepo")
        _create_git_repo(self.git_path)
        # create a repo in hg
        self.hg_path = os.path.join(self.test_root_path, "hgrepo")
        _create_hg_repo(self.hg_path)
        # create custom wstool files to use as input
        self.simple_rosinstall = os.path.join(self.test_root_path, "simple.rosinstall")
        _create_yaml_file([_create_config_elt_dict("git", "ros", self.ros_path),
                           _create_config_elt_dict("git", "gitrepo", self.git_path)],
                          self.simple_rosinstall)
        self.simple_changed_vcs_rosinstall = os.path.join(self.test_root_path, "simple_changed_vcs.rosinstall")
        _create_yaml_file([_create_config_elt_dict("git", "ros", self.ros_path),
                           _create_config_elt_dict("hg", "hgrepo", self.hg_path)],
                          self.simple_changed_vcs_rosinstall)

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.test_root_path)


class AbstractSCMTest(AbstractRosinstallCLITest):
    """Base class for diff tests, setting up a tempdir self.test_root_path for a whole class"""
    @classmethod
    def setUpClass(self):
        """creates a directory 'ros' mimicking to be a ROS root to rosinstall"""
        AbstractRosinstallCLITest.setUpClass()
        self.test_root_path = os.path.realpath(tempfile.mkdtemp())
        self.directories = {}
        self.directories["root"] = self.test_root_path

        _create_fake_ros_dir(self.test_root_path)
        self.local_path = os.path.join(self.test_root_path, "ws")
        os.makedirs(self.local_path)
        self.curdir = os.getcwd()

    @classmethod
    def tearDownClass(self):
        os.chdir(self.curdir)
        for d in self.directories:
            shutil.rmtree(self.directories[d])

    def assertStatusListEqual(self, listexpect, listactual):
        """helper fun to check scm status output while discarding file ordering differences"""
        lines_expect = listexpect.splitlines()
        lines_actual = listactual.splitlines()
        for line in lines_expect:
            self.assertTrue(line in lines_actual, 'Missing entry %s in output %s' % (line, listactual))
        for line in lines_actual:
            self.assertTrue(line in lines_expect, 'Superflous entry %s in output %s' % (line, listactual))


class UtilTest(unittest.TestCase):
    """test to check the methods run by unit test setups"""

    def test_add_to_file(self):
        self.test_root_path = tempfile.mkdtemp()
        filepath = os.path.join(self.test_root_path, 'foofile')
        self.assertFalse(os.path.exists(filepath))
        _add_to_file(filepath, 'foo')
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            read_data = f.read()
            self.assertEqual(read_data, 'foo')
        _add_to_file(filepath, 'bar')
        with open(filepath, 'r') as f:
            read_data = f.read()
            self.assertEqual(read_data, 'foobar')
        shutil.rmtree(self.test_root_path)

    def test_create_fake_ros(self):
        self.test_root_path = tempfile.mkdtemp()
        rospath = os.path.join(self.test_root_path, 'ros')
        self.assertFalse(os.path.exists(rospath))
        _create_fake_ros_dir(self.test_root_path)
        self.assertTrue(os.path.exists(rospath))
        self.assertTrue(os.path.exists(os.path.join(rospath, "setup.sh")))
        self.assertTrue(os.path.exists(os.path.join(rospath, "stack.xml")))
        self.assertTrue(os.path.exists(os.path.join(rospath, ".git")))
        shutil.rmtree(self.test_root_path)

    def test_create_config_elt_dict(self):
        scmtype = 'foo'
        uri = 'bar'
        localname = 'pip'
        version = 'pop'
        element = _create_config_elt_dict(scmtype, localname, uri, version)
        self.assertEqual(element["type"], scmtype)
        self.assertEqual(element["uri"], uri)
        self.assertEqual(element["local-name"], localname)
        self.assertEqual(element["version"], version)

    def test_create_yaml_file(self):
        self.test_root_path = tempfile.mkdtemp()
        filepath = os.path.join(self.test_root_path, 'foofile')
        config_elements = [
            _create_config_elt_dict("other", "foo"),
            _create_config_elt_dict("git", "foo", "foouri"),
            _create_config_elt_dict("svn", "bar", "baruri", "barversion")]
        _create_yaml_file(config_elements, filepath)
        with open(filepath, 'r') as f:
            read_data = f.read()
            self.assertEqual(read_data, """- other:
    local-name: 'foo'
- git:
    uri: 'foouri'
    local-name: 'foo'
- svn:
    uri: 'baruri'
    local-name: 'bar'
    version: 'barversion'
""")
        shutil.rmtree(self.test_root_path)
