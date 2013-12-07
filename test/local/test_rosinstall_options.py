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
import copy
import tempfile

import rosinstall
from rosinstall.rosinstall_cli import rosinstall_main
from rosinstall.common import MultiProjectException

from test.scm_test_base import AbstractFakeRosBasedTest, _create_yaml_file, _create_config_elt_dict, _create_git_repo


class RosinstallOptionsTest(AbstractFakeRosBasedTest):
    """Test command line option for failure behavior"""

    @classmethod
    def setUpClass(self):
        AbstractFakeRosBasedTest.setUpClass()

        # create another repo in git
        self.git_path2 = os.path.join(self.test_root_path, "gitrepo2")
        _create_git_repo(self.git_path2)
        self.simple_changed_uri_rosinstall = os.path.join(self.test_root_path, "simple_changed_uri.rosinstall")
        # same local name for gitrepo, different uri
        _create_yaml_file([_create_config_elt_dict("git", "ros", self.ros_path),
                           _create_config_elt_dict("git", "gitrepo", self.git_path2)],
                          self.simple_changed_uri_rosinstall)

        # create a broken config
        self.broken_rosinstall = os.path.join(self.test_root_path, "broken.rosinstall")
        _create_yaml_file([_create_config_elt_dict("other", self.ros_path),
                           _create_config_elt_dict("hg", "hgrepo", self.hg_path + "invalid")],
                          self.broken_rosinstall)

    def test_Rosinstall_help(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.append("-h")
        try:
            rosinstall_main(cmd)
            self.fail("expected SystemExit")
        except SystemExit as e:
            self.assertEqual(0, e.code)

    def test_rosinstall_delete_changes(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertTrue(rosinstall_main(cmd))
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_changed_uri_rosinstall, "--delete-changed-uri"])
        self.assertTrue(rosinstall_main(cmd))

    def test_rosinstall_abort_changes(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertTrue(rosinstall_main(cmd))
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_changed_uri_rosinstall, "--abort-changed-uri", "-n"])
        try:
            rosinstall_main(cmd)
            self.fail("expected exception")
        except MultiProjectException:
            pass

    def test_rosinstall_backup_changes(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertTrue(rosinstall_main(cmd))
        directory1 = tempfile.mkdtemp()
        self.directories["backup1"] = directory1
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_changed_uri_rosinstall, "--backup-changed-uri=%s" % directory1])
        self.assertTrue(rosinstall_main(cmd))
        self.assertEqual(len(os.listdir(directory1)), 1)

    def test_rosinstall_change_vcs_type(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertTrue(rosinstall_main(cmd))
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_changed_vcs_rosinstall, "--delete-changed-uri", "-n"])
        self.assertTrue(rosinstall_main(cmd))

    def test_rosinstall_invalid_fail(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.broken_rosinstall])
        try:
            rosinstall_main(cmd)
            self.fail("expected exception")
        except MultiProjectException:
            pass

    def test_rosinstall_invalid_continue(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.broken_rosinstall, "--continue-on-error"])
        self.assertTrue(rosinstall_main(cmd))
