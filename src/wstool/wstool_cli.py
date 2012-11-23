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

"""%(prog)s is a command to manipulate ROS workspaces. %(prog)s replaces its predecessor rosinstall.

Official usage:
  %(prog)s CMD [ARGS] [OPTIONS]

%(prog)s will try to infer install path from context

Type '%(prog)s help' for usage.
"""

from __future__ import print_function
import os
import sys
import yaml

from optparse import OptionParser

from rosinstall.cli_common import get_info_list, get_info_table, get_workspace
from rosinstall.multiproject_cmd import get_config, \
    cmd_snapshot, cmd_version, cmd_info
import rosinstall.__version__

from rosinstall.common import MultiProjectException, select_elements
from rosinstall.helpers import ROSINSTALL_FILENAME, \
    get_ros_package_path, get_ros_stack_path
from rosinstall.multiproject_cli import MultiprojectCLI, \
    __MULTIPRO_CMD_DICT__, __MULTIPRO_CMD_ALIASES__, \
    __MULTIPRO_CMD_HELP_LIST__, IndentedHelpFormatterWithNL, \
    list_usage

## This file adds or extends commands from multiproject_cli where ROS
## specific output has to be generated.

_PROGNAME = 'wstool'
_VARNAME = 'ROS_WORKSPACE'


