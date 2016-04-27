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

"Support for any command line interface (CLI) for wstool"

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict
import os
import re
from optparse import OptionParser
from wstool.common import samefile, MultiProjectException, select_elements

ONLY_OPTION_VALID_ATTRS = ['path', 'localname', 'version',
                           'revision', 'cur_revision', 'uri', 'cur_uri', 'scmtype']


def get_workspace(argv, shell_path, config_filename=None, varname=None):
    """
    If target option -t is given return value of that one. Else, if varname
    is given and exists, considers that one, plus,
    if config_filename is given, searches for a file named in config_filename
    in 'shell_path' and ancestors.
    In that case, if two solutions are found, asks the user.

    :param shell_path: where to look for relevant config_filename
    :param config_filename: optional, filename for files defining workspaces
    :param varname: optional, env var to be used as workspace folder
    :returns: abspath if a .rosinstall was found, error and exist else.
    """
    parser = OptionParser()
    parser.add_option(
        "-t", "--target-workspace",
        dest="workspace", default=None,
        help="which workspace to use",
        action="store")
    # suppress errors based on any other options this parser is agnostic about
    argv2 = [x for x in argv if ((not x.startswith('-')) or
                                 x.startswith('--target-workspace=') or
                                 x.startswith('-t') or
                                 x == '--target-workspace')]
    (options, _) = parser.parse_args(argv2)
    if options.workspace is not None:
        if (config_filename is not None and
            not os.path.isfile(os.path.join(options.workspace, config_filename))):

            raise MultiProjectException("%s has no workspace configuration file '%s'" % (os.path.abspath(options.workspace), config_filename))
        return os.path.abspath(options.workspace)

    varname_path = None
    if varname is not None and varname in os.environ:
        # workspace could be relative, maybe confusing,
        # but that's the users fault
        varname_path = os.environ[varname]
        if varname_path.strip() == '' or not os.path.isdir(varname_path):
            varname_path = None

    # use current dir
    current_path = None
    if config_filename is not None:
        while shell_path is not None and not shell_path == os.path.dirname(shell_path):
            if os.path.exists(os.path.join(shell_path, config_filename)):
                current_path = shell_path
                break
            shell_path = os.path.dirname(shell_path)

    if current_path is not None and varname_path is not None and not samefile(current_path, varname_path):
        raise MultiProjectException("Ambiguous workspace: %s=%s, %s" % (varname, varname_path, os.path.abspath(config_filename)))

    if current_path is None and varname_path is None:
        raise MultiProjectException("Command requires a target workspace.")

    if current_path is not None:
        return current_path
    else:
        return varname_path


def _uris_match(basepath, uri1, uri2):
    """
    True if uri2 is None or not None and same folder or equal string
    as uri1. Relative folders resolved using basepath
    """
    if uri1 is None:
        uri1 = ''
    if uri2 is None:
        return True
    if ((uri1 == uri2) or
        (basepath is not None and
         os.path.isdir(os.path.join(basepath, uri1)) and
         os.path.realpath(os.path.join(basepath, uri2)) == os.path.realpath(os.path.join(basepath, uri1)))):
        return True
    return False


def _get_svn_version_from_uri(uri):
    """
    in case of SVN, we can use the final part of
    standard uri as spec version, if it follows canonical SVN layout

    :param uri: uri to extract version from
    :returns changed_uri: str, version extracted uri
    :returns version: str, extracted version
    :returns: (None, None), for empty uri or when there is no regex match for version info
    """
    if uri is None:
        return None, None
    match = re.match('(.*/)((tags|branches|trunk)(/.*)*)', uri)
    if (match is not None and
            len(match.groups()) > 1 and
            uri == ''.join(match.groups()[0:2])):
        changed_uri = match.groups()[0]
        version = match.groups()[1]
        return changed_uri, version
    return None, None


