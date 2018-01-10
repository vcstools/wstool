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
import shutil
import datetime

from vcstools.vcs_abstraction import get_vcs_client
from vcstools.vcs_base import VcsError

from wstool.common import samefile, MultiProjectException
from wstool.config_yaml import PathSpec
from wstool.ui import Ui


# helper class
class PreparationReport(object):
    """
    Specifies after user interaction of how to perform install / update
    """

    def __init__(self, element):
        self.config_element = element
        self.abort = False       # abort ALL operations
        self.skip = False        # skip this tree
        self.error = None        # message
        self.verbose = False     # verbosity
        self.checkout = True     # checkout vs update
        self.backup = False      # backup vs delete
        self.backup_path = None  # where to move tree to
        self.inplace = False     # whether to follow symlink or just delete
        self.timeout = None      # maximum time for each checkout/update


## Each Config element provides actions on a local folder
class ConfigElement(object):
    """
    Base class for Config provides methods with not implemented
    exceptions. Also a few shared methods.
    """

    def __init__(self, path, local_name, properties=None):
        self.path = path
        if path is None:
            raise MultiProjectException("Invalid empty path")
        self.local_name = local_name
        self.properties = properties

    def get_path(self):
        """A normalized absolute path"""
        return self.path

    def get_local_name(self):
        """What the user specified in his config"""
        return self.local_name

    def prepare_install(self, backup_path=None, arg_mode='abort', robust=False):
        """
        Check whether install can be performed, asking user for
        decision if necessary.

        :param arg_mode: one of prompt, backup, delete, skip.
        Determines how to handle error cases
        :param backup_path: if arg_mode==backup, determines where to backup to
        :param robust: if true, operation will be aborted without
        changes to the filesystem and without user interaction
        :returns: A preparation_report instance,
        telling whether to checkout or to update,
        how to deal with existing tree, and where to backup to.
        """
        preparation_report = PreparationReport(self)
        preparation_report.skip = True
        return preparation_report

    def install(self, checkout=True, backup=False, backup_path=None,
                inplace=False, verbose=False, timeout=None, shallow=False):
        """
        Attempt to make it so that self.path is the result of checking
        out / updating from remote repo.

        No user Interaction allowed here (for concurrent mode).

        :param checkout: whether to checkout or update
        :param backup: if checking out, what to do if path exists.
        If true, backup_path must be set.
        """
        raise NotImplementedError("ConfigElement install unimplemented")

    def get_path_spec(self):
        """PathSpec object with values as specified in file"""
        raise NotImplementedError("ConfigElement get_path_spec unimplemented")

    def get_properties(self):
        """Any meta information attached"""
        return self.properties

    def get_versioned_path_spec(self):
        """PathSpec where VCS elements have the version looked up"""
        raise NotImplementedError(
            "ConfigElement get_versioned_path_spec unimplemented")

    def is_vcs_element(self):
        # subclasses to override when appropriate
        return False

    def get_diff(self, basepath=None):
        raise NotImplementedError("ConfigElement get_diff unimplemented")

    def get_status(self, basepath=None, untracked=False):
        raise NotImplementedError("ConfigElement get_status unimplemented")


    def backup(self, backup_path):
        if not backup_path:
            raise MultiProjectException(
                "[%s] Cannot install %s.  backup disabled." % (self.get_local_name(),
                                                               self.get_path()))
        backup_path = os.path.join(
            backup_path,
            "%s_%s" % (os.path.basename(self.path),
                       datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))
        print("[%s] Backing up %s to %s" % (self.get_local_name(),
                                            self.get_path(),
                                            backup_path))
        shutil.move(self.path, backup_path)

    def __str__(self):
        return str(self.get_path_spec().get_legacy_yaml())

    def __repr__(self):
        return str(self.get_path_spec().get_legacy_yaml())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.get_path_spec() == other.get_path_spec()
        else:
            return False


class OtherConfigElement(ConfigElement):

    def __init__(self, path, local_name, uri=None, version='', properties=None):
        super(OtherConfigElement, self).__init__(path, local_name, properties)
        self.uri = uri
        self.version = version

    def install(self, checkout=True, backup=False, backup_path=None,
                inplace=False, verbose=False, shallow=False):
        return True

    def get_versioned_path_spec(self):
        raise MultiProjectException(
            "Cannot generate versioned outputs with non source types")

    def get_path_spec(self):
        "yaml as from source"
        version = self.version
        if version == '':
            version = None
        return PathSpec(local_name=self.get_local_name(),
                        path=self.get_path(),
                        scmtype=None,
                        uri=self.uri,
                        version=version,
                        tags=self.get_properties())

    def get_diff(self, basepath=None):
        return ''

    def get_status(self, basepath=None, untracked=False):
        return ''


