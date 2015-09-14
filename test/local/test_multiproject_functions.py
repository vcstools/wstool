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
import unittest

from wstool.common import DistributedWork, WorkerThread, normabspath,\
    is_web_uri, select_elements, select_element, normalize_uri, realpath_relation,\
    conditional_abspath, string_diff, MultiProjectException


class FooThing:
    def __init__(self, el, result=None):
        self.element = el
        self.done = False
        self.result = result

    def do_work(self):
        self.done = True
        return self.result

    def get_path_spec(self):
        return self.element

    def get_local_name(self):
        return 'bar'


class MockElement:
    def __init__(self, localname, path):
        self.localname = localname
        self.path = path

    def get_local_name(self):
        return self.localname

    def get_path(self):
        return self.path


class FunctionsTest(unittest.TestCase):

    def test_normabspath(self):
        base = "/foo/bar"
        self.assertEqual("/foo/bar", normabspath('.', base))
        self.assertEqual("/foo/bar", normabspath('foo/..', base))
        self.assertEqual("/foo/bar", normabspath(base, base))
        self.assertEqual("/foo", normabspath("/foo", base))
        self.assertEqual("/foo/bar/bim", normabspath('bim', base))
        self.assertEqual("/foo", normabspath('..', base))

    def test_is_web_uri(self):
        self.assertTrue(is_web_uri('http://foo.com'))
        self.assertTrue(is_web_uri('http://foo.com/bar'))
        self.assertTrue(is_web_uri('http://foo.com:42'))
        self.assertTrue(is_web_uri('http://foo.com:42/bar'))
        self.assertTrue(is_web_uri('ssh://foo.com'))
        self.assertTrue(is_web_uri('lp:foo.com'))
        self.assertTrue(is_web_uri('git://foo.com'))
        self.assertTrue(is_web_uri('git+ssh://foo.com:foo'))
        self.assertTrue(is_web_uri('user@foo:foo/bar'))
        self.assertFalse(is_web_uri('foo/bar'))
        self.assertFalse(is_web_uri('bar'))
        self.assertFalse(is_web_uri(''))
        self.assertFalse(is_web_uri(None))

    def test_normalize_uri(self):
        self.assertEqual('/foo', normalize_uri('/foo', None))
        self.assertEqual(None, normalize_uri(None, None))
        self.assertEqual('/bar/foo', normalize_uri('foo', '/bar'))
        self.assertEqual('http://foo.com', normalize_uri('http://foo.com', None))

    def test_string_diff(self):
        self.assertEqual('', string_diff(None, None))
        self.assertEqual('foo', string_diff('foo', 'foo'))
        self.assertEqual('foo3', string_diff('foo', 'foo3'))
        self.assertEqual(
            '...7890foo3',
            string_diff('12345678901234567890foo',
                        '12345678901234567890foo3'))
        self.assertEqual(
            '...7890foo3',
            string_diff('12345678901234567890foo4',
                        '12345678901234567890foo3'))
        self.assertEqual(
            '...7890foo3',
            string_diff('12345678901234567890foo45',
                        '12345678901234567890foo3'))
        self.assertEqual(
            '...4567890foo123456789123456789',
            string_diff('12345678901234567890',
                        '12345678901234567890foo123456789123456789'))

        self.assertEqual("['foo']", string_diff(['foo'], ['foo']))
        self.assertEqual("['bar']", string_diff(['foo'], ['bar']))

    def test_conditional_abspath(self):
        path = "foo"
        self.assertEqual(os.path.normpath(os.path.join(os.getcwd(), path)), conditional_abspath(path))
        path = "http://someuri.com"
        self.assertEqual("http://someuri.com", conditional_abspath(path))

    def test_abspath_overlap(self):
        base = "/foo/bar"
        # simple
        self.assertEqual('SAME_AS', realpath_relation("/foo", "/foo"))
        self.assertEqual('SAME_AS', realpath_relation("/", "/"))
        # denormalized
        self.assertEqual('SAME_AS', realpath_relation("/foo/.", "/foo/bar/../"))
        # subdir
        self.assertEqual('PARENT_OF', realpath_relation("/foo", "/foo/bar/baz/bam"))
        self.assertEqual('CHILD_OF', realpath_relation("/foo/bar/baz/bam", "/foo"))
        ## Negatives
        self.assertEqual(None, realpath_relation("/foo", "/bar"))
        self.assertEqual(None, realpath_relation("/foo", "/foo2"))
        self.assertEqual(None, realpath_relation("/foo/bar", "/foo/ba"))
        self.assertEqual(None, realpath_relation("/foo/ba", "/foo/bar/baz"))
        self.assertEqual(None, realpath_relation("/foo/bar/baz", "/foo/ba"))

    def test_select_element(self):
        self.assertEqual(None, select_element(None, None))
        self.assertEqual(None, select_element([], None))
        mock1 = MockElement('foo', '/test/path1')
        mock2 = MockElement('bar', '/test/path2')
        mock3 = MockElement('baz', '/test/path3')
        self.assertEqual(None, select_element([], 'pin'))
        self.assertEqual(None, select_element([mock1], 'pin'))
        self.assertEqual(None, select_element([mock1, mock3], 'pin'))

        self.assertEqual('bar', select_element([mock1, mock2, mock3], 'bar').get_local_name())
        self.assertEqual('bar', select_element([mock1, mock2, mock3], '/test/path2').get_local_name())
        self.assertEqual('bar', select_element([mock1, mock2, mock3], '/test/../foo/../test/path2/').get_local_name())

    def test_worker_thread(self):
        try:
            w = WorkerThread(None, None, None)
            self.fail("expected Exception")
        except MultiProjectException:
            pass
        try:
            w = WorkerThread(FooThing(el=None), 2, 3)
            self.fail("expected Exception")
        except MultiProjectException:
            pass
        thing = FooThing(FooThing(None))
        result = [None]
        w = WorkerThread(thing, result, 0)
        self.assertEqual(thing.done, False)
        w.run()
        self.assertEqual(thing.done, True, result)
        self.assertEqual(True, 'error' in result[0])

        thing = FooThing(FooThing(None), result={'done': True})
        result = [None]
        w = WorkerThread(thing, result, 0)
        self.assertEqual(thing.done, False)
        w.run()
        self.assertEqual(thing.done, True, result)
        self.assertEqual(False, 'error' in result[0], result)

    def test_distributed_work_init(self):
        work = DistributedWork(capacity=200)
        self.assertEqual(10, work.num_threads)
        work = DistributedWork(capacity=3, num_threads=5)
        self.assertEqual(3, work.num_threads)
        work = DistributedWork(capacity=5, num_threads=3)
        self.assertEqual(3, work.num_threads)
        work = DistributedWork(capacity=3, num_threads=-1)
        self.assertEqual(3, work.num_threads)

    def test_distributed_work(self):
        work = DistributedWork(3)

        thing1 = FooThing(FooThing(FooThing(None)), result={'done': True})
        thing2 = FooThing(FooThing(FooThing(None)), result={'done': True})
        thing3 = FooThing(FooThing(FooThing(None)), result={'done': True})
        self.assertEqual(3, len(work.outputs))
        work.add_thread(thing1)
        self.assertEqual(1, len(work.threads))
        work.add_thread(thing2)
        self.assertEqual(2, len(work.threads))
        work.add_thread(thing3)
        self.assertEqual(3, len(work.threads))
        self.assertEqual(thing1.done, False)
        self.assertEqual(thing2.done, False)
        self.assertEqual(thing3.done, False)
        output = work.run()
        self.assertEqual(False, 'error' in output[0], output)
        self.assertEqual(False, 'error' in output[1], output)
        self.assertEqual(False, 'error' in output[2], output)

    def test_select_elements(self):
        self.assertEqual([], select_elements(None, None))
        mock1 = MockElement('foo', '/test/path1')
        mock2 = MockElement('bar', '/test/path2')
        mock3 = MockElement('baz', '/test/path3')

        class FakeConfig():
            def get_config_elements(self):
                return [mock1, mock2, mock3]

            def get_base_path(self):
                return '/foo/bar'
        self.assertEqual([mock1, mock2, mock3],
                         select_elements(FakeConfig(), None))
        self.assertEqual([mock2],
                         select_elements(FakeConfig(), ['bar']))
        self.assertEqual([mock1, mock2, mock3],
                         select_elements(FakeConfig(), ['/foo/bar']))
        self.assertRaises(MultiProjectException, select_elements, FakeConfig(), ['bum'])
        self.assertRaises(MultiProjectException, select_elements, FakeConfig(), ['foo', 'bum', 'bar'])
        self.assertRaises(MultiProjectException, select_elements, FakeConfig(), ['bu*'])
