"""SCons.Environment

XXX

"""

#
# Copyright (c) 2001, 2002 Steven Knight
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


import os
import copy
import os.path
import re
import string
import sys
import types

import SCons.Builder
import SCons.Defaults
from SCons.Errors import UserError
import SCons.Node.FS
import SCons.Util

def installFunc(env, target, source):
    try:
        map(lambda t: os.unlink(str(t)), target)
    except OSError:
        pass
    
    try:
        SCons.Node.FS.file_link(str(source[0]), str(target[0]))
        print 'Install file: "%s" as "%s"' % \
              (source[0], target[0])
        return 0
    except IOError, e:
        sys.stderr.write('Unable to install "%s" as "%s"\n%s\n' % \
                         (source[0], target[0], str(e)))
        return -1
    except OSError, e:
        sys.stderr.write('Unable to install "%s" as "%s"\n%s\n' % \
                         (source[0], target[0], str(e)))
        return -1

InstallBuilder = SCons.Builder.Builder(name='Install',
                                       action=installFunc)

def our_deepcopy(x):
   """deepcopy lists and dictionaries, and just copy the reference 
   for everything else.""" 
   if SCons.Util.is_Dict(x):
       copy = {}
       for key in x.keys():
           copy[key] = our_deepcopy(x[key])
   elif SCons.Util.is_List(x):
       copy = map(our_deepcopy, x)
   else:
       copy = x
   return copy

class Environment:
    """Base class for construction Environments.  These are
    the primary objects used to communicate dependency and
    construction information to the build engine.

    Keyword arguments supplied when the construction Environment
    is created are construction variables used to initialize the
    Environment.
    """

    def __init__(self, **kw):
	import SCons.Defaults
	self._dict = our_deepcopy(SCons.Defaults.ConstructionEnvironment)
        apply(self.Update, (), kw)

        #
        # self.autogen_vars is a tuple of tuples.  Each inner tuple
        # has four elements, each strings referring to an environment
        # variable, and describing how to autogenerate a particular
        # variable.  The elements are:
        #
        # 0 - The variable to generate
        # 1 - The "source" variable, usually a list
        # 2 - The "prefix" variable
        # 3 - The "suffix" variable
        #
        # The autogenerated variable is a list, consisting of every
        # element of the source list, or a single element if the source
        # is a string, with the prefix and suffix concatenated.
        #
        self.autogen_vars = ( VarInterpolator('_LIBFLAGS',
                                              'LIBS',
                                              'LIBLINKPREFIX',
                                              'LIBLINKSUFFIX'),
                              DirVarInterp('_LIBDIRFLAGS',
                                           'LIBPATH',
                                           'LIBDIRPREFIX',
                                           'LIBDIRSUFFIX' ),
                              DirVarInterp('_INCFLAGS',
                                           'CPPPATH',
                                           'INCPREFIX',
                                           'INCSUFFIX') )

    def __cmp__(self, other):
	return cmp(self._dict, other._dict)

    def Builders(self):
	pass	# XXX

    def Copy(self, **kw):
	"""Return a copy of a construction Environment.  The
	copy is like a Python "deep copy"--that is, independent
	copies are made recursively of each objects--except that
	a reference is copied when an object is not deep-copyable
	(like a function).  There are no references to any mutable
	objects in the original Environment.
	"""
        clone = copy.copy(self)
        clone._dict = our_deepcopy(self._dict)
	apply(clone.Update, (), kw)
	return clone

    def Scanners(self):
	pass	# XXX

    def	Update(self, **kw):
	"""Update an existing construction Environment with new
	construction variables and/or values.
	"""
	self._dict.update(our_deepcopy(kw))
        if self._dict.has_key('BUILDERS') and \
           not SCons.Util.is_List(self._dict['BUILDERS']):
            self._dict['BUILDERS'] = [self._dict['BUILDERS']]
        if self._dict.has_key('SCANNERS') and \
           not SCons.Util.is_List(self._dict['SCANNERS']):
            self._dict['SCANNERS'] = [self._dict['SCANNERS']]

        class BuilderWrapper:
            """Wrapper class that allows an environment to
            be associated with a Builder at instantiation.
            """
            def __init__(self, env, builder):
                self.env = env
                self.builder = builder

            def __call__(self, target = None, source = None):
                return self.builder(self.env, target, source)

            # This allows a Builder to be executed directly
            # through the Environment to which it's attached.
            # In practice, we shouldn't need this, because
            # builders actually get executed through a Node.
            # But we do have a unit test for this, and can't
            # yet rule out that it would be useful in the
            # future, so leave it for now.
            def execute(self, **kw):
                kw['env'] = self.env
                apply(self.builder.execute, (), kw)

        for b in self._dict['BUILDERS']:
            setattr(self, b.name, BuilderWrapper(self, b))

        for s in self._dict['SCANNERS']:
            setattr(self, s.name, s)

    def	Depends(self, target, dependency):
	"""Explicity specify that 'target's depend on 'dependency'."""
	tlist = SCons.Util.scons_str2nodes(target)
	dlist = SCons.Util.scons_str2nodes(dependency)
	for t in tlist:
	    t.add_dependency(dlist)

	if len(tlist) == 1:
	    tlist = tlist[0]
	return tlist

    def Ignore(self, target, dependency):
        """Ignore a dependency."""
        tlist = SCons.Util.scons_str2nodes(target)
        dlist = SCons.Util.scons_str2nodes(dependency)
        for t in tlist:
            t.add_ignore(dlist)

        if len(tlist) == 1:
            tlist = tlist[0]
        return tlist

    def Precious(self, *targets):
        tlist = []
        for t in targets:
            tlist.extend(SCons.Util.scons_str2nodes(t))

        for t in tlist:
            t.set_precious()

        if len(tlist) == 1:
            tlist = tlist[0]
        return tlist

    def Dictionary(self, *args):
	if not args:
	    return self._dict
	dlist = map(lambda x, s=self: s._dict[x], args)
	if len(dlist) == 1:
	    dlist = dlist[0]
	return dlist

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]

    def __delitem__(self, key):
        del self._dict[key]

    def Command(self, target, source, action):
        """Builds the supplied target files from the supplied
        source files using the supplied action.  Action may
        be any type that the Builder constructor will accept
        for an action."""
        bld = SCons.Builder.Builder(name="Command", action=action)
        return bld(self, target, source)

    def Install(self, dir, source):
        """Install specified files in the given directory."""
        sources = SCons.Util.scons_str2nodes(source)
        dnodes = SCons.Util.scons_str2nodes(dir,
                                            SCons.Node.FS.default_fs.Dir)
        tgt = []
        for dnode in dnodes:
            for src in sources:
                target = SCons.Node.FS.default_fs.File(src.name, dnode)
                tgt.append(InstallBuilder(self, target, src))
        if len(tgt) == 1:
            tgt = tgt[0]
        return tgt

    def InstallAs(self, target, source):
        """Install sources as targets."""
        sources = SCons.Util.scons_str2nodes(source)
        targets = SCons.Util.scons_str2nodes(target)
        ret = []
        for src, tgt in map(lambda x, y: (x, y), sources, targets):
            ret.append(InstallBuilder(self, tgt, src))
        if len(ret) == 1:
            ret = ret[0]
        return ret
  
    def subst(self, string):
	"""Recursively interpolates construction variables from the
	Environment into the specified string, returning the expanded
	result.  Construction variables are specified by a $ prefix
	in the string and begin with an initial underscore or
	alphabetic character followed by any number of underscores
	or alphanumeric characters.  The construction variable names
	may be surrounded by curly braces to separate the name from
	trailing characters.
	"""
	return SCons.Util.scons_subst(string, self._dict, {})

    def get_scanner(self, skey):
        """Find the appropriate scanner given a key (usually a file suffix).
        Does a linear search. Could be sped up by creating a dictionary if
        this proves too slow.
        """
        if self._dict['SCANNERS']:
            for scanner in self._dict['SCANNERS']:
                if skey in scanner.skeys:
                    return scanner
        return None

    def autogenerate(self, fs = SCons.Node.FS.default_fs, dir = None):
        """Return a dictionary of autogenerated "interpolated"
        construction variables.
        """
        dict = {}
        for interp in self.autogen_vars:
            interp.instance(dir, fs).generate(dict, self._dict)
        return dict

