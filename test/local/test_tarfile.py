import os
import copy
import yaml

import rosinstall
import rosinstall.helpers
from rosinstall.rosinstall_cli import rosinstall_main

from test.scm_test_base import AbstractFakeRosBasedTest, _create_yaml_file, _create_config_elt_dict, _create_tar_file


class RosinstallTarTest(AbstractFakeRosBasedTest):
    """Tests for tarfile support"""

    @classmethod
    def setUpClass(self):
        AbstractFakeRosBasedTest.setUpClass()

        # create another repo in git

        self.tar_path = os.path.join(self.test_root_path, "tarfile.tar.bz2")
        _create_tar_file(self.tar_path)

        self.simple_tar_rosinstall = os.path.join(self.test_root_path, "simple_changed_uri.rosinstall")
        # same local name for gitrepo, different uri
        _create_yaml_file([_create_config_elt_dict("other", self.ros_path),
                           _create_config_elt_dict("tar", "temptar", uri=self.tar_path, version='temptar')],
                          self.simple_tar_rosinstall)

    def test_install(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_tar_rosinstall])
        self.assertTrue(rosinstall_main(cmd))

        self.assertTrue(os.path.isdir(os.path.join(self.directory, "temptar")))
        self.assertTrue(os.path.isfile(os.path.join(self.directory, ".rosinstall")))
        stream = open(os.path.join(self.directory, '.rosinstall'), 'r')
        yamlsrc = yaml.load(stream)
        stream.close()
        self.assertEqual(2, len(yamlsrc))
        self.assertEqual('other', list(yamlsrc[0].keys())[0])
        self.assertEqual('tar', list(yamlsrc[1].keys())[0])
