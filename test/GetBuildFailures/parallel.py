#!/usr/bin/env python
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

"""
Verify that a failed build action with -j works as expected.
"""

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import TestSCons

_python_ = TestSCons._python_

try:
    import threading
except ImportError:
    # if threads are not supported, then
    # there is nothing to test
    TestCmd.no_result()
    sys.exit()


test = TestSCons.TestSCons()

# We want to verify that -j 4 starts all four jobs, the first and last of
# which fail and the second and third of which succeed, and then stops
# processing due to the build failures.  To try to control the timing,
# the created build scripts use marker directories to avoid doing their
# processing until the previous script has finished.

contents = r"""\
import os.path
import sys
import time
wait_marker = sys.argv[1] + '.marker'
write_marker = sys.argv[2] + '.marker'
if wait_marker != '-.marker':
    while not os.path.exists(wait_marker):
        time.sleep(1)
if sys.argv[0] == 'mypass.py':
    open(sys.argv[3], 'w').write(open(sys.argv[4], 'r').read())
    exit_value = 0
elif sys.argv[0] == 'myfail.py':
    exit_value = 1
if write_marker != '-.marker':
    os.mkdir(write_marker)
sys.exit(exit_value)
"""

test.write('mypass.py', contents)
test.write('myfail.py', contents)

test.write('SConstruct', """\
Command('f3', 'f3.in', r'@%(_python_)s mypass.py -  f3 $TARGET $SOURCE')
Command('f4', 'f4.in', r'@%(_python_)s myfail.py f3 f4 $TARGET $SOURCE')
Command('f5', 'f5.in', r'@%(_python_)s myfail.py f4 f5 $TARGET $SOURCE')
Command('f6', 'f6.in', r'@%(_python_)s mypass.py f5 -  $TARGET $SOURCE')

import atexit

def print_build_failures():
    from SCons.Script import GetBuildFailures
    for bf in GetBuildFailures():
        print "%%s failed:  %%s" %% (bf.node, bf.errstr)

atexit.register(print_build_failures)
""" % locals())

test.write('f3.in', "f3.in\n")
test.write('f4.in', "f4.in\n")
test.write('f5.in', "f5.in\n")
test.write('f6.in', "f6.in\n")

expect_stdout = """\
scons: Reading SConscript files ...
scons: done reading SConscript files.
scons: Building targets ...
scons: building terminated because of errors.
f4 failed:  Error 1
f5 failed:  Error 1
""" % locals()

expect_stderr = """\
scons: *** [f4] Error 1
scons: *** [f5] Error 1
"""

test.run(arguments = '-j 4 .',
         status = 2,
         stdout = expect_stdout,
         stderr = expect_stderr)

test.must_match(test.workpath('f3'), 'f3.in\n')
test.must_not_exist(test.workpath('f4'))
test.must_not_exist(test.workpath('f5'))
test.must_match(test.workpath('f6'), 'f6.in\n') 



test.pass_test()
