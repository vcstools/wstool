# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
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
import codecs
import subprocess
from rosinstall.config_elements import SetupConfigElement

ROSINSTALL_FILENAME = ".rosinstall"


class ROSInstallException(Exception):
    pass


def is_path_stack(path):
    """

    @return: True if the path provided is the root of a stack.
    """
    stack_path = os.path.join(path, 'stack.xml')
    if os.path.isfile(stack_path):
        return True
    return False


def is_path_ros(path):
    """
    warning: exits with code 1 if stack document is invalid
    @param path: path of directory to check
    @type  path: str
    @return: True if path points to the ROS stack
    @rtype: bool
    """
    if path is None:
        return False
    if os.path.basename(path) == 'ros':
        stack_path = os.path.join(path, 'stack.xml')
        return os.path.isfile(stack_path)
    return False


def get_ros_root_from_setupfile(path):
    """ Return the ROS_ROOT if the path is a setup.sh file with an
    env.sh next to it which sets the ROS_ROOT

    :returns: path to ROS_ROOT or None
    """
    # For groovy, we rely on setup.sh setting ROS_ROOT, as no more
    # rosbuild stack 'ros' exists
    dirpath, basename = os.path.split(path)
    if basename != 'setup.sh':
        return None

    # env.sh exists since fuerte
    setupfilename = os.path.join(dirpath, 'env.sh')
    if not os.path.isfile(setupfilename):
        return None

    cmd = "%s sh -c 'echo $ROS_ROOT'" % setupfilename
    local_env = os.environ
    if 'ROS_ROOT' in local_env:
        local_env.pop('ROS_ROOT')
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               env=local_env, shell=True)
    out = process.communicate()[0]
    if sys.version < '3':
        out_str = codecs.unicode_escape_decode(out)[0]
    else:
        out_str = out
    return out_str.strip()


def get_ros_stack_path(config):
    """ Detect valid ROS_ROOT directories from the config elements"""
    # need to track actual path, realpath, and source
    found_paths = set()
    sources = {}
    for tree_el in config.get_config_elements():
        el_path = tree_el.get_path()
        if is_path_ros(el_path):
            found_paths.add(os.path.realpath(el_path))
            sources[el_path] = el_path
        elif isinstance(tree_el, SetupConfigElement):
            ros_root = get_ros_root_from_setupfile(tree_el.get_local_name())
            if ros_root:
                found_paths.add(os.path.realpath(ros_root))
                sources[tree_el.get_local_name()] = ros_root
    if len(found_paths) > 1:
        raise ROSInstallException("""\
Multiple ros stacks found in config %s, Please elimate all but one.
They come from the following sources: %s\n""" % (found_paths, sources))
    elif len(found_paths) == 1:
        return list(sources.values())[0]
    return None


def get_ros_package_path(config):
    """ Return the simplifed ROS_PACKAGE_PATH """
    code_trees = []
    for tree_el in reversed(config.get_config_elements()):
        if not is_path_ros(tree_el.get_path()):
            if not os.path.isfile(tree_el.get_path()):
                code_trees.append(tree_el.get_path())
    return code_trees
