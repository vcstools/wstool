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


import sys
import traceback
import os
import copy
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
# choosing multiprocessing over threading for clean Control-C
# interrupts (provides terminate())
from multiprocessing import Process, Manager
from vcstools.vcs_base import VcsError


class MultiProjectException(Exception):
    pass


def samefile(file1, file2):
    """
    Test whether two pathnames reference the same actual file
    This is a workaround for the fact that some platforms
    do not have os.path.samefile (particularly windows). This
    is the patch that was integrated in python 3.0 (at which
    time we can probably remove this workaround).
    """
    try:
        return os.path.samefile(file1, file2)
    except AttributeError:
        try:
            from nt import _getfinalpathname
            return _getfinalpathname(file1) == _getfinalpathname(file2)
        except (NotImplementedError, ImportError):
            # On Windows XP and earlier, two files are the same if their
            #  absolute pathnames are the same.
            # Also, on other operating systems, fake this method with a
            #  Windows-XP approximation.
            return os.path.abspath(file1) == os.path.abspath(file2)


def conditional_abspath(uri):
    """
    @param uri: The uri to check
    @return: abspath(uri) if local path otherwise pass through uri
    """
    uri2 = urlparse(uri)
    # maybe it's a local file?
    if uri2.scheme == '':
        return os.path.abspath(uri)
    else:
        return uri


def is_web_uri(source_uri):
    """
    Uses heuristics to check whether uri is a web uri (as opposed to a file path)
    :param source_uri: string representing web uri or file path
    :returns: bool
    """
    if source_uri is None or source_uri == '':
        return False
    parsed_uri = urlparse(source_uri)
    if (parsed_uri.scheme == '' and
        parsed_uri.netloc == '' and
        not '@' in parsed_uri.path.split('/')[0]):

        return False
    return True


def normalize_uri(source_uri, base_path):
    """
    If source_uri is none or a web uri, return it.
    If source_uri is a relative path, make it an absolute path.
    Else return it normalized
    :param source_uri: some uri to a file, folder, or web resource
    :param base_path: path to use to make relative paths absolute
    :returns: normalized string
    """
    if source_uri is not None and not is_web_uri(source_uri):
        if os.path.isabs(source_uri):
            source_uri = os.path.normpath(source_uri)
        else:
            source_uri2 = os.path.normpath(os.path.join(base_path, source_uri))
            # sys.stderr.write("Warning: Converted relative uri path %s to abspath %s\n" %
            #       (source_uri, source_uri2))
            source_uri = source_uri2
    return source_uri


def string_diff(str1_orig, str2_orig, maxlen=11, backtrack=7):
    """
    Compares strings, returns a part of str2 depending on how many
    chars into the string the first difference can be found. If the
    difference is after maxlen, a prefix of str is removed so that
    only the 'backtrack'-last letters of the common prefix remain in str2.

    This only makes sense if str1 != str2, really.

    The purpose is to print str1 -> str2 without repeating a same long prefix

    :returns: a representation of where str2 differs from str1.
    """
    result = str2_orig or ''
    if str1_orig is not None and str2_orig is not None:
        # we cannot be sure we have strings, might be lists,
        # gracefully fail convert to string
        str1 = str(str1_orig)
        str2 = str(str2_orig)
        result = str2

        if len(str2) > len(str1):
            str1 = str1.ljust(len(str2))
        charcompare = [x[0] == x[1] for x in zip(str(str2), str(str1))]
        if False in charcompare:
            commonprefix = str2[:charcompare.index(False)]
            if len(commonprefix) > maxlen:
                result = "...%s" % str2[len(commonprefix) - backtrack:]
    return result


def normabspath(localname, path):
    """
    if localname is absolute, return it normalized. If relative,
    return normalized join of path and localname
    """
    # do not use realpath here as we want to keep symlinked path as such
    if os.path.isabs(localname) or path is None:
        return os.path.normpath(localname)
    abs_path = os.path.normpath(os.path.join(path, localname))
    return abs_path


def _is_parent_path(parent, child):
    """Return true if child is subdirectory of parent.

    Assumes both paths are absolute and don't contain symlinks.
    """
    parent = os.path.normpath(parent)
    child = os.path.normpath(child)

    prefix = os.path.commonprefix([parent, child])

    if prefix == parent:
        # Note: os.path.commonprefix operates on character basis, so
        # take extra care of situations like '/foo/ba' and '/foo/bar/baz'

        child_suffix = child[len(prefix):]
        child_suffix = child_suffix.lstrip(os.sep)

        if child == os.path.join(prefix, child_suffix):
            return True

    return False


def realpath_relation(abspath1, abspath2):
    """
    Computes the relationship abspath1 to abspath2
    :returns: None, 'SAME_AS', 'PARENT_OF', 'CHILD_OF'
    """
    assert os.path.isabs(abspath1), "Bug, %s is not absolute path" % abspath1
    assert os.path.isabs(abspath2), "Bug, %s is not absolute path" % abspath2
    realpath1 = os.path.realpath(abspath1)
    realpath2 = os.path.realpath(abspath2)
    if os.path.dirname(realpath1) == os.path.dirname(realpath2):
        if os.path.basename(realpath1) == os.path.basename(realpath2):
            return 'SAME_AS'
        return None
    else:
        if _is_parent_path(realpath1, realpath2):
            return 'PARENT_OF'
        if _is_parent_path(realpath2, realpath1):
            return 'CHILD_OF'
    return None