class VarInterpolator:
    def __init__(self, dest, src, prefix, suffix):
        self.dest = dest
        self.src = src
        self.prefix = prefix
        self.suffix = suffix

    def prepareSrc(self, dict):
        src = dict[self.src]
	if SCons.Util.is_String(src):
	    src = string.split(src)
        elif not SCons.Util.is_List(src):
            src = [ src ]

        def prepare(x, dict=dict):
            if isinstance(x, SCons.Node.Node):
                return x
            else:
                return SCons.Util.scons_subst(x, {}, dict)

        return map(prepare, src)

    def generate(self, ddict, sdict):
        if not sdict.has_key(self.src):
            ddict[self.dest] = ''
            return

        src = filter(lambda x: not x is None, self.prepareSrc(sdict))

        if not src:
            ddict[self.dest] = ''
            return

        prefix = sdict.get(self.prefix, '')
        suffix = sdict.get(self.suffix, '')

        def autogenFunc(x, suff=suffix, pref=prefix):
            """Generate the interpolated variable.  If the prefix
            ends in a space, or the suffix begins in a space,
            leave it as a separate element of the list."""
            ret = [ str(x) ]
            if pref and pref[-1] == ' ':
                ret.insert(0, pref[:-1])
            else:
                ret[0] = pref + ret[0]
            if suff and suff[0] == ' ':
                ret.append(suff[1:])
            else:
                ret[-1] = ret[-1] + suff
            return ret

        ddict[self.dest] = reduce(lambda x, y: x+y,
                                  map(autogenFunc, src))

    def instance(self, dir, fs):
        return self

class DirVarInterp(VarInterpolator):
    def __init__(self, dest, src, prefix, suffix):
        VarInterpolator.__init__(self, dest, src, prefix, suffix)
        self.fs = None
        self.Dir = None
        self.dictInstCache = {}

    def prepareSrc(self, dict):
        src = VarInterpolator.prepareSrc(self, dict)

        def prepare(x, self=self):
            if isinstance(x, SCons.Node.Node):
                return x
            elif str(x):
                return self.fs.Dir(str(x), directory=self.dir)
            else:
                return None

        return map(prepare, src)

    def instance(self, dir, fs):
        try:
            ret = self.dictInstCache[(dir, fs)]
        except KeyError:
            ret = copy.copy(self)
            ret.fs = fs
            ret.dir = dir
            self.dictInstCache[(dir, fs)] = ret
        return ret

    def generate(self, ddict, sdict):
        VarInterpolator.generate(self, ddict, sdict)
        if ddict[self.dest]:
            ddict[self.dest] = ['$('] + ddict[self.dest] + ['$)']