class SetupConfigElement(ConfigElement):
    """
    A setup config element specifies a single file containing
    configuration data for a config.
    """

    def install(self, checkout=True, backup=False, backup_path=None,
                inplace=False, verbose=False, shallow=False):
        return True

    def get_versioned_path_spec(self):
        raise MultiProjectException(
            "Cannot generate versioned outputs with non source types")

    def get_path_spec(self):
        return PathSpec(local_name=self.get_local_name(),
                        path=self.get_path(),
                        tags=['setup-file'] + (self.get_properties() or []))

    def get_diff(self, basepath=None):
        return ''

    def get_status(self, basepath=None, untracked=False):
        return ''


class VCSConfigElement(ConfigElement):

    def __init__(self, path, local_name, uri, version='', properties=None):
        """
        Creates a config element for a VCS repository.

        :param path: absolute or relative path, str
        :param vcs_client: Object compatible with vcstools.VcsClientBase
        :param local_name: display name for the element, str
        :param uri: VCS uri to checkout/pull from, str
        :param version: optional revision spec (tagname, SHAID, ..., str)
        """
        super(VCSConfigElement, self).__init__(path, local_name, properties)
        if uri is None:
            raise MultiProjectException(
                "Invalid scm entry having no uri attribute for path %s" % path)
        # strip trailing slashes if defined to not be too strict #3061
        self.uri = uri.rstrip('/')
        self.version = version

    def _get_vcsc(self):
        raise NotImplementedError("VCSConfigElement _get_vcsc() unimplemented")

    def is_vcs_element(self):
        return True

    def get_vcs_type_name(self):
        # also see override in AVCSConfigElement
        return self._get_vcsc().get_vcs_type_name()

    def detect_presence(self):
        # also see override in AVCSConfigElement
        return self._get_vcsc().detect_presence()

    def path_exists(self):
        # we could use _get_vcsc().path_exit(), but this causes a time
        # penalty for initializing this is crucial for bash tab
        # completion
        return os.path.isdir(self.path)

    def prepare_install(self, backup_path=None, arg_mode='abort', robust=False):
        preparation_report = PreparationReport(self)
        present = self.detect_presence()
        if present or self.path_exists():
            is_link = os.path.islink(self.path)
            # Directory exists see what we need to do
            error_message = None
            if not present:
                error_message = "Failed to detect %s presence at %s." % (
                    self.get_vcs_type_name(), self.path)
                if is_link:
                    error_message += " Path is symlink, only symlink will be removed."
            else:
                cur_url = self._get_vcsc().get_url()
                if cur_url is not None:
                    # strip trailing slashes for #3269
                    cur_url = cur_url.rstrip('/')
                if not cur_url or cur_url != self.uri.rstrip('/'):
                    # local repositories get absolute pathnames
                    if not (os.path.isdir(self.uri) and
                            os.path.isdir(cur_url) and
                            samefile(cur_url, self.uri)):
                        if not self._get_vcsc().url_matches(cur_url, self.uri):
                            error_message = "Url %s does not match %s requested." % (
                                cur_url, self.uri)
            if error_message is None:
                # update should be possible
                preparation_report.checkout = False
            else:
                # If robust ala continue-on-error, just error now and
                # it will be continued at a higher level
                if robust:
                    raise MultiProjectException("Update Failed of %s: %s" %
                                                (self.path, error_message))
                # prompt the user based on the error code
                if arg_mode == 'prompt':
                    print("Prepare updating %s (version %s) to %s" %
                          (self.uri, self.version, self.path))
                    mode = Ui.get_ui().prompt_del_abort_retry(
                        error_message,
                        allow_skip=True,
                        allow_inplace=is_link)
                else:
                    mode = arg_mode
                if mode == 'backup':
                    preparation_report.backup = True
                    if backup_path is None:
                        print("Prepare updating %s (version %s) to %s" %
                              (self.uri, self.version, self.path))
                        preparation_report.backup_path = \
                            Ui.get_ui().get_backup_path()
                    else:
                        preparation_report.backup_path = backup_path
                elif mode == 'abort':
                    preparation_report.abort = True
                    preparation_report.error = error_message
                elif mode == 'skip':
                    preparation_report.skip = True
                    preparation_report.error = error_message
                elif mode == 'delete':
                    preparation_report.backup = False
                elif mode == 'inplace':
                    preparation_report.inplace = True
                else:
                    raise RuntimeError(
                        'Bug: Unknown option "%s" selected' % mode)
        return preparation_report

    def install(self,
                checkout=True,
                backup=True,
                backup_path=None,
                inplace=False,
                timeout=None,
                verbose=False,
                shallow=False):
        """
        Runs the equivalent of SCM checkout for new local repos or
        update for existing.

        :param checkout: whether to use an update command or
        a checkout/clone command
        :param backup: if checkout is True and folder exists,
        if backup is false folder will be DELETED.
        :param backup_path: if checkout is true and backup is true,
        move folder to this location
        :param inplace: for symlinks, allows to delete contents
        at target location and checkout to there.
        """
        if checkout is True:
            print("[%s] Fetching %s (version %s) to %s" % (
                self.get_local_name(), self.uri, self.version, self.get_path()))
            if self.path_exists():
                if os.path.islink(self.path):
                    if inplace is False:
                        # remove same as unlink
                        os.remove(self.path)
                    else:
                        shutil.rmtree(os.path.realpath(self.path))
                else:
                    if backup is False:
                        shutil.rmtree(self.path)
                    else:
                        self.backup(backup_path)
            if not self._get_vcsc().checkout(self.uri,
                                             self.version,
                                             timeout=timeout,
                                             verbose=verbose,
                                             shallow=shallow):
                raise MultiProjectException(
                    "[%s] Checkout of %s version %s into %s failed." % (
                        self.get_local_name(),
                        self.uri,
                        self.version,
                        self.get_path()))
        else:
            print("[%s] Updating %s" %
                  (self.get_local_name(), self.get_path()))
            if not self._get_vcsc().update(self.version, verbose=verbose,
                                           timeout=timeout):
                raise MultiProjectException(
                    "[%s] Update Failed of %s" % (self.get_local_name(),
                                                  self.get_path()))
        print("[%s] Done." % self.get_local_name())

    def get_path_spec(self):
        "yaml as from source"
        version = self.version
        if version == '':
            version = None
        return PathSpec(local_name=self.get_local_name(),
                        path=self.get_path(),
                        scmtype=self.get_vcs_type_name(),
                        uri=self.uri,
                        version=version,
                        tags=self.get_properties())

    def get_versioned_path_spec(self, fetch=False):
        "yaml looking up current version"
        version = self.version
        if version == '':
            version = None
        revision = None
        if version is not None:
            # revision is the UID of the version spec, can be them same
            revision = self._get_vcsc().get_version(self.version)
            if revision is None:
                sys.stderr.write("Warning: version '%s' not found for '%s'\n"
                                  % (self.version, self.local_name))
        currevision = self._get_vcsc().get_version()
        remote_revision = self._get_vcsc().get_remote_version(fetch=fetch)
        curr_version = self._get_vcsc().get_current_version_label()
        uri = self.uri
        curr_uri = self._get_vcsc().get_url()
        # uri might be a shorthand notation equivalent to curr_uri
        if self._get_vcsc().url_matches(curr_uri, uri):
            curr_uri = uri
        return PathSpec(local_name=self.get_local_name(),
                        path=self.get_path(),
                        scmtype=self.get_vcs_type_name(),
                        uri=self.uri,
                        version=version,
                        curr_version=curr_version,
                        revision=revision,
                        currevision=currevision,
                        remote_revision=remote_revision,
                        curr_uri=curr_uri,
                        tags=self.get_properties())

    def get_default_remote_label(self):
        """
        check remote for e.g. default git branch
        """
        return self._get_vcsc().get_default_remote_version_label()

    def get_diff(self, basepath=None):
        return self._get_vcsc().get_diff(basepath)

    def get_status(self, basepath=None, untracked=False):
        return self._get_vcsc().get_status(basepath, untracked)


