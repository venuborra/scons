#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import os.path
import sys
import unittest

import SCons.Errors
import SCons.Options

import TestCmd

class PathOptionTestCase(unittest.TestCase):
    def test_PathOption(self):
        """Test PathOption creation"""
        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test',
                                          'test option help',
                                          '/default/path'))

        o = opts.options[0]
        assert o.key == 'test', o.key
        assert o.help == 'test option help ( /path/to/test )', repr(o.help)
        assert o.default == '/default/path', o.default
        assert not o.validator is None, o.validator
        assert o.converter is None, o.converter

    def test_PathExists(self):
        """Test the PathExists validator"""
        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test',
                                          'test option help',
                                          '/default/path',
                                          SCons.Options.PathOption.PathExists))

        test = TestCmd.TestCmd(workdir='')
        test.write('exists', 'exists\n')

        o = opts.options[0]

        o.validator('X', test.workpath('exists'), {})

        dne = test.workpath('does_not_exist')
        try:
            o.validator('X', dne, {})
        except SCons.Errors.UserError, e:
            assert str(e) == 'Path for option X does not exist: %s' % dne, e
        except:
            raise "did not catch expected UserError"

    def test_PathIsDir(self):
        """Test the PathIsDir validator"""
        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test',
                                          'test option help',
                                          '/default/path',
                                          SCons.Options.PathOption.PathIsDir))

        test = TestCmd.TestCmd(workdir='')
        test.subdir('dir')
        test.write('file', "file\n")

        o = opts.options[0]

        o.validator('X', test.workpath('dir'), {})

        f = test.workpath('file')
        try:
            o.validator('X', f, {})
        except SCons.Errors.UserError, e:
            assert str(e) == 'Directory path for option X is a file: %s' % f, e
        except:
            raise "did not catch expected UserError"

        dne = test.workpath('does_not_exist')
        try:
            o.validator('X', dne, {})
        except SCons.Errors.UserError, e:
            assert str(e) == 'Directory path for option X does not exist: %s' % dne, e
        except:
            raise "did not catch expected UserError"

    def test_PathIsDirCreate(self):
        """Test the PathIsDirCreate validator"""
        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test',
                                          'test option help',
                                          '/default/path',
                                          SCons.Options.PathOption.PathIsDirCreate))

        test = TestCmd.TestCmd(workdir='')
        test.write('file', "file\n")

        o = opts.options[0]

        d = test.workpath('dir')
        o.validator('X', d, {})
        assert os.path.isdir(d)

        f = test.workpath('file')
        try:
            o.validator('X', f, {})
        except SCons.Errors.UserError, e:
            assert str(e) == 'Path for option X is a file, not a directory: %s' % f, e
        except:
            raise "did not catch expected UserError"

    def test_PathIsFile(self):
        """Test the PathIsFile validator"""
        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test',
                                          'test option help',
                                          '/default/path',
                                          SCons.Options.PathOption.PathIsFile))

        test = TestCmd.TestCmd(workdir='')
        test.subdir('dir')
        test.write('file', "file\n")

        o = opts.options[0]

        o.validator('X', test.workpath('file'), {})

        d = test.workpath('d')
        try:
            o.validator('X', d, {})
        except SCons.Errors.UserError, e:
            assert str(e) == 'File path for option X does not exist: %s' % d, e
        except:
            raise "did not catch expected UserError"

        dne = test.workpath('does_not_exist')
        try:
            o.validator('X', dne, {})
        except SCons.Errors.UserError, e:
            assert str(e) == 'File path for option X does not exist: %s' % dne, e
        except:
            raise "did not catch expected UserError"

    def test_PathAccept(self):
        """Test the PathAccept validator"""
        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test',
                                          'test option help',
                                          '/default/path',
                                          SCons.Options.PathOption.PathAccept))

        test = TestCmd.TestCmd(workdir='')
        test.subdir('dir')
        test.write('file', "file\n")

        o = opts.options[0]

        o.validator('X', test.workpath('file'), {})

        d = test.workpath('d')
        o.validator('X', d, {})

        dne = test.workpath('does_not_exist')
        o.validator('X', dne, {})

    def test_validator(self):
        """Test the PathOption validator argument"""
        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test',
                                          'test option help',
                                          '/default/path'))

        test = TestCmd.TestCmd(workdir='')
        test.write('exists', 'exists\n')

        o = opts.options[0]

        o.validator('X', test.workpath('exists'), {})

        dne = test.workpath('does_not_exist')
        try:
            o.validator('X', dne, {})
        except SCons.Errors.UserError, e:
            expect = 'Path for option X does not exist: %s' % dne
            assert str(e) == expect, e
        else:
            raise "did not catch expected UserError"

        def my_validator(key, val, env):
            raise Exception, "my_validator() got called for %s, %s!" % (key, val)

        opts = SCons.Options.Options()
        opts.Add(SCons.Options.PathOption('test2',
                                          'more help',
                                          '/default/path/again',
                                          my_validator))

        o = opts.options[0]

        try:
            o.validator('Y', 'value', {})
        except Exception, e:
            assert str(e) == 'my_validator() got called for Y, value!', e
        else:
            raise "did not catch expected exception from my_validator()"




if __name__ == "__main__":
    suite = unittest.makeSuite(PathOptionTestCase, 'test_')
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