def select_element(elements, localname):
    """
    selects entry among elements where path or localname matches.
    Prefers localname matches in case of ambiguity.
    """
    path_candidate = None
    if localname is not None:
        realpath = os.path.realpath(localname)
        for element in elements:
            if localname == element.get_local_name():
                path_candidate = element
                break
            elif realpath == os.path.realpath(element.get_path()):
                path_candidate = element
    return path_candidate


def select_elements(config, localnames):
    """
    selects config elements with given localnames, returns in the
    order given in config If localnames has one element which is path
    of the config, return all elements
    """
    if config is None:
        return []
    if localnames is None:
        return config.get_config_elements()
    elements = config.get_config_elements()
    selected = []
    notfound = []
    for localname in localnames:
        element = select_element(elements, localname)
        if element is not None:
            selected.append(element)
        else:
            notfound.append(localname)
    if notfound != []:
        # if we just passed workspace path, return all workspace entries
        if (len(localnames) == 1 and
            os.path.realpath(localnames[0]) == os.path.realpath(config.get_base_path())):

            return config.get_config_elements()
        raise MultiProjectException("Unknown elements '%s'" % notfound)
    result = []
    # select in order and remove duplicates
    for element in config.get_config_elements():
        if element in selected:
            result.append(element)
    return result


## Multithreading The following classes help with distributing work
## over several instances, providing wrapping for starting, joining,
## collecting results, and catching Exceptions. Also they provide
## support for running groups of threads sequentially, for the case
## that some library is not thread-safe.


class WorkerThread(Process):

    def __init__(self, worker, outlist, index):
        Process.__init__(self)
        self.worker = worker
        if worker is None or worker.element is None:
            raise MultiProjectException("Bug: Invalid Worker")
        self.outlist = outlist
        self.index = index

    def run(self):
        result = {}
        try:
            result = {'entry': self.worker.element.get_path_spec()}
            result_dict = self.worker.do_work()
            if result_dict is not None:
                result.update(result_dict)
            else:
                result.update(
                    {'error': MultiProjectException("worker returned None")})
        except MultiProjectException as mpe:
            result.update({'error': mpe})
        except VcsError as vcse:
            result.update({'error': vcse})
        except OSError as ose:
            result.update({'error': ose})
        except Exception as exc:
            # this would be a bug, and we need trace to find them in
            # multithreaded cases.
            traceback.print_exc(file=sys.stderr)
            result.update({'error': exc})
        self.outlist[self.index] = result


class DistributedWork():

    def __init__(self, capacity, num_threads=10, silent=True):
         # need managed array since we need the results later
        man = Manager()
        self.outputs = man.list([None for _ in range(capacity)])
        self.threads = []
        self.sequentializers = {}
        self.index = 0
        self.num_threads = capacity if num_threads <= 0 else min(num_threads, capacity)
        self.silent = silent

    def add_thread(self, worker):
        thread = WorkerThread(worker, self.outputs, self.index)
        if self.index >= len(self.outputs):
            raise MultiProjectException(
                "Bug: Declared capacity exceeded %s >= %s" % (self.index,
                                                              len(self.outputs)))
        self.index += 1
        self.threads.append(thread)

    def run(self):
        """
        Execute all collected workers, terminate all on KeyboardInterrupt
        """
        if self.threads == []:
            return []
        if (self.num_threads == 1):
            for thread in self.threads:
                thread.run()
        else:
            # The following code is rather delicate and may behave differently
            # using threading or multiprocessing. running_threads is
            # intentionally not used as a shrinking list because of al the
            # possible multithreading / interruption corner cases
            # Not using Pool because of KeyboardInterrupt cases
            try:
                waiting_index = 0
                maxthreads = self.num_threads
                running_threads = []
                missing_threads = copy.copy(self.threads)
                # we are done if all threads have finished
                while len(missing_threads) > 0:
                    # we spawn more threads whenever some threads have finished
                    if len(running_threads) < maxthreads:
                        to_index = min(
                            waiting_index + maxthreads - len(running_threads),
                            len(self.threads))
                        for i in range(waiting_index, to_index):
                            self.threads[i].start()
                            running_threads.append(self.threads[i])
                        waiting_index = to_index
                    # threads have exitcode only once they terminated
                    missing_threads = [t for t in missing_threads if t.exitcode is None]
                    running_threads = [t for t in running_threads if t.exitcode is None]
                    if (not self.silent
                        and len(running_threads) > 0):

                        print("[%s] still active" % ",".join([th.worker.element.get_local_name() for th in running_threads]))
                    for thread in running_threads:
                        # this should prevent busy waiting
                        thread.join(1)
            except KeyboardInterrupt as k:
                for thread in self.threads:
                    if thread is not None and thread.is_alive():
                        print("[%s] terminated while active" % thread.worker.element.get_local_name())
                        thread.terminate()
                raise k

        self.outputs = [x for x in self.outputs if x is not None]
        message = ''
        for output in self.outputs:
            if "error" in output:
                if 'entry' in output:
                    message += "Error processing '%s' : %s\n" % (
                        output['entry'].get_local_name(), output["error"])
                else:
                    message += "%s\n" % output["error"]
        if message != '':
            raise MultiProjectException(message)
        return self.outputs
