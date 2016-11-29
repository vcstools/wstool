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
from wstool.config_elements import AVCSConfigElement, OtherConfigElement, SetupConfigElement
from wstool.common import MultiProjectException, normabspath, realpath_relation, normalize_uri


class Config:
    """
    A config is a set of config elements, each of which defines a folder or file
    and possibly a VCS from which to update the folder.
    """

    def __init__(self, path_specs, install_path, config_filename=None, extended_types=None, merge_strategy='KillAppend'):
        """
        :param config_source_dict: A list (e.g. from yaml) describing the config, list of dict, each dict describing one element.
        :param config_filename: When given a folder, Config
        :param merge_strategy: how to deal with entries with equivalent path. See insert_element

        will look in folder for file of that name for more config source, str.
        """
        assert install_path is not None, "Install path is None"
        if path_specs is None:
            raise MultiProjectException("Passed empty source to create config")
        # All API operations must grant that elements in trees have unique local_name and paths
        # Also managed (VCS) entries must be disjunct (meaning one cannot be in a child folder of another managed one)
        # The idea is that managed entries can safely be concurrently modified
        self.trees = []
        self.base_path = os.path.abspath(install_path)

        self.config_filename = None
        if config_filename is not None:
            self.config_filename = os.path.basename(config_filename)
        # using a registry primarily for unit test design
        self.registry = {'svn': AVCSConfigElement,
                         'git': AVCSConfigElement,
                         'hg': AVCSConfigElement,
                         'bzr': AVCSConfigElement,
                         'tar': AVCSConfigElement}
        if extended_types is not None:
            self.registry = dict(list(self.registry.items()) + list(extended_types.items()))

        for path_spec in path_specs:
            action = self.add_path_spec(path_spec, merge_strategy)
            # Usual action in init should be 'Append', anything else is unusual
            if action == 'KillAppend':
                print("Replace existing entry %s by appending." % path_spec.get_local_name())
            elif action == 'MergeReplace':
                print("Replace existing entry %s" % path_spec.get_local_name())
            elif action == 'MergeKeep':
                print("Keep existing entry %s, discard later one" % path_spec.get_local_name())

    def __str__(self):
        return str([str(x) for x in self.trees])

    def add_path_spec(self, path_spec, merge_strategy='KillAppend'):
        """
        add new element to this config with information provided in path spec

        :param merge_strategy: see insert_element
        :param path_specs: PathSpec objects
        :returns: merge action taken, see insert_element
        """
        # compute the local_path for the config element
        local_path = normabspath(
            path_spec.get_local_name(), self.get_base_path())
        if os.path.isfile(local_path):
            if path_spec.get_tags() is not None and 'setup-file' in path_spec.get_tags():
                elem = SetupConfigElement(local_path,
                                          os.path.normpath(path_spec.get_local_name()),
                                          properties=path_spec.get_tags())
                return self.insert_element(elem, merge_strategy)
            else:
                print("!!!!! Warning: Not adding file %s" % local_path)
                return None
        else:
            # scmtype == None kept for historic reasons here
            if (path_spec.get_scmtype() == None and
                self.config_filename is not None and
                os.path.exists(os.path.join(local_path, self.config_filename))):

                print("!!!!! Warning: Not recursing into other config folder %s containing file %s" % (local_path, self.config_filename))
                return None

            if path_spec.get_scmtype() != None:
                return self._insert_vcs_path_spec(path_spec, local_path, merge_strategy)
            else:
                # keep the given local name (e.g. relative path) for other
                # elements, but normalize
                local_name = os.path.normpath(path_spec.get_local_name())
                elem = OtherConfigElement(local_path,
                                          local_name,
                                          path_spec.get_uri(),
                                          path_spec.get_version(),
                                          properties=path_spec.get_tags())
                return self.insert_element(elem, merge_strategy)

    def _insert_vcs_path_spec(self, path_spec, local_path, merge_strategy='KillAppend'):
        # Get the version and source_uri elements
        source_uri = normalize_uri(path_spec.get_uri(), self.get_base_path())

        version = path_spec.get_version()
        try:
            local_name = os.path.normpath(path_spec.get_local_name())
            elem = self._create_vcs_config_element(
                path_spec.get_scmtype(),
                local_path,
                local_name,
                source_uri,
                version,
                properties=path_spec.get_tags())
            return self.insert_element(elem, merge_strategy)
        except LookupError as ex:
            raise MultiProjectException(
                "Abstracted VCS Config failed. Exception: %s" % ex)

    def insert_element(self, new_config_elt, merge_strategy='KillAppend'):
        """
        Insert ConfigElement to self.trees, checking for duplicate
        local-name or path first.  In case local_name matches, follow
        given strategy

        - KillAppend (default): remove old element, append new at the end
        - MergeReplace: remove first hit, insert new at that position.
        - MergeKeep: Discard new element

        In case local path matches but local name does not, raise Exception

        :returns: the action performed None, 'Append', 'KillAppend',
        'MergeReplace', 'MergeKeep'
        """
        removals = []
        replaced = False
        for index, loop_elt in enumerate(self.trees):
            # if paths are os.path.realpath, no symlink problems.
            relationship = realpath_relation(loop_elt.get_path(),
                                             new_config_elt.get_path())
            if relationship == 'SAME_AS':
                if os.path.normpath(loop_elt.get_local_name()) != os.path.normpath(new_config_elt.get_local_name()):
                    raise MultiProjectException("Elements with different local_name target the same path: %s, %s" % (loop_elt, new_config_elt))
                else:
                    if (loop_elt == new_config_elt):
                        return None
                    if (merge_strategy == 'MergeReplace' or
                        (merge_strategy == 'KillAppend' and
                         index == len(self.trees) - 1)):
                        self.trees[index] = new_config_elt
                        # keep looping to check for overlap when replacing non-
                        # scm with scm entry
                        replaced = True
                        if (loop_elt.is_vcs_element or not new_config_elt.is_vcs_element):
                            return 'MergeReplace'
                    elif merge_strategy == 'KillAppend':
                        removals.append(loop_elt)
                    elif merge_strategy == 'MergeKeep':
                        return 'MergeKeep'
                    else:
                        raise LookupError(
                            "No such merge strategy: %s" % str(merge_strategy))
            elif ((relationship == 'CHILD_OF' and new_config_elt.is_vcs_element())
                  or (relationship == 'PARENT_OF' and loop_elt.is_vcs_element())):
                # we do not allow any elements to be children of scm elements
                # to allow for parallel updates and because wstool may
                # delete scm folders on update, and thus subfolders can be
                # deleted with their parents
                raise MultiProjectException(
                    "Managed Element paths overlap: %s, %s" % (loop_elt,
                                                               new_config_elt))
        if replaced:
            return 'MergeReplace'
        for loop_elt in removals:
            self.trees.remove(loop_elt)
        self.trees.append(new_config_elt)
        if len(removals) > 0:
            return 'KillAppend'
        return 'Append'

    def remove_element(self, local_name):
        """
        Removes element in the tree with the given local name (should be only one)

        :returns: True if such an element was found
        """
        removals = []
        for tree_el in self.trees:
            if tree_el.get_local_name() == local_name:
                removals.append(tree_el)
        if len(removals) > 0:
            for tree_el in removals:
                self.trees.remove(tree_el)
            return True
        return False

    def _create_vcs_config_element(self, scmtype, path, local_name, uri, version='', properties=None):
        try:
            eclass = self.registry[scmtype]
        except LookupError:
            raise MultiProjectException(
                "No VCS client registered for vcs type %s" % scmtype)
        return eclass(scmtype=scmtype,
                      path=path,
                      local_name=local_name,
                      uri=uri,
                      version=version,
                      properties=properties)

    def get_base_path(self):
        return self.base_path

    def get_config_filename(self):
        return self.config_filename

    def get_source(self, versioned=False, vcs_only=False):
        """
        :param versioned: True returns sources as versioned PathSpec, False
        returns sources as simple PathSpec
        :param vcs_only: True returns only version-controlled sources, False
        returns all sources
        :returns: all elements that got added by user keystrokes
        (CLI and changed .rosinstall)
        """
        source_aggregate = []
        for tree_el in self.trees:
            if vcs_only and not tree_el.is_vcs_element():
                continue

            if not versioned or not tree_el.is_vcs_element():
                source_aggregate.append(tree_el.get_path_spec())
            else:
                source_aggregate.append(tree_el.get_versioned_path_spec())
        return source_aggregate

    def get_config_elements(self):
        source_aggregate = []
        for tree_el in self.trees:
            source_aggregate.append(tree_el)
        return source_aggregate
