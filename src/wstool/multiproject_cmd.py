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


"""
The _cmd python files attempt to provide a reasonably
complete level of abstraction to multiproject functionality.

Client code will need to pass the Config element through,
and may use the ConfigElement API in places.
There are no guarantees at this time for the API to
remain stable, but the cmd API probably will change least.
A change to expect is abstraction of user interaction.
"""


import sys
import os
import shlex
from wstool.common import MultiProjectException, DistributedWork, \
    select_elements, normabspath
from wstool.config import Config, realpath_relation
from wstool.config_elements import AVCSConfigElement
from wstool.config_yaml import aggregate_from_uris, generate_config_yaml, \
    get_path_specs_from_uri, PathSpec

import vcstools
import vcstools.__version__
from vcstools.common import run_shell_command
from vcstools.vcs_abstraction import get_vcs_client
from vcstools.git import GitClient
from vcstools.hg  import HgClient
from vcstools.bzr import BzrClient
from vcstools.svn import SvnClient


def get_config(basepath,
               additional_uris=None,
               config_filename=None,
               merge_strategy='KillAppend'):
    """
    Create a Config element necessary for all other commands.  The
    command will look at the uris in sequence, each can be a web
    resource, a filename or a folder. In case it is a folder, when a
    config_filename is provided, the folder will be searched for a
    file of that name, and that one will be used.  Else the folder
    will be considered a target location for the config.  All files
    will be parsed for config elements, thus conceptually the input to
    Config is an expanded list of config elements. Config takes this
    list and consolidates duplicate paths by keeping the last one in
    the list.

    :param basepath: where relative paths shall be resolved against
    :param additional_uris: the location of config specifications or folders
    :param config_filename: name of files which may be looked at for config information
    :param merge_strategy: One of 'KillAppend, 'MergeKeep', 'MergeReplace'
    :returns: a Config object
    :raises MultiProjectException: on plenty of errors
    """
    if basepath is None:
        raise MultiProjectException("Need to provide a basepath for Config.")

    # print("source...........................", path_specs)

    ## Generate the config class with the uri and path
    if (config_filename is not None
        and basepath is not None
        and os.path.isfile(os.path.join(basepath, config_filename))):

        base_path_specs = get_path_specs_from_uri(os.path.join(basepath,
                                                               config_filename),
                                                  as_is=True)
    else:
        base_path_specs = []

    config = Config(base_path_specs, basepath,
                    config_filename=config_filename,
                    merge_strategy=merge_strategy)

    add_uris(config=config,
             additional_uris=additional_uris,
             config_filename=config.get_config_filename(),
             merge_strategy=merge_strategy)

    return config


def add_uris(config,
             additional_uris,
             # config_filename is not redundant with config.get_config_filename()
             # because in some cases a different config_filename is required
             config_filename=None,
             merge_strategy="KillAppend",
             allow_other_element=True):
    """
    changes the given config by merging with the additional_uris

    :param config: a Config objects
    :param additional_uris: the location of config specifications or folders
    :param config_filename: name of files which may be looked at for config
    information
    :param merge_strategy: One of 'KillAppend, 'MergeKeep', 'MergeReplace'
    :param allow_other_element: if False, discards elements to be added with
    no SCM information
    :returns: a dict {<local-name>: (<action>, <path-spec>), <local-name>: ...}
    determined by the merge_strategy
    :raises MultiProjectException: on plenty of errors
    """
    if config is None:
        raise MultiProjectException("Need to provide a Config.")

    if not additional_uris:
        return {}

    if config_filename is None:
        added_uris = additional_uris
    else:
        added_uris = []
        # reject if the additional uri points to the same file as our
        # config is based on
        for uri in additional_uris:
            # check whether we try to merge with other workspace
            comp_uri = None
            if (os.path.isfile(uri)
                and os.path.basename(uri) == config_filename):
                # add from other workspace by file
                comp_uri = os.path.dirname(uri)
            if (os.path.isdir(uri)
                and os.path.isfile(os.path.join(uri, config_filename))):
                # add from other workspace by dir
                comp_uri = uri
            if (comp_uri is not None and
                realpath_relation(os.path.abspath(comp_uri),
                                  os.path.abspath(config.get_base_path())) == 'SAME_AS'):
                print('Warning: Discarding config basepath as additional uri: %s' % uri)
                continue
            added_uris.append(uri)

    actions = {}
    if len(added_uris) > 0:
        path_specs = aggregate_from_uris(added_uris,
                                         config_filename,
                                         allow_other_element)
        for path_spec in path_specs:
            action = config.add_path_spec(path_spec, merge_strategy)
            actions[path_spec.get_local_name()] = (action, path_spec)

    return actions