class WstoolCLI(MultiprojectCLI):

    def __init__(self, config_filename=ROSINSTALL_FILENAME, progname=_PROGNAME):
        MultiprojectCLI.__init__(
            self,
            progname=progname,
            config_filename=config_filename,
            config_generator=rosinstall.multiproject_cmd.cmd_persist_config)

    def cmd_info(self, target_path, argv, reverse=True, config=None):
        only_option_valid_attrs = ['path', 'localname', 'version', 'revision', 'cur_revision', 'uri', 'cur_uri', 'scmtype']
        parser = OptionParser(usage="usage: %s info [localname]* [OPTIONS]" % self.progname,
                              formatter=IndentedHelpFormatterWithNL(),
                              description=__MULTIPRO_CMD_DICT__["info"] + """

The Status (S) column shows
 x  for missing
 L  for uncommited (local) changes
 V  for difference in version and/or remote URI

The 'Version-Spec' column shows what tag, branch or revision was given
in the .rosinstall file. The 'UID' column shows the unique ID of the
current (and specified) version. The 'URI' column shows the configured
URL of the repo.

If status is V, the difference between what was specified and what is
real is shown in the respective column. For SVN entries, the url is
split up according to standard layout (trunk/tags/branches).  The
ROS_PACKAGE_PATH follows the order of the table, earlier entries
overlay later entries.

When given one localname, just show the data of one element in list form.
This also has the generic properties element which is usually empty.

The --only option accepts keywords: %(opts)s

Examples:
$ %(prog)s info -t ~/ros/fuerte
$ %(prog)s info robot_model
$ %(prog)s info --yaml
$ %(prog)s info --only=path,cur_uri,cur_revision robot_model geometry
""" % {'prog': _PROGNAME, 'opts': only_option_valid_attrs},
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("--data-only", dest="data_only", default=False,
                          help="Does not provide explanations",
                          action="store_true")
        parser.add_option("--no-pkg-path", dest="no_pkg_path", default=False,
                          help="Suppress ROS_PACKAGE_PATH.",
                          action="store_true")
        parser.add_option("--pkg-path-only", dest="pkg_path_only", default=False,
                          help="Shows only ROS_PACKAGE_PATH separated by ':'. Supercedes all other options.",
                          action="store_true")
        parser.add_option("--only", dest="only", default=False,
                          help="Shows comma-separated lists of only given comma-separated attribute(s).",
                          action="store")
        parser.add_option("--yaml", dest="yaml", default=False,
                          help="Shows only version of single entry. Intended for scripting.",
                          action="store_true")

        # -t option required here for help but used one layer above, see cli_common
        parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
                          help="which workspace to use",
                          action="store")
        (options, args) = parser.parse_args(argv)

        if config is None:
            config = get_config(
                target_path,
                additional_uris=[],
                config_filename=self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s " % (config.get_base_path(), target_path))
        if args == []:
            args = None
        # relevant for code completion, so these should yield quick response:
        if options.pkg_path_only:
            print(":".join(get_ros_package_path(config)))
            return 0
        elif options.only:
            only_options = options.only.split(",")
            if only_options == '':
                parser.error('No valid options given')

            lookup_required = False
            for attr in only_options:
                if not attr in only_option_valid_attrs:
                    parser.error("Invalid --only option '%s', valids are %s" % (attr, only_option_valid_attrs))
                if attr in ['cur_revision', 'cur_uri', 'revision']:
                    lookup_required = True
            elements = select_elements(config, args)
            for element in elements:
                if lookup_required and element.is_vcs_element():
                    spec = element.get_versioned_path_spec()
                else:
                    spec = element.get_path_spec()
                output = []
                for attr in only_options:
                    if 'localname' == attr:
                        output.append(spec.get_local_name() or '')
                    if 'path' == attr:
                        output.append(spec.get_path() or '')
                    if 'scmtype' == attr:
                        output.append(spec.get_scmtype() or '')
                    if 'uri' == attr:
                        output.append(spec.get_uri() or '')
                    if 'version' == attr:
                        output.append(spec.get_version() or '')
                    if 'revision' == attr:
                        output.append(spec.get_revision() or '')
                    if 'cur_uri' == attr:
                        output.append(spec.get_curr_uri() or '')
                    if 'cur_revision' == attr:
                        output.append(spec.get_current_revision() or '')
                print(','.join(output))
            return 0
        if options.yaml:
            source_aggregate = cmd_snapshot(config, localnames=args)
            print(yaml.safe_dump(source_aggregate))
            return 0

        # this call takes long, as it invokes scms.
        outputs = cmd_info(config, localnames=args)
        if args is not None and len(outputs) == 1:
            print(get_info_list(config.get_base_path(),
                                outputs[0],
                                options.data_only))
            return 0

        header = 'workspace: %s\nROS_ROOT: %s' % (target_path,
                                                get_ros_stack_path(config))
        print(header)
        if not options.no_pkg_path:
            table = get_info_table(config.get_base_path(),
                                   outputs,
                                   options.data_only,
                                   reverse=reverse)
            if table is not None and table != '':
                print("\n%s" % table)

        return 0


def wstool_main(argv=None, usage=None):
    """
    Calls the function corresponding to the first argument.

    :param argv: sys.argv by default
    :param usage: function printing usage string, multiproject_cli.list_usage by default
    """
    if argv is None:
        argv = sys.argv
    if (sys.argv[0] == '-c'):
        sys.argv = [_PROGNAME] + sys.argv[1:]
    if '--version' in argv:
        print("%s: \t%s\n%s" % (_PROGNAME, rosinstall.__version__.version, cmd_version()))
        sys.exit(0)

    if not usage:
        usage = lambda: print(list_usage(progname=_PROGNAME,
                                         description=__doc__,
                                         command_keys=__MULTIPRO_CMD_HELP_LIST__,
                                         command_helps=__MULTIPRO_CMD_DICT__,
                                         command_aliases=__MULTIPRO_CMD_ALIASES__))
    workspace = None
    if len(argv) < 2:
        try:
            workspace = get_workspace(argv,
                                      os.getcwd(),
                                      config_filename=ROSINSTALL_FILENAME,
                                      varname=_VARNAME)
            argv.append('info')
        except MultiProjectException as e:
            print(str(e))
            usage()
            return 0

    if '--help' in argv or '-h' in argv:
        usage()
        return 0

    try:
        command = argv[1]
        args = argv[2:]

        if command == 'help':
            if len(argv) < 3:
                usage()
                return 0

            else:
                command = argv[2]
                args = argv[3:]
                args.insert(0, "--help")
                # help help
                if command == 'help':
                    usage()
                    return 0
        cli = WstoolCLI(progname=_PROGNAME)

        # commands for which we do not infer target workspace
        commands = {'init': cli.cmd_init}
        # commands which work on a workspace
        ws_commands = {
            'info': cli.cmd_info,
            'remove': cli.cmd_remove,
            'set': cli.cmd_set,
            'merge': cli.cmd_merge,
            'diff': cli.cmd_diff,
            'status': cli.cmd_status,
            'update': cli.cmd_update}
        for label in list(ws_commands.keys()):
            if label in __MULTIPRO_CMD_ALIASES__:
                ws_commands[__MULTIPRO_CMD_ALIASES__[label]] = ws_commands[label]

        if command not in commands and command not in ws_commands:
            if os.path.exists(command):
                args = ['-t', command] + args
                command = 'info'
            else:
                if command.startswith('-'):
                    print("First argument must be name of a command: %s" % command)
                else:
                    print("Error: unknown command: %s" % command)
                usage()
                return 1

        if command in commands:
            return commands[command](args)
        else:
            if workspace is None:
                workspace = get_workspace(args,
                                          os.getcwd(),
                                          config_filename=ROSINSTALL_FILENAME,
                                          varname=_VARNAME)
            return ws_commands[command](workspace, args)

    except KeyboardInterrupt:
        return 1
