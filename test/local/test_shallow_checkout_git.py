# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# Copyright (c) 2017, wstool authors
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
import subprocess

from wstool.wstool_cli import wstool_main

from test.scm_test_base import AbstractSCMTest, _add_to_file


def create_git_repo(remote_path):
    # create a "remote" repo
    subprocess.check_call(["git", "init"], cwd=remote_path)
    subprocess.check_call(["touch", "1.txt"], cwd=remote_path)
    subprocess.check_call(["git", "add", "."], cwd=remote_path)
    subprocess.check_call(["git", "commit", "-m", "first commit"], cwd=remote_path)
    subprocess.check_call(["touch", "2.txt"], cwd=remote_path)
    subprocess.check_call(["git", "add", "."], cwd=remote_path)
    subprocess.check_call(["git", "commit", "-m", "second commit"], cwd=remote_path)
    subprocess.check_call(["touch", "3.txt"], cwd=remote_path)
    subprocess.check_call(["git", "add", "."], cwd=remote_path)
    subprocess.check_call(["git", "commit", "-m", "third commit"], cwd=remote_path)


class WstoolShallowCheckoutGitTest(AbstractSCMTest):

    @classmethod
    def setUpClass(self):
        AbstractSCMTest.setUpClass()
        remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(remote_path)

        create_git_repo(remote_path)

        self.rosinstall_filename = os.path.join(self.local_path, "shallow-test.rosinstall")
        _add_to_file(self.rosinstall_filename, "- git: {local-name: clone, uri: \"file://" + remote_path + "\"}")

        cmd = ["wstool", "init", "ws-without-shallow", self.rosinstall_filename]
        os.chdir(self.test_root_path)
        wstool_main(cmd)

        cmd = ["wstool", "init", "--shallow", "ws-with-shallow", self.rosinstall_filename]
        os.chdir(self.test_root_path)
        wstool_main(cmd)

    def test_history_without_shallow(self):
        """Test history of cloned repo without shallow option"""

        clone_path = os.path.join(self.test_root_path, "ws-without-shallow", "clone")

        output = subprocess.check_output(["git", "log", "--pretty=format:%s"], cwd=clone_path)
        self.assertEqual(output.decode("ascii"), "third commit\nsecond commit\nfirst commit")

    def test_history_with_shallow(self):
        """Test history of cloned repo with shallow option"""

        clone_path = os.path.join(self.test_root_path, "ws-with-shallow", "clone")

        output = subprocess.check_output(["git", "log", "--pretty=format:%s"], cwd=clone_path)
        self.assertEqual(output.decode("ascii"), "third commit")

    def test_compare_workspace(self):
        """Compare worktrees with/without shallow option"""

        clone_path_without_shallow = os.path.join(self.test_root_path, "ws-without-shallow", "clone")
        clone_path_with_shallow = os.path.join(self.test_root_path, "ws-with-shallow", "clone")

        output = subprocess.check_output(["diff", "--exclude=.git", clone_path_without_shallow, clone_path_with_shallow], cwd=self.test_root_path)
        self.assertEqual(output.decode("ascii"), "")
