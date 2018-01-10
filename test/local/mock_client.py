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


class MockVcsClient():
    """
    Mocked vcs client. TODO: we should be using pathon magic mock instead.
    """


class MockVcsClient():

    def __init__(self,
                 scmtype='mocktype',
                 path_exists=False,
                 checkout_success=True,
                 update_success=True,
                 vcs_presence=False,
                 url="mockurl",
                 actualversion=None,
                 specversion=None,
                 remoteversion=None):
        self.scmtype = scmtype
        self.path_exists_flag = path_exists
        self.checkout_success = checkout_success
        self.update_success = update_success
        self.vcs_presence = vcs_presence
        self.mockurl = url
        self.checkedout = vcs_presence
        self.updated = False
        self.actualversion = actualversion
        self.specversion = specversion
        self.remoteversion = remoteversion

    def get_vcs_type_name(self):
        return self.scmtype

    def get_diff(self, basepath=None):
        return self.scmtype + "mockdiff%s" % basepath

    def get_version(self, revision=None):
        if revision == None:
            return self.actualversion
        else:
            return self.specversion

    def get_remote_version(self, fetch=False):
        return self.remoteversion

    def get_current_version_label(self):
        return self.scmtype + "mockcurrentversionlabel"

    def get_status(self, basepath=None, untracked=False):
        return self.scmtype + " mockstatus%s,%s" % (basepath, untracked)

    def path_exists(self):
        return self.path_exists_flag

    def checkout(self, uri=None, version=None, verbose=False, timeout=None, shallow=False):
        self.checkedout = True
        return self.checkout_success

    def update(self, version, verbose=False, timeout=None):
        self.updated = True
        return self.update_success

    def detect_presence(self):
        return self.vcs_presence

    def get_url(self):
        return self.mockurl

    def url_matches(self, url, url_or_shortcut):
        return (url == url_or_shortcut or
                url_or_shortcut is None or
                url_or_shortcut.endswith('_shortcut'))
