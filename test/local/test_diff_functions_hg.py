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
import sys
from test.io_wrapper import StringIO
import subprocess

import wstool
import wstool.helpers
import wstool.wstool_cli
from wstool.wstool_cli import WstoolCLI
from wstool.wstool_cli import wstool_main

import test.scm_test_base
from test.scm_test_base import AbstractSCMTest, _add_to_file, _nth_line_split


def create_hg_repo(remote_path):
    # create a "remote" repo
    subprocess.check_call(["hg", "init"], cwd=remote_path)
    subprocess.check_call(["touch", "fixed.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "modified.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "modified-fs.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "deleted.txt"], cwd=remote_path)
    subprocess.check_call(["touch", "deleted-fs.txt"], cwd=remote_path)
    subprocess.check_call(["hg", "add", "fixed.txt"], cwd=remote_path)
    subprocess.check_call(["hg", "add", "modified.txt"], cwd=remote_path)
    subprocess.check_call(["hg", "add", "modified-fs.txt"], cwd=remote_path)
    subprocess.check_call(["hg", "add", "deleted.txt"], cwd=remote_path)
    subprocess.check_call(["hg", "add", "deleted-fs.txt"], cwd=remote_path)
    subprocess.check_call(["hg", "commit", "-m", "modified"], cwd=remote_path)


def modify_hg_repo(clone_path):
    # make local modifications
    subprocess.check_call(["rm", "deleted-fs.txt"], cwd=clone_path)
    subprocess.check_call(["hg", "rm", "deleted.txt"], cwd=clone_path)
    _add_to_file(os.path.join(clone_path, "modified-fs.txt"), "foo\n")
    _add_to_file(os.path.join(clone_path, "modified.txt"), "foo\n")
    _add_to_file(os.path.join(clone_path, "added-fs.txt"), "tada\n")
    _add_to_file(os.path.join(clone_path, "added.txt"), "flam\n")
    subprocess.check_call(["hg", "add", "added.txt"], cwd=clone_path)


class WstoolDiffHgTest(AbstractSCMTest):

    @classmethod
    def setUpClass(self):
        AbstractSCMTest.setUpClass()
        remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(remote_path)

        create_hg_repo(remote_path)

        # wstool the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- hg: {local-name: clone, uri: ../remote}")

        cmd = ["wstool", "update", "-t", "ws"]
        os.chdir(self.test_root_path)
        wstool_main(cmd)

        clone_path = os.path.join(self.local_path, "clone")

        modify_hg_repo(clone_path)

    def check_diff_output(self, output):
        # sha ids are always same with hg
        self.assertEqual('diff --git clone/added.txt clone/added.txt\nnew file mode 100644\n--- /dev/null\n+++ clone/added.txt\n@@ -0,0 +1,1 @@\n+flam\ndiff --git clone/deleted.txt clone/deleted.txt\ndeleted file mode 100644\ndiff --git clone/modified-fs.txt clone/modified-fs.txt\n--- clone/modified-fs.txt\n+++ clone/modified-fs.txt\n@@ -0,0 +1,1 @@\n+foo\ndiff --git clone/modified.txt clone/modified.txt\n--- clone/modified.txt\n+++ clone/modified.txt\n@@ -0,0 +1,1 @@\n+foo\n', output)

    def test_wstool_diff_hg_outside(self):
        """Test diff output for hg when run outside workspace"""

        cmd = ["wstool", "diff", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.check_diff_output(output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_diff(os.path.join(self.test_root_path, 'ws'), []))

    def test_wstool_diff_hg_inside(self):
        """Test diff output for hg when run inside workspace"""
        directory = self.test_root_path + "/ws"

        cmd = ["wstool", "diff"]
        os.chdir(directory)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__
        self.check_diff_output(output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_status(directory, []))

    def test_wstool_status_hg_inside(self):
        """Test status output for hg when run inside workspace"""
        directory = self.test_root_path + "/ws"

        cmd = ["wstool", "status"]
        os.chdir(directory)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__
        self.assertEqual('M       clone/modified-fs.txt\nM       clone/modified.txt\nA       clone/added.txt\nR       clone/deleted.txt\n!       clone/deleted-fs.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_diff(directory, []))

    def test_wstool_status_hg_outside(self):
        """Test status output for hg when run outside workspace"""

        cmd = ["wstool", "status", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('M       clone/modified-fs.txt\nM       clone/modified.txt\nA       clone/added.txt\nR       clone/deleted.txt\n!       clone/deleted-fs.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), []))

    def test_wstool_status_hg_untracked(self):
        """Test untracked status output for hg when run outside workspace"""
        cmd = ["wstool", "status", "-t", "ws", "--untracked"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('M       clone/modified-fs.txt\nM       clone/modified.txt\nA       clone/added.txt\nR       clone/deleted.txt\n!       clone/deleted-fs.txt\n?       clone/added-fs.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), ["--untracked"]))

    def test_wstool_info_hg(self):
        cmd = ["wstool", "info", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'M', 'hg'], tokens[0:3], output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_info(os.path.join(self.test_root_path, 'ws'), []))


class WstoolInfoHgTest(AbstractSCMTest):

    def setUp(self):
        AbstractSCMTest.setUp(self)
        remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(remote_path)

        # create a "remote" repo
        subprocess.check_call(["hg", "init"], cwd=remote_path)
        subprocess.check_call(["touch", "test.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "test.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "commit", "-m", "modified"], cwd=remote_path)
        po = subprocess.Popen(["hg", "log", "--template", "'{node|short}'", "-l1"], cwd=remote_path, stdout=subprocess.PIPE)
        self.version_init = po.stdout.read().decode('UTF-8').rstrip("'").lstrip("'")
        subprocess.check_call(["hg", "tag", "footag"], cwd=remote_path)
        subprocess.check_call(["touch", "test2.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "test2.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "commit", "-m", "modified"], cwd=remote_path)
        po = subprocess.Popen(["hg", "log", "--template", "'{node|short}'", "-l1"], cwd=remote_path, stdout=subprocess.PIPE)
        self.version_end = po.stdout.read().decode('UTF-8').rstrip("'").lstrip("'")

        # wstool the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- hg: {local-name: clone, uri: ../remote}")

        cmd = ["wstool", "update"]
        os.chdir(self.local_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__

    def test_rosinstall_detailed_locapath_info(self):
        cmd = ["wstool", "info", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'hg', 'default', '(-)', self.version_end, os.path.join(self.test_root_path, 'remote')], tokens)

        clone_path = os.path.join(self.local_path, "clone")
        # make local modifications check
        subprocess.check_call(["hg", "rm", "test2.txt"], cwd=clone_path)
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'M', 'hg', 'default', '(-)', self.version_end, os.path.join(self.test_root_path, 'remote')], tokens)

        subprocess.check_call(["rm", ".rosinstall"], cwd=self.local_path)
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), "- other: {local-name: ../ros}\n- hg: {local-name: clone, uri: ../remote, version: \"footag\"}")
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'MV', 'hg', 'default', '(footag)', self.version_end, "(%s)" % self.version_init, os.path.join(self.test_root_path, 'remote')], tokens)

        subprocess.check_call(["rm", "-rf", "clone"], cwd=self.local_path)
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        tokens = _nth_line_split(-2, output)
        self.assertEqual(['clone', 'x', 'hg', '(footag)', os.path.join(self.test_root_path, 'remote')], tokens)
