
from glob import glob
import keyword
import re
import sys
import os
import stat
from os.path import dirname, join, split, splitext

parent = os.path.join(sys.path[0],'..')
if sys.path[1] != parent:
    sys.path.insert(1, parent)

def isidentifier(s):  # to make this work with Python 2.7.
    if s in keyword.kwlist:
        return False
    return re.match(r'^[a-z_][a-z0-9_]*$', s, re.I) is not None

basedir = dirname(__file__)
os_name = os.name

vc_types = {'no_vc' : 'no_vc: disable valve controller and sending of zone_changed signal',
            'virtual' : 'virtual: should go away'
           }

vct_installed = {}

__all__ = []
for name in glob(join(basedir, '*.py')):
    module = splitext(split(name)[-1])[0]
    if not module.startswith('_') and isidentifier(module) and not keyword.iskeyword(module):
        if os_name == "posix":
            st = os.stat(name)
            if bool(st.st_mode & stat.S_IXGRP):  # Load plugin if group permission is executable.
                try:
                   __import__(__name__+'.'+module)
                except Exception as e:
                    print 'Ignoring exception while loading the {} plug-in.'.format(module)
                    print e  # Provide feedback for plugin development
                else:
                    __all__.append(module)       
        elif os_name == "nt":
            try:
                __import__(__name__+'.'+module)
            except Exception as e:
                print 'Ignoring exception while loading the {} plug-in.'.format(module)
                print e  # Provide feedback for plugin development
            else:
                __all__.append(module)

#list the top level subdirectories and see if they contain an __init__.py file
candidate_pkgs = [ name for name in os.listdir(basedir) if os.path.isdir(os.path.join(basedir, name)) ]
for name  in candidate_pkgs:
    pkg_file = join(join(basedir,name),'__init__.py')
    if os.path.exists(pkg_file): #potential valid package
        if os_name == "posix":
            st = os.stat(pkg_file)
            if bool(st.st_mode & stat.S_IXGRP) and bool(st.st_mode & stat.S_ISREG):  # Load plugin if group permission is executable.
                try:
                    __import__(__name__ + '.' + name)
                except Exception as e:
                    print 'Ignoring exception while loading the {} package.'.format(name)
                    print e  # Provide feedback for plugin development
                else:
                    __all__.append(module)       
        elif os_name == "nt":
            try:
                __import__(__name__ + '.' + name)
            except Exception as e:
                print 'Ignoring exception while loading the {} package.'.format(name)
                print e  # Provide feedback for plugin development
            else:
                __all__.append(name)
__all__.sort()