class AVCSConfigElement(VCSConfigElement):
    """
    Implementation using vcstools vcsclient, works for types svn, git, hg, bzr, tar

    :raises: Lookup Exception for unknown types
    """
    def __init__(self, scmtype, path, local_name, uri,
                 version='', vcsc=None, properties=None):
        super(AVCSConfigElement, self).__init__(path,
                                                local_name=local_name,
                                                uri=uri,
                                                version=version,
                                                properties=properties)
        self.vcsc = vcsc
        self._scmtype = scmtype

    def get_vcs_type_name(self):
        return self._scmtype

    def _get_vcsc(self):
        # lazy initializer
        if self.vcsc is None:
            try:
                self.vcsc = get_vcs_client(self._scmtype, self.get_path())
            except VcsError as exc:
                raise MultiProjectException(
                    "Unable to create vcs client of type %s for %s: %s" % (
                        self._scmtype, self.get_path(), exc))
        return self.vcsc

    def detect_presence(self):
        # to make more use of lazy initializer, do not instantiate
        # client for just this this is crucial for bash tab completion
        if self.get_vcs_type_name() == 'git':
            return os.path.exists(os.path.join(self.path, '.git'))
        elif self.get_vcs_type_name() == 'svn':
            return os.path.isdir(os.path.join(self.path, '.svn'))
        elif self.get_vcs_type_name() == 'hg':
            return os.path.isdir(os.path.join(self.path, '.hg'))
        elif self.get_vcs_type_name() == 'bzr':
            return os.path.isdir(os.path.join(self.path, '.bzr'))
        else:
            return self._get_vcsc().detect_presence()
