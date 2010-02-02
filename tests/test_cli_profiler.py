"""CLI tools for Python.

Copyright (c) 2009-2010 Will Maier <will@m.aier.us>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

from cli.profiler import Profiler

from tests import BaseTest

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class TestProfiler(BaseTest):

    def setUp(self):
        self.stdout = StringIO()
        self.profiler = Profiler(stdout=self.stdout)
        def func():
            """foo"""
            return "foo"
        def wrapper(*args, **kwargs):
            return func()
        self.func = func
        self.wrapper = wrapper


    def test_wrap(self):
        wrapped = self.profiler.wrap(self.wrapper, self.func)
        self.assertEqual(wrapped(), "foo")
        self.assertEqual(wrapped.__doc__, self.func.__doc__)

    def test_anon_wrap(self):
        def __profiler_func():
            """foo"""
            return "foo"
        wrapped = self.profiler.wrap(self.wrapper, __profiler_func)
        self.assertEqual(wrapped, "foo")

    def test_deterministic(self):
        # Sanity check...
        @self.profiler.deterministic
        def foo():
            pass
        foo()

    def test_deterministic(self):
        # Sanity check...
        @self.profiler.statistical
        def foo():
            pass
        foo()
