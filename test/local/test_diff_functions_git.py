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
import subprocess

from test.io_wrapper import StringIO

import wstool
import wstool.helpers
import wstool.wstool_cli
from wstool.wstool_cli import WstoolCLI
from wstool.wstool_cli import wstool_main

import test.scm_test_base
from test.scm_test_base import AbstractSCMTest, _add_to_file, _nth_line_split


def create_git_repo(remote_path):
    # create a "remote" repo
    subprocess.check_call(["git", "init"], cwd=remote_path)
    subprocess.check_call(["touch", "fixed.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "modified.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "modified-fs.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "deleted.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "deleted-fs.txt"], cwd=remote_path)
    subprocess.check_call(["git", "add", "*"], cwd=remote_path)
    subprocess.check_call(["git", "commit", "-m", "modified"], cwd=remote_path)


def modify_git_repo(clone_path):
    # make local modifications
    subprocess.check_call(["rm", "deleted-fs.txt"], cwd=clone_path)
    subprocess.check_call(["git", "rm", "deleted.txt"], cwd=clone_path)
    _add_to_file(os.path.join(clone_path, "modified-fs.txt"), "foo\n")
    _add_to_file(os.path.join(clone_path, "modified.txt"), "foo\n")
    subprocess.check_call(["git", "add", "modified.txt"], cwd=clone_path)
    _add_to_file(os.path.join(clone_path, "added-fs.txt"), "tada\n")
    _add_to_file(os.path.join(clone_path, "added.txt"), "flam\n")
    subprocess.check_call(["git", "add", "added.txt"], cwd=clone_path)