def cmd_persist_config(config, filename, header=None,
                       pretty=False, sort_with_localname=False,
                       spec=True, exact=False, vcs_only=False):
    """writes config to given file in yaml syntax"""
    generate_config_yaml(config, filename, header,
                         pretty, sort_with_localname,
                         spec, exact, vcs_only)


def cmd_version():
    """Returns extensive version information"""
    def prettyversion(vdict):
        version = vdict.pop("version")
        return "%s; %s" % (version, ",".join(list(vdict.values())))
    return """vcstools:  %s
SVN:       %s
Mercurial: %s
Git:       %s
Tar:       %s
Bzr:       %s
""" % (vcstools.__version__.version,
       prettyversion(vcstools.SvnClient.get_environment_metadata()),
       prettyversion(vcstools.HgClient.get_environment_metadata()),
       prettyversion(vcstools.GitClient.get_environment_metadata()),
       prettyversion(vcstools.TarClient.get_environment_metadata()),
       prettyversion(vcstools.BzrClient.get_environment_metadata()))


def cmd_status(config, localnames=None, untracked=False):
    """
    calls SCM status for all SCM entries in config, relative to path

    :returns: List of dict {element: ConfigElement, diff: diffstring}
    :param untracked: also show files not added to the SCM
    :raises MultiProjectException: on plenty of errors
    """
    class StatusRetriever():

        def __init__(self, element, path, untracked):
            self.element = element
            self.path = path
            self.untracked = untracked

        def do_work(self):
            path_spec = self.element.get_path_spec()
            scmtype = path_spec.get_scmtype()
            status = self.element.get_status(self.path, self.untracked)
            # align other scm output to svn
            columns = -1
            if scmtype == "git":
                columns = 3
            elif scmtype == "hg":
                columns = 2
            elif scmtype == "bzr":
                columns = 4
            if columns > -1 and status is not None:
                status_aligned = ''
                for line in status.splitlines():
                    status_aligned = "%s%s%s\n" % (status_aligned,
                                                   line[:columns].ljust(8),
                                                   line[columns:])
                status = status_aligned
            return {'status': status}

    path = config.get_base_path()
    # call SCM info in separate threads
    elements = config.get_config_elements()
    work = DistributedWork(capacity=len(elements), num_threads=-1)
    elements = select_elements(config, localnames)
    for element in elements:
        if element.is_vcs_element():
            work.add_thread(StatusRetriever(element, path, untracked))
    outputs = work.run()
    return outputs


def cmd_diff(config, localnames=None):
    """
    calls SCM diff for all SCM entries in config, relative to path

    :returns: List of dict {element: ConfigElement, diff: diffstring}
    :raises MultiProjectException: on plenty of errors
    """
    class DiffRetriever():

        def __init__(self, element, path):
            self.element = element
            self.path = path

        def do_work(self):
            return {'diff': self.element.get_diff(self.path)}

    path = config.get_base_path()
    elements = config.get_config_elements()
    work = DistributedWork(capacity=len(elements), num_threads=-1)
    elements = select_elements(config, localnames)
    for element in elements:
        if element.is_vcs_element():
            work.add_thread(DiffRetriever(element, path))
    outputs = work.run()
    return outputs


def cmd_foreach(
    config,
    command,
    localnames=None,
    num_threads=1,
    timeout=None,
    scm_types=None,
    shell=False,
    verbose=False):
    """Run command in all SCM entries in config, relative to path"""

    class ForeachRetriever(object):
        def __init__(self, element, command, timeout, shell, verbose):
            self.element = element
            self.command = command
            self.timeout = timeout
            self.shell = shell
            self.verbose = verbose

        def do_work(self):
            command = self.command
            if not self.shell:
                command = shlex.split(command)
            returncode, stdout, stderr = run_shell_command(
                command,
                cwd=self.element.path,
                timeout=self.timeout,
                shell=self.shell,
                show_stdout=self.verbose)
            return {'returncode': returncode,
                    'stdout': stdout,
                    'stderr': stderr}

    elements = select_elements(config, localnames)
    work = DistributedWork(capacity=len(elements),
                           num_threads=num_threads)
    for element in elements:
        if ((scm_types is not None) and
                (element.get_vcs_type_name() not in scm_types)):
            continue
        work.add_thread(ForeachRetriever(element,
                                         command,
                                         timeout,
                                         shell,
                                         verbose))
    outputs = work.run()
    return outputs


