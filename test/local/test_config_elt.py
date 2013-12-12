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

import unittest

import wstool.config
from wstool.common import MultiProjectException
from . import mock_client


class ConfigElements_Test(unittest.TestCase):

    def test_simple_config_element_API(self):
        path = "some/path"
        localname = "some/local/name"
        other1 = wstool.config_elements.ConfigElement(path, localname)
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertFalse(other1.is_vcs_element())
        other1 = wstool.config_elements.OtherConfigElement(path, localname)
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertEqual({'other': {'local-name': 'some/local/name'}}, other1.get_path_spec().get_legacy_yaml())
        self.assertFalse(other1.is_vcs_element())
        other1 = wstool.config_elements.SetupConfigElement(path, localname)
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertEqual({'setup-file': {'local-name': 'some/local/name'}}, other1.get_path_spec().get_legacy_yaml())
        self.assertFalse(other1.is_vcs_element())
        other1 = wstool.config_elements.OtherConfigElement(path, localname, properties=[{}])
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertEqual({'other': {'local-name': 'some/local/name'}}, other1.get_path_spec().get_legacy_yaml())
        self.assertFalse(other1.is_vcs_element())
        other1 = wstool.config_elements.OtherConfigElement(path, localname, properties=['meta'])
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertEqual({'other': {'local-name': 'some/local/name', 'meta': None}}, other1.get_path_spec().get_legacy_yaml())
        self.assertFalse(other1.is_vcs_element())
        other1 = wstool.config_elements.OtherConfigElement(path, localname, properties=[{'meta': {'repo-name': 'skynetish-ros-pkg'}}])
        self.assertEqual(path, other1.get_path())
        self.assertEqual(localname, other1.get_local_name())
        self.assertEqual({'other': {'local-name': 'some/local/name', 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, other1.get_path_spec().get_legacy_yaml())
        self.assertFalse(other1.is_vcs_element())

    def test_mock_vcs_config_element_init(self):
        path = "some/path"
        localname = "some/local/name"
        try:
            wstool.config_elements.AVCSConfigElement("mock", None, None, None)
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        try:
            wstool.config_elements.AVCSConfigElement("mock", "path", None, None)
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        try:
            wstool.config_elements.AVCSConfigElement("mock", None, None, "some/uri")
            self.fail("Exception expected")
        except MultiProjectException:
            pass
        path = "some/path"
        localname = "some/local/name"
        uri = 'some/uri'
        version = 'some.version'
        vcsc = wstool.config_elements.AVCSConfigElement("mock", path, localname, uri, vcsc=mock_client.MockVcsClient())
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mocktypemockdiffNone", vcsc.get_diff())
        self.assertEqual("mocktype mockstatusNone,False", vcsc.get_status())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'uri': 'some/uri'}}, vcsc.get_path_spec().get_legacy_yaml())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'uri': 'some/uri', }}, vcsc.get_versioned_path_spec().get_legacy_yaml())

        vcsc = wstool.config_elements.AVCSConfigElement("mock", path, localname, uri, None, vcsc=mock_client.MockVcsClient())
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mocktypemockdiffNone", vcsc.get_diff())
        self.assertEqual("mocktype mockstatusNone,False", vcsc.get_status())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'uri': 'some/uri'}}, vcsc.get_path_spec().get_legacy_yaml())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'uri': 'some/uri', }}, vcsc.get_versioned_path_spec().get_legacy_yaml())

        vcsc = wstool.config_elements.AVCSConfigElement("mock", path, localname, uri, version, vcsc=mock_client.MockVcsClient())
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mocktypemockdiffNone", vcsc.get_diff())
        self.assertEqual("mocktype mockstatusNone,False", vcsc.get_status())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'version': 'some.version', 'uri': 'some/uri'}}, vcsc.get_path_spec().get_legacy_yaml())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'version': 'some.version', 'uri': 'some/uri'}}, vcsc.get_versioned_path_spec().get_legacy_yaml())

        vcsc = wstool.config_elements.AVCSConfigElement(
            "mock", path, localname, uri, version,
            vcsc=mock_client.MockVcsClient(),
            properties=[{'meta': {'repo-name': 'skynetish-ros-pkg'}}])
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mocktypemockdiffNone", vcsc.get_diff())
        self.assertEqual("mocktype mockstatusNone,False", vcsc.get_status())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'version': 'some.version', 'uri': 'some/uri', 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, vcsc.get_path_spec().get_legacy_yaml())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'version': 'some.version', 'uri': 'some/uri', 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, vcsc.get_versioned_path_spec().get_legacy_yaml())

        # this time using 'uri_shortcut' in mock_client.MockVcsClient, get special treatment un url_matches()
        uri2 = 'some/uri2'
        vcsc = wstool.config_elements.AVCSConfigElement(
            "mock", path, localname, uri2, version,
            vcsc=mock_client.MockVcsClient(url='url_shortcut'),
            properties=[{'meta': {'repo-name': 'skynetish-ros-pkg'}}])
        self.assertEqual(path, vcsc.get_path())
        self.assertEqual(localname, vcsc.get_local_name())
        self.assertEqual(uri2, vcsc.uri)
        self.assertTrue(vcsc.is_vcs_element())
        self.assertEqual("mocktypemockdiffNone", vcsc.get_diff())
        self.assertEqual("mocktype mockstatusNone,False", vcsc.get_status())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'version': 'some.version', 'uri': 'some/uri2', 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, vcsc.get_path_spec().get_legacy_yaml())
        self.assertEqual({'mock': {'local-name': 'some/local/name', 'version': 'some.version', 'uri': 'some/uri2', 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, vcsc.get_versioned_path_spec().get_legacy_yaml())

    def test_mock_install(self):
        path = "some/path"
        localname = "some/local/name"
        uri = 'some/uri'
        version = 'some.version'
        mockclient = mock_client.MockVcsClient(url=uri)
        vcsc = wstool.config_elements.AVCSConfigElement("mock", path, localname, uri, None, vcsc=mockclient)
        vcsc.install()
        self.assertTrue(mockclient.checkedout)
        self.assertFalse(mockclient.updated)
        # checkout failure
        mockclient = mock_client.MockVcsClient(url=uri, checkout_success=False)
        try:
            vcsc = wstool.config_elements.AVCSConfigElement("mock", path, localname, uri, None, vcsc=mockclient)
            vcsc.install()
            self.fail("should have raised Exception")
        except MultiProjectException:
            pass
