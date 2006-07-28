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

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

"""
Test retrieving derived files from a CacheDir.
"""

import os.path
import shutil

import TestSCons

test = TestSCons.TestSCons()

test.subdir('cache', 'src')

test.write(['src', 'SConstruct'], """\
CacheDir(r'%s')
SConscript('SConscript')
""" % test.workpath('cache'))

test.write(['src', 'SConscript'], """\
def cat(env, source, target):
    target = str(target[0])
    open('cat.out', 'ab').write(target + "\\n")
    source = map(str, source)
    f = open(target, "wb")
    for src in source:
        f.write(open(src, "rb").read())
    f.close()
env = Environment(BUILDERS={'Cat':Builder(action=cat)})
env.Cat('aaa.out', 'aaa.in')
env.Cat('bbb.out', 'bbb.in')
env.Cat('ccc.out', 'ccc.in')
env.Cat('all', ['aaa.out', 'bbb.out', 'ccc.out'])
foo = 1
env.Depends('ccc.out', Value(foo))
""")

test.write(['src', 'aaa.in'], "aaa.in\n")
test.write(['src', 'bbb.in'], "bbb.in\n")
test.write(['src', 'ccc.in'], "ccc.in\n")


# Verify that building with -n and an empty cache reports that proper
# build operations would be taken, but that nothing is actually built
# and that the cache is still empty.
test.run(chdir = 'src', arguments = '-n .', stdout = test.wrap_stdout("""\
cat(["aaa.out"], ["aaa.in"])
cat(["bbb.out"], ["bbb.in"])
cat(["ccc.out"], ["ccc.in"])
cat(["all"], ["aaa.out", "bbb.out", "ccc.out"])
"""))

test.must_not_exist(test.workpath('src', 'aaa.out'))
test.must_not_exist(test.workpath('src', 'bbb.out'))
test.must_not_exist(test.workpath('src', 'ccc.out'))
test.must_not_exist(test.workpath('src', 'all'))
test.fail_test(len(os.listdir(test.workpath('cache'))))

# Verify that a normal build works correctly.
# This should populate the cache with our derived files.
test.run(chdir = 'src', arguments = '.')

test.must_match(['src', 'all'], "aaa.in\nbbb.in\nccc.in\n")
test.must_match(['src', 'cat.out'], "aaa.out\nbbb.out\nccc.out\nall\n")

test.up_to_date(chdir = 'src', arguments = '.')


test.run(chdir = 'src', arguments = '-c .')
test.unlink(['src', 'cat.out'])


# Verify that we now retrieve the derived files from cache,
# not rebuild them.  Then clean up.
test.run(chdir = 'src', arguments = '.', stdout = test.wrap_stdout("""\
Retrieved `aaa.out' from cache
Retrieved `bbb.out' from cache
Retrieved `ccc.out' from cache
Retrieved `all' from cache
"""))

test.must_not_exist(test.workpath('src', 'cat.out'))

test.up_to_date(chdir = 'src', arguments = '.')


test.run(chdir = 'src', arguments = '-c .')


# Verify that rebuilding with -n reports that everything was retrieved
# from the cache, but that nothing really was.
test.run(chdir = 'src', arguments = '-n .', stdout = test.wrap_stdout("""\
Retrieved `aaa.out' from cache
Retrieved `bbb.out' from cache
Retrieved `ccc.out' from cache
Retrieved `all' from cache
"""))

test.must_not_exist(test.workpath('src', 'aaa.out'))
test.must_not_exist(test.workpath('src', 'bbb.out'))
test.must_not_exist(test.workpath('src', 'ccc.out'))
test.must_not_exist(test.workpath('src', 'all'))


# Verify that rebuilding with -s retrieves everything from the cache
# even though it doesn't report anything.
test.run(chdir = 'src', arguments = '-s .', stdout = "")

test.must_match(['src', 'all'], "aaa.in\nbbb.in\nccc.in\n")
test.must_not_exist(test.workpath('src', 'cat.out'))

test.up_to_date(chdir = 'src', arguments = '.')


test.run(chdir = 'src', arguments = '-c .')


# Verify that updating one input file builds its derived file and
# dependency but that the other files are retrieved from cache.
test.write(['src', 'bbb.in'], "bbb.in 2\n")

test.run(chdir = 'src', arguments = '.', stdout = test.wrap_stdout("""\
Retrieved `aaa.out' from cache
cat(["bbb.out"], ["bbb.in"])
Retrieved `ccc.out' from cache
cat(["all"], ["aaa.out", "bbb.out", "ccc.out"])
"""))

test.must_match(['src', 'all'], "aaa.in\nbbb.in 2\nccc.in\n")
test.must_match(['src', 'cat.out'], "bbb.out\nall\n")

test.up_to_date(chdir = 'src', arguments = '.')


test.pass_test()