def cmd_install_or_update(
    config,
    backup_path=None,
    mode='abort',
    robust=False,
    localnames=None,
    num_threads=1,
    timeout=None,
    verbose=False,
    shallow=False):
    """
    performs many things, generally attempting to make
    the local filesystem look like what the config specifies,
    pulling from remote sources the most recent changes.

    The command may have stdin user interaction (TODO abstract)

    :param backup_path: if and where to backup trees before deleting them
    :param robust: proceed to next element even when one element fails
    :returns: True on Success
    :raises MultiProjectException: on plenty of errors
    """
    success = True
    if not os.path.exists(config.get_base_path()):
        os.mkdir(config.get_base_path())
    # Prepare install operation check filesystem and ask user
    preparation_reports = []
    elements = select_elements(config, localnames)
    for tree_el in elements:
        abs_backup_path = None
        if backup_path is not None:
            abs_backup_path = os.path.join(config.get_base_path(), backup_path)
        try:
            preparation_report = tree_el.prepare_install(
                backup_path=abs_backup_path,
                arg_mode=mode,
                robust=robust)
            if preparation_report is not None:
                if preparation_report.abort:
                    raise MultiProjectException(
                        "Aborting install because of %s" % preparation_report.error)
                if not preparation_report.skip:
                    preparation_reports.append(preparation_report)
                else:
                    if preparation_report.error is not None:
                        print("Skipping install of %s because: %s" %
                              (preparation_report.config_element.get_local_name(),
                               preparation_report.error))
        except MultiProjectException as exc:
            fail_str = ("Failed to install tree '%s'\n %s" %
                        (tree_el.get_path(), exc))
            if robust:
                success = False
                print("Continuing despite %s" % fail_str)
            else:
                raise MultiProjectException(fail_str)

    class Installer():

        def __init__(self, report):
            self.element = report.config_element
            self.report = report

        def do_work(self):
            self.element.install(checkout=self.report.checkout,
                                 backup=self.report.backup,
                                 backup_path=self.report.backup_path,
                                 inplace=self.report.inplace,
                                 timeout=self.report.timeout,
                                 verbose=self.report.verbose,
                                 shallow=self.report.shallow)
            return {}

    work = DistributedWork(capacity=len(preparation_reports),
                           num_threads=num_threads,
                           silent=False)
    for report in preparation_reports:
        report.verbose = verbose
        report.timeout = timeout
        report.shallow = shallow
        thread = Installer(report)
        work.add_thread(thread)

    try:
        work.run()
    except MultiProjectException as exc:
        print ("Exception caught during install: %s" % exc)
        success = False
        if not robust:
            raise
    return success
    # TODO go back and make sure that everything in options.path is
    # described in the yaml, and offer to delete otherwise? not sure,
    # but it could go here


def cmd_snapshot(config, localnames=None):
    elements = select_elements(config, localnames)
    source_aggregate = []
    for element in elements:
        if element.is_vcs_element():
            spec = element.get_versioned_path_spec()
            export_spec = PathSpec(
                local_name=spec.get_local_name(),
                scmtype=spec.get_scmtype(),
                uri=spec.get_uri() or spec.get_curr_uri(),
                version=(spec.get_current_revision() or
                         spec.get_revision() or
                         spec.get_version()),
                path=spec.get_path())
            if not export_spec.get_version():
                sys.stderr.write(
                    'Warning, discarding non-vcs element %s\n' % element.get_local_name())
            source = export_spec.get_legacy_yaml()
            source_aggregate.append(source)
        else:
            sys.stderr.write('Warning, discarding non-vcs element %s\n' %
                             element.get_local_name())
    return source_aggregate