def _get_status_flags(basepath, elt_dict):
    """
    returns a string where each char conveys status information about
    a config element entry

    :param basepath: path in which element lies
    :param elt_dict: a dict representing one elt_dict in a table
    :returns: str
    """
    if 'exists' in elt_dict and elt_dict['exists'] is False:
        return 'x'
    mflag = ''
    if 'modified' in elt_dict and elt_dict['modified'] is True:
        mflag = 'M'
    if (('curr_uri' in elt_dict and
         not _uris_match(basepath, elt_dict['uri'], elt_dict['curr_uri'])) or
        ('specversion' in elt_dict and
         elt_dict['specversion'] is not None and
         elt_dict['actualversion'] is not None and
         elt_dict['specversion'] != elt_dict['actualversion'])):
        mflag += 'V'
    if (('remote_revision' in elt_dict and
         elt_dict['remote_revision'] != '' and
         elt_dict['remote_revision'] is not None and
         'actualversion' in elt_dict and
         elt_dict['actualversion'] is not None and
         elt_dict['remote_revision'] != elt_dict['actualversion']) or
        (('version' not in elt_dict or
          elt_dict['version'] is None) and
         'default_remote_label' in elt_dict and
         elt_dict['default_remote_label'] is not None and
         ('curr_version' not in elt_dict or
          elt_dict['curr_version'] != elt_dict['default_remote_label']))):
        mflag += 'C'
    return mflag


def get_info_table_elements(basepath, entries, unmanaged=False):
    """returns a list of dict with refined information from entries"""

    outputs = []
    for line in entries:
        if not 'curr_uri' in line:
            line['curr_uri'] = None
        if not 'specversion' in line:
            line['specversion'] = None
        if not 'actualversion' in line:
            line['actualversion'] = None
        if not 'curr_version' in line:
            line['curr_version'] = None
        if not 'version' in line:
            line['version'] = None
        if not 'remote_revision' in line:
            line['remote_revision'] = None
        if not 'curr_version_label' in line:
            line['curr_version_label'] = None
        output_dict = {'scm': line['scm'],
                       'uri': line['uri'],
                       'curr_uri': None,
                       'version': line['version'],
                       'localname': line['localname']}

        if line is None:
            print("Bug Warning, an element is missing")
            continue

        if line['scm'] == 'git':
            if (line['specversion'] is not None and len(line['specversion']) > 12):
                line['specversion'] = line['specversion'][0:12]
            if (line['actualversion'] is not None and len(line['actualversion']) > 12):
                line['actualversion'] = line['actualversion'][0:12]
            if (line['remote_revision'] is not None and len(line['remote_revision']) > 12):
                line['remote_revision'] = line['remote_revision'][0:12]

        if line['scm'] is not None:

            if line['scm'] == 'svn':
                (line['uri'],
                line['version']) = _get_svn_version_from_uri(uri=line['uri'])
                if line['curr_uri'] is not None:
                    (line['curr_uri'],
                     line['curr_version_label']) = _get_svn_version_from_uri(
                         uri=line['curr_uri'])

            if line['scm'] in ['git', 'svn', 'hg']:
                line['curr_version'] = line['curr_version_label']

            if line['curr_version'] is not None:
                output_dict['version'] = line['curr_version']
            if output_dict['version'] is not None:
                if line['version'] != output_dict['version']:
                    if line['version']:
                        output_dict['version'] += "  (%s)" % line['version']
                    else:
                        if line['default_remote_label']:
                            if output_dict['version'] == line['default_remote_label']:
                                output_dict['version'] += "  (=)"
                            else:
                                output_dict['version'] += "  (%s)" % line['default_remote_label']
                        else:
                            output_dict['version'] += "  (-)"

            if (line['specversion'] is not None and
                line['specversion'] != '' and
                line['actualversion'] != line['specversion']):
                output_dict['matching'] = "%s (%s)" % (line['actualversion'], line['specversion'])
            else:
                output_dict['matching'] = line['actualversion']

            common_prefixes = ["https://", "http://"]
            if line['uri'] is not None and unmanaged is False:
                for pre in common_prefixes:
                    if line['uri'].startswith(pre):
                        line['uri'] = line['uri'][len(pre):]
                        break
                output_dict['uri'] = line['uri']

            if line['curr_uri'] is not None:
                for pre in common_prefixes:
                    if line['curr_uri'].startswith(pre):
                        line['curr_uri'] = line['curr_uri'][len(pre):]
                        break

            if (not _uris_match(basepath, line['uri'], line['curr_uri'])):
                output_dict['uri'] = "%s    (%s)" % (line[
                                                     'curr_uri'], line['uri'])

        else:
            output_dict['matching'] = " "
        output_dict['status'] = _get_status_flags(basepath, line)

        outputs.append(output_dict)

    return outputs


