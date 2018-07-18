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

"""%(prog)s is a command to manipulate ROS workspaces. %(prog)s replaces its predecessor rosws.

Official usage:
  %(prog)s CMD [ARGS] [OPTIONS]

%(prog)s will try to infer install path from context

Type '%(prog)s help' for usage.
"""

from __future__ import print_function
import os
import sys

from optparse import OptionParser

from wstool.cli_common import get_info_table, get_workspace
import wstool.multiproject_cmd as multiproject_cmd
import wstool.__version__

from wstool.helpers import ROSINSTALL_FILENAME
from wstool.common import MultiProjectException
from wstool.multiproject_cli import MultiprojectCLI, \
    __MULTIPRO_CMD_DICT__, __MULTIPRO_CMD_ALIASES__, \
    __MULTIPRO_CMD_HELP_LIST__, IndentedHelpFormatterWithNL, \
    list_usage, get_header

## This file adds or extends commands from multiproject_cli where ROS
## specific output has to be generated.


_PROGNAME = 'wstool'


class WstoolCLI(MultiprojectCLI):

    def __init__(self, config_filename=ROSINSTALL_FILENAME, progname=_PROGNAME):

        def config_generator(config, filename, header=None, spec=True,
                             exact=False, vcs_only=False):
            wstool.multiproject_cmd.cmd_persist_config(
                config,
                filename,
                header,
                pretty=True,
                sort_with_localname=True,
                spec=spec,
                exact=exact,
                vcs_only=vcs_only)

        MultiprojectCLI.__init__(
            self,
            progname=progname,
            config_filename=config_filename,
            config_generator=config_generator)


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
        print("%s: \t%s\n%s" % (_PROGNAME,
                                wstool.__version__.version,
                                multiproject_cmd.cmd_version()))
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
                                      config_filename=ROSINSTALL_FILENAME)
            argv.append('info')
        except MultiProjectException as e:
            print(str(e))
            usage()
            return 0

    if argv[1] in ['--help', '-h']:
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
            'export': cli.cmd_snapshot,
            'diff': cli.cmd_diff,
            'foreach': cli.cmd_foreach,
            'scrape': cli.cmd_scrape,
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
            if workspace is None and not '--help' in args and not '-h' in args:
                workspace = get_workspace(args,
                                          os.getcwd(),
                                          config_filename=ROSINSTALL_FILENAME)
            return ws_commands[command](workspace, args)

    except KeyboardInterrupt:
        return 1