class WstoolDiffGitTest(AbstractSCMTest):

    @classmethod
    def setUpClass(self):
        AbstractSCMTest.setUpClass()
        remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(remote_path)

        create_git_repo(remote_path)

        # wstool the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- git: {local-name: clone, uri: ../remote}")

        cmd = ["wstool", "update", "-t", "ws"]
        os.chdir(self.test_root_path)
        wstool_main(cmd)

        clone_path = os.path.join(self.local_path, "clone")

        modify_git_repo(clone_path)

    def check_diff_output(self, output):
        # sha ids are always same with git
        self.assertEqual('diff --git clone/added.txt clone/added.txt\nnew file mode 100644\nindex 0000000..8d63207\n--- /dev/null\n+++ clone/added.txt\n@@ -0,0 +1 @@\n+flam\ndiff --git clone/deleted-fs.txt clone/deleted-fs.txt\ndeleted file mode 100644\nindex e69de29..0000000\ndiff --git clone/deleted.txt clone/deleted.txt\ndeleted file mode 100644\nindex e69de29..0000000\ndiff --git clone/modified-fs.txt clone/modified-fs.txt\nindex e69de29..257cc56 100644\n--- clone/modified-fs.txt\n+++ clone/modified-fs.txt\n@@ -0,0 +1 @@\n+foo\ndiff --git clone/modified.txt clone/modified.txt\nindex e69de29..257cc56 100644\n--- clone/modified.txt\n+++ clone/modified.txt\n@@ -0,0 +1 @@\n+foo', output.rstrip())

    def test_wstool_diff_git_outside(self):
        """Test diff output for git when run outside workspace"""

        cmd = ["wstool", "diff", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.check_diff_output(output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_diff(os.path.join(self.test_root_path, 'ws'), []))

    def test_wstool_diff_git_inside(self):
        """Test diff output for git when run inside workspace"""
        directory = self.test_root_path + "/ws"
        cmd = ["wstool", "diff"]
        os.chdir(directory)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__
        self.check_diff_output(output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_diff(directory, []))

    def test_wstool_status_git_inside(self):
        """Test status output for git when run inside workspace"""
        directory = self.test_root_path + "/ws"

        cmd = ["wstool", "status"]
        os.chdir(directory)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__
        self.assertEqual('A       clone/added.txt\n D      clone/deleted-fs.txt\nD       clone/deleted.txt\n M      clone/modified-fs.txt\nM       clone/modified.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_diff(directory, []))

    def test_Wstool_status_git_outside(self):
        """Test status output for git when run outside workspace"""

        cmd = ["wstool", "status", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('A       clone/added.txt\n D      clone/deleted-fs.txt\nD       clone/deleted.txt\n M      clone/modified-fs.txt\nM       clone/modified.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), []))

    def test_Wstool_status_git_untracked(self):
        """Test untracked status output for git when run outside workspace"""

        cmd = ["wstool", "status", "-t", "ws", "--untracked"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('A       clone/added.txt\n D      clone/deleted-fs.txt\nD       clone/deleted.txt\n M      clone/modified-fs.txt\nM       clone/modified.txt\n??      clone/added-fs.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), ["--untracked"]))

    def test_wstool_info_git(self):
        cmd = ["wstool", "info", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'M', 'git'], tokens[0:3])
        tokens2 = _nth_line_split(-1, output)
        self.assertEqual(1, len(tokens2))
        self.assertEqual('../ros', tokens2[0])

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_info(os.path.join(self.test_root_path, 'ws'), []))


class WstoolInfoGitTest(AbstractSCMTest):

    def setUp(self):
        AbstractSCMTest.setUp(self)
        self.remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(self.remote_path)

        # create a "remote" repo
        subprocess.check_call(["git", "init"], cwd=self.remote_path)
        subprocess.check_call(["touch", "test.txt"], cwd=self.remote_path)
        subprocess.check_call(["git", "add", "*"], cwd=self.remote_path)
        subprocess.check_call(["git", "commit", "-m", "modified"], cwd=self.remote_path)
        po = subprocess.Popen(["git", "log", "-n", "1", "--pretty=format:\"%H\""], cwd=self.remote_path, stdout=subprocess.PIPE)
        self.version_init = po.stdout.read().decode('UTF-8').rstrip('"').lstrip('"')[0:12]
        subprocess.check_call(["git", "tag", "footag"], cwd=self.remote_path)
        subprocess.check_call(["touch", "test2.txt"], cwd=self.remote_path)
        subprocess.check_call(["git", "add", "*"], cwd=self.remote_path)
        subprocess.check_call(["git", "commit", "-m", "modified"], cwd=self.remote_path)
        po = subprocess.Popen(["git", "log", "-n", "1", "--pretty=format:\"%H\""], cwd=self.remote_path, stdout=subprocess.PIPE)
        self.version_end = po.stdout.read().decode('UTF-8').rstrip('"').lstrip('"')[0:12]

        # wstool the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- git: {local-name: clone, uri: ../remote}")
        self.clone_path = os.path.join(self.local_path, "clone")

        cmd = ["wstool", "update"]
        os.chdir(self.local_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__

    def test_wstool_detailed_localpath_info(self):
        cmd = ["wstool", "info", "-t", "ws", "--managed-only"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'git', 'master', '(-)', self.version_end, self.remote_path], tokens)

        # test when remote version is different
        subprocess.check_call(["git", "reset", "--hard", "HEAD~1"], cwd=self.clone_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'C', 'git', 'master', '(-)', self.version_init, self.remote_path], tokens)
        # return branch back to original revision
        subprocess.check_call(["git", "reset", "--hard", self.version_end], cwd=self.clone_path)

        # make local modifications check
        subprocess.check_call(["rm", "test2.txt"], cwd=self.clone_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'M', 'git', 'master', '(-)', self.version_end, self.remote_path], tokens)

        subprocess.check_call(["rm", ".rosinstall"], cwd=self.local_path)
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- git: {local-name: clone, uri: ../remote, version: \"footag\"}")
        # test when version is different
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'MV', 'git', 'master', '(footag)', self.version_end, "(%s)" % self.version_init, self.remote_path], tokens)
        # test when tracking branch is different from current branch
        subprocess.check_call(["git", "checkout", "-b", "test_branch"], cwd=self.clone_path)
        subprocess.check_call(["git", "config", "--replace-all", "branch.test_branch.remote", "origin"], cwd=self.clone_path)
        subprocess.check_call(["git", "config", "--replace-all", "branch.test_branch.merge", "master"], cwd=self.clone_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'MV', 'git', 'test_branch', '<', 'master', '(footag)', self.version_end, "(%s)" % self.version_init, self.remote_path], tokens)

        # test when remote is different from origin by rename
        subprocess.check_call(["git", "remote", "rename", "origin", "remote2"], cwd=self.clone_path)
        subprocess.check_call(["git", "config", "--replace-all", "branch.test_branch.remote", "remote2"], cwd=self.clone_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'MV', 'git', 'test_branch', '<', 'remote2/master', '(footag)', self.version_end, "(%s)" % self.version_init, "(%s)" % self.remote_path], tokens)
        # return remote name to origin
        subprocess.check_call(["git", "remote", "rename", "remote2", "origin"], cwd=self.clone_path)

        # test when remote is different from origin, no fetch
        subprocess.check_call(["git", "remote", "add", "remote2", "../../remote"], cwd=self.clone_path)
        subprocess.check_call(["git", "config", "--replace-all", "branch.test_branch.remote", "remote2"], cwd=self.clone_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'MV', 'git', 'test_branch', '(footag)', self.version_end, "(%s)" % self.version_init, self.remote_path], tokens)


        # test when remote is different from origin, with fetch
        sys.stdout = output = StringIO()
        wstool_main(cmd + ['--fetch'])
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'MV', 'git', 'test_branch', '<', 'remote2/master', '(footag)', self.version_end, "(%s)" % self.version_init, self.remote_path], tokens)


        # return branch back to master
        subprocess.check_call(["git", "checkout", "master"], cwd=self.clone_path)

        # using a denormalized local-name here
        subprocess.check_call(["rm", ".rosinstall"], cwd=self.local_path)
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- git: {local-name: clone/../clone, uri: ../remote, version: \"footag\"}")
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'MV', 'git', 'master', '(footag)', self.version_end, "(%s)" %
                         self.version_init, self.remote_path], tokens)

        # using an absolute path to clone dir here
        subprocess.check_call(["rm", ".rosinstall"], cwd=self.local_path)
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- git: {local-name: '"+self.clone_path+"', uri: ../remote, version: \"footag\"}")
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual([self.clone_path, 'MV', 'git', 'master', '(footag)', self.version_end, "(%s)" % self.version_init, self.remote_path], tokens)

        # using an absolute path here where relative path is shorter to display (also checks x for missing)
        subprocess.check_call(["rm", ".rosinstall"], cwd=self.local_path)
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- git: {local-name: '"+os.path.join(self.local_path, "../foo")+"', uri: ../remote, version: \"footag\"}")
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        localname = os.path.join(os.path.dirname(self.local_path), 'foo')
        self.assertEqual([localname, 'x', 'git', '(footag)', self.remote_path], tokens)
