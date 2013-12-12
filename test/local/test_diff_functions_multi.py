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

import wstool
import wstool.helpers
import wstool.wstool_cli
from wstool.wstool_cli import WstoolCLI
from wstool.wstool_cli import wstool_main

from test.scm_test_base import AbstractSCMTest, _add_to_file

from test.local.test_diff_functions_svn import create_svn_repo, modify_svn_repo
from test.local.test_diff_functions_git import create_git_repo, modify_git_repo
from test.local.test_diff_functions_hg import create_hg_repo, modify_hg_repo
from test.local.test_diff_functions_bzr import create_bzr_repo, modify_bzr_repo


class WstoolDiffMultiTest(AbstractSCMTest):

    @classmethod
    def setUpClass(self):
        AbstractSCMTest.setUpClass()
        remote_path_svn = os.path.join(self.test_root_path, "remote_svn")
        remote_path_git = os.path.join(self.test_root_path, "remote_git")
        remote_path_bzr = os.path.join(self.test_root_path, "remote_bzr")
        remote_path_hg = os.path.join(self.test_root_path, "remote_hg")
        os.makedirs(remote_path_git)
        os.makedirs(remote_path_svn)
        os.makedirs(remote_path_hg)
        os.makedirs(remote_path_bzr)

        filler_path = os.path.join(self.test_root_path, "filler")
        svn_uri = "file://localhost"+remote_path_svn

        create_svn_repo(self.test_root_path, remote_path_svn, filler_path, svn_uri)
        create_git_repo(remote_path_git)
        create_hg_repo(remote_path_hg)
        create_bzr_repo(remote_path_bzr)

        # wstool the remote repo and fake ros (using git twice to check all overlaps)
        rosinstall_spec = """- other: {local-name: ../ros}
- git: {local-name: clone_git, uri: ../remote_git}
- svn: {local-name: clone_svn, uri: '%s'}
- hg: {local-name: clone_hg, uri: ../remote_hg}
- bzr: {local-name: clone_bzr, uri: ../remote_bzr}
- git: {local-name: clone_git2, uri: ../remote_git}""" % svn_uri

        _add_to_file(os.path.join(self.local_path, ".rosinstall"), rosinstall_spec)

        cmd = ["rosws", "update", "-t", "ws"]
        os.chdir(self.test_root_path)
        wstool_main(cmd)

        clone_path_git = os.path.join(self.local_path, "clone_git")
        clone_path_git2 = os.path.join(self.local_path, "clone_git2")
        clone_path_svn = os.path.join(self.local_path, "clone_svn")
        clone_path_hg = os.path.join(self.local_path, "clone_hg")
        clone_path_bzr = os.path.join(self.local_path, "clone_bzr")

        modify_git_repo(clone_path_git2)
        modify_git_repo(clone_path_git)
        modify_svn_repo(clone_path_svn)
        modify_hg_repo(clone_path_hg)
        modify_bzr_repo(clone_path_bzr)

    def check_diff_output(self, output):
        # this tests that there are proper newlines between diff outputs
        # for svn, the order varies, so we check two known variants
        self.assertTrue("\nIndex: clone_svn/added.txt" in output, output)
        self.assertTrue("\nIndex: clone_svn/added.txt" in output, output)
        self.assertTrue("\nIndex: clone_svn/modified.txt" in output, output)
        self.assertTrue("\ndiff --git clone_hg/added.txt" in output, output)
        self.assertTrue("\n=== added file 'added.txt'\n--- clone_bzr/added.txt" in output, output)
        self.assertTrue("\ndiff --git clone_git2/added.txt" in output, output)

    def test_multi_diff_rosinstall_outside(self):
        '''Test wstool diff output from outside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
        cmd = ["wstool", "diff", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.check_diff_output(output)

    def test_multi_diff_wstool_outside(self):
        '''Test wstool diff output from outside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
        cmd = ["wstool", "diff", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.check_diff_output(output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_diff(os.path.join(self.test_root_path, 'ws'), []))

    def test_multi_diff_rosinstall_inside(self):
        '''Test wstool diff output from inside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
        directory = self.test_root_path + "/ws"
        cmd = ["wstool", "diff"]
        os.chdir(directory)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        self.check_diff_output(output)

    def test_multi_diff_wstool_inside(self):
        '''Test wstool diff output from inside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
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

    def test_multi_status_rosinstall_inside(self):
        """Test wstool status output when run inside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        directory = self.test_root_path + "/ws"
        cmd = ["wstool", "status"]
        os.chdir(directory)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()

        self.assertStatusListEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)

    def test_multi_status_wstool_inside(self):
        """Test wstool status output when run inside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        directory = self.test_root_path + "/ws"
        cmd = ["wstool", "status"]
        os.chdir(directory)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__
        self.assertStatusListEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_diff(directory, []))

    def test_multi_status_rosinstall_outside(self):
        """Test wstool status output when run outside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        cmd = ["rosinstall", "status", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertStatusListEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)

    def test_multi_status_wstool_outside(self):
        """Test wstool status output when run outside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        cmd = ["wstool", "status", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertStatusListEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), []))

    def test_multi_status_untracked(self):
        '''tests status output for --untracked.
        In particular asserts that there are newlines between statuses, and no overlaps'''
        cmd = ["wstool", "status", "-t", "ws", "--untracked"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertStatusListEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\n??      clone_git/added-fs.txt\n?       clone_svn/added-fs.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n?       clone_hg/added-fs.txt\n?       clone_bzr/added-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n??      clone_git2/added-fs.txt\n', output)

        cmd = ["wstool", "status", "-t", "ws", "--untracked"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO()
        wstool_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertStatusListEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\n??      clone_git/added-fs.txt\n?       clone_svn/added-fs.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n?       clone_hg/added-fs.txt\n?       clone_bzr/added-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n??      clone_git2/added-fs.txt\n', output)

        cli = WstoolCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), ["--untracked"]))
