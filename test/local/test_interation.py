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

import wstool
import wstool.multiproject_cmd
import wstool.ui


from test.scm_test_base import AbstractFakeRosBasedTest, _create_yaml_file, _create_config_elt_dict


class FakeUi(wstool.ui.Ui):
    def __init__(self, path='', mode='skip', prompt_result='y'):
        self.path = path
        self.mode = mode

    def get_backup_path(self):
        return path

    def prompt_del_abort_retry(self, prompt, allow_skip=False):
        return mode

    def get_input(self, prompt):
        return prompt_result


class RosinstallInteractive(AbstractFakeRosBasedTest):
    """tests with possible User Interaction, using mock to simulate user input"""

    def setUp(self):
        self.old_ui = wstool.ui.Ui.get_ui()
        wstool.ui.Ui.set_ui(FakeUi())

    def tearDown(self):
        wstool.ui.Ui.set_ui(self.old_ui)

    def test_twice_with_relpath(self):
        """runs wstool with generated self.simple_rosinstall to create local wstool env
        and creates a directory for a second local wstool env"""
        AbstractFakeRosBasedTest.setUp(self)

        self.rel_uri_rosinstall = os.path.join(self.test_root_path, "rel_uri.rosinstall")
        _create_yaml_file([_create_config_elt_dict("git", "ros", self.ros_path),
                           _create_config_elt_dict("git", "gitrepo", os.path.relpath(self.git_path, self.directory))],
                          self.rel_uri_rosinstall)

        config = wstool.multiproject_cmd.get_config(self.directory, [self.rel_uri_rosinstall, self.ros_path])
        wstool.multiproject_cmd.cmd_info(config)
        wstool.multiproject_cmd.cmd_find_unmanaged_repos
        wstool.multiproject_cmd.cmd_install_or_update(config)

        config = wstool.multiproject_cmd.get_config(self.directory, [self.rel_uri_rosinstall, self.ros_path])
        wstool.multiproject_cmd.cmd_install_or_update(config)

        self.rel_uri_rosinstall2 = os.path.join(self.test_root_path, "rel_uri.wstool2")
        # switch URIs to confuse config
        _create_yaml_file([_create_config_elt_dict("git", "ros", os.path.relpath(self.git_path, self.directory)),
                           _create_config_elt_dict("git", "gitrepo", self.ros_path)],
                          self.rel_uri_rosinstall2)

        config = wstool.multiproject_cmd.get_config(self.directory, [self.rel_uri_rosinstall, self.ros_path])
        wstool.multiproject_cmd.cmd_install_or_update(config)