def get_info_table(basepath, entries, data_only=False, reverse=False,
                   unmanaged=False, selected_headers=None):
    """
    return a refined textual representation of the entries. Provides
    column headers and processes data.
    """
    headers = OrderedDict([
        ('localname', "Localname"),
        ('status', "S"),
        ('scm', "SCM"),
        ('version', "Version (Spec)"),
        ('matching', "UID  (Spec)"),
        ('uri', "URI  (Spec) [http(s)://...]"),
    ])
    # table design
    if unmanaged:
        selected_headers = ['localname', 'scm', 'uri']
    elif selected_headers is None:
        selected_headers = headers.keys()
    # validate selected_headers
    invalid_headers = [h for h in selected_headers if h not in headers.keys()]
    if invalid_headers:
        raise ValueError('Invalid headers are passed: %s' % invalid_headers)

    outputs = get_info_table_elements(
        basepath=basepath,
        entries=entries,
        unmanaged=unmanaged)

    # adjust column width
    column_length = {}
    for header in list(headers.keys()):
        column_length[header] = len(headers[header])
        for entry in outputs:
            if entry[header] is not None:
                column_length[header] = max(column_length[header],
                                            len(entry[header]))

    resultlines = []
    if not data_only and len(outputs) > 0:
        header_line = ' '
        for i, header in enumerate(selected_headers):
            output = headers[header]
            if i < len(selected_headers) - 1:
                output = output.ljust(column_length[header]) + " "
            header_line += output
        resultlines.append(header_line)
        header_line = ' '
        for i, header in enumerate(selected_headers):
            output = '-' * len(headers[header])
            if i < len(selected_headers) - 1:
                output = output.ljust(column_length[header]) + " "
            header_line += output
        resultlines.append(header_line)

    if reverse:
        outputs = reversed(outputs)
    for entry in outputs:
        if entry is None:
            print("Bug Warning, an element is missing")
            continue
        data_line = ' '
        for i, header in enumerate(selected_headers):
            output = entry[header]
            if output is None:
                output = ''
            if i < len(selected_headers) - 1:
                output = output.ljust(column_length[header]) + " "
            data_line += output
        resultlines.append(data_line)
    return "\n".join(resultlines)


def get_info_list(basepath, line, data_only=False):
    """
    Info for a single config entry
    """

    assert line is not None, "Bug Warning, an element is missing"

    headers = {
        'uri': "URI:",
        'curr_uri': "Current URI:",
        'scm': "SCM:",
        'localname': "Localname:",
        'path': "Path",
        'version': "Spec-Version:",
        'curr_version_label': "Current-Version:",
        'status': "Status:",
        'specversion': "Spec-Revision:",
        'actualversion': "Current-Revision:",
        'properties': "Other Properties:"}

    # table design
    selected_headers = ['localname', 'path', 'status',
                        'scm', 'uri', 'curr_uri',
                        'version', 'curr_version_label', 'specversion',
                        'actualversion', 'properties']

    line['status'] = _get_status_flags(basepath, line)

    header_length = 0
    for header in list(headers.keys()):
        header_length = max(header_length, len(headers[header]))
    result = ''
    for header in selected_headers:
        if not data_only:
            title = "%s  " % (headers[header].ljust(header_length))
        else:
            title = ''
        if header in line:
            output = line[header]
        if output is None:
            output = ''
        result += "%s%s\n" % (title, output)
    return result


def get_info_table_raw_csv(config, parser, properties, localnames):
    """
    returns raw data without decorations in comma-separated value format.
    allows to select properties.
    Given a config, collects all elements, and prints a line of each,
    with selected properties in the output

    :param parser: OptionParser used to throw option errors
    :param properties: list of property ids to display
    :param localnames: which config elements to show
    :return: list of str, each a csv line
    """
    lookup_required = False
    for attr in properties:
        if not attr in ONLY_OPTION_VALID_ATTRS:
            parser.error("Invalid --only option '%s', valids are %s" %
                         (attr, ONLY_OPTION_VALID_ATTRS))
        if attr in ['cur_revision', 'cur_uri', 'revision']:
            lookup_required = True
    elements = select_elements(config, localnames)
    result=[]
    for element in elements:
        if lookup_required and element.is_vcs_element():
            spec = element.get_versioned_path_spec()
        else:
            spec = element.get_path_spec()
        output = []
        for attr in properties:
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
        result.append(','.join(output))
    return result