def cmd_info(config, localnames=None, untracked=False, fetch=False):
    """This function compares what should be (config_file) with what is
    (directories) and returns a list of dictionary giving each local
    path and all the state information about it available.
    """

    class InfoRetriever():
        """
        Auxilliary class to perform IO-bound operations in individual threads
        """

        def __init__(self, element, path, untracked, fetch):
            self.element = element
            self.path = path
            self.fetch = fetch
            self.untracked = untracked

        def do_work(self):
            localname = ""
            scm = None
            uri = ""
            curr_uri = None
            exists = False
            version = ""  # what is given in config file
            curr_version_label = ""  # e.g. branchname
            remote_revision = "" # UID on remote
            default_remote_label = None # git default branch
            display_version = ''
            modified = ""
            currevision = ""  # revision number of version
            specversion = ""  # actual revision number
            localname = self.element.get_local_name()
            path = self.element.get_path() or localname

            if localname is None or localname == "":
                raise MultiProjectException(
                    "Missing local-name in element: %s" % self.element)
            if (os.path.exists(normabspath(path, self.path))):
                exists = True
            if self.element.is_vcs_element():
                if not exists:
                    path_spec = self.element.get_path_spec()
                    version = path_spec.get_version()
                else:
                    path_spec = self.element.get_versioned_path_spec(fetch=fetch)
                    version = path_spec.get_version()
                    remote_revision = path_spec.get_remote_revision()
                    curr_version_label = path_spec.get_curr_version()
                    if (curr_version_label is not None and
                        version != curr_version_label):
                        display_version = curr_version_label
                    else:
                        display_version = version
                    curr_uri = path_spec.get_curr_uri()
                    status = self.element.get_status(self.path, self.untracked)
                    if (status is not None and
                        status.strip() != ''):
                        modified = True
                    specversion = path_spec.get_revision()
                    if (version is not None and
                        version.strip() != '' and
                        (specversion is None or specversion.strip() == '')):
                        specversion = '"%s"' % version
                    if (self.fetch and specversion == None and
                        path_spec.get_scmtype() == 'git'):
                        default_remote_label = self.element.get_default_remote_label()
                    currevision = path_spec.get_current_revision()
                scm = path_spec.get_scmtype()
                uri = path_spec.get_uri()
            return {'scm': scm,
                    'exists': exists,
                    'localname': localname,
                    'path': path,
                    'uri': uri,
                    'curr_uri': curr_uri,
                    'version': version,
                    'remote_revision': remote_revision,
                    'default_remote_label': default_remote_label,
                    'curr_version_label': curr_version_label,
                    'specversion': specversion,
                    'actualversion': currevision,
                    'modified': modified,
                    'properties': self.element.get_properties()}

    path = config.get_base_path()
    # call SCM info in separate threads
    elements = config.get_config_elements()
    elements = select_elements(config, localnames)
    work = DistributedWork(capacity=len(elements), num_threads=-1)
    for element in elements:
        if element.get_properties() is None or not 'setup-file' in element.get_properties():
            work.add_thread(InfoRetriever(element, path, untracked, fetch))
    outputs = work.run()

    return outputs



def cmd_find_unmanaged_repos(config):
    """
    Auxilliary function to find SCM folders within workspace that have not been tracked. This
    allows quicker diagnosis of the general state in a workspace, where folders can be part
    of the build even when they are not mentioned in the .rosinstall file.
    Nested SCMs are not investigated.
    """

    class UnmanagedInfoRetriever():

        def __init__(self, path, localname, scm_type):
            self.path = path
            self.localname = localname
            self.scm_type = scm_type
            self.element = AVCSConfigElement(scm_type, os.path.join(self.path, self.localname), localname, '')

        def do_work(self):
            vcsc = get_vcs_client(self.scm_type, os.path.join(self.path, self.localname))
            return {'scm': '--' + self.scm_type, # prefix '--' to allow copy&paste to set command
                'localname': self.localname,
                'path': self.path,
                'uri': vcsc.get_url(),
                'properties': self.element.get_properties()}

    path = config.get_base_path()
    # call SCM info in separate threads
    elements = config.get_config_elements()

    managed_paths = [os.path.join(path, e.get_local_name()) for e in elements]
    unmanaged_paths = []
    scm_clients = {SvnClient: 'svn', GitClient: 'git', BzrClient:'bzr', HgClient:'hg'}
    for root, dirs, files in os.walk(path):
        if root in managed_paths:
            # remove it from the walk if it's managed
            del dirs[:]
        else:
            for client, key in scm_clients.items():
                # check if it's a vcs dir
                if client.static_detect_presence(root):
                    # add it to the unmanaged list
                    unmanaged_paths.append((os.path.relpath(root, path), key))
                    # don't walk any other directories in this root
                    del dirs[:]
    work = DistributedWork(capacity=len(unmanaged_paths), num_threads=-1)
    for localname, scm_type in sorted(unmanaged_paths, key=lambda up: up[0], reverse=True):
        work.add_thread(UnmanagedInfoRetriever(path, localname, scm_type))
    outputs = work.run()

    return outputs
