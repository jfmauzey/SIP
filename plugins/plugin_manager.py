# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import urllib
import base64
import time

import os, glob
import web
import gv  # Get access to SIP's settings
from urls import urls  # Get access to SIP's URLs
from sip import template_render
from webpages import ProtectedPage
from helpers import restart

installed = []

# Add new url(s).
urls.extend([
            '/plugins', 'plugins.plugin_manager.plugins',
            '/upd-plugins', 'plugins.plugin_manager.update_plugins',
            '/browse-plugins', 'plugins.plugin_manager.browse_plugins',
            '/inst-plugins', 'plugins.plugin_manager.install_plugins',
            '/pmr', 'plugins.plugin_manager.restart_page'
             ])

# Add this plugin to the plugins menu
gv.plugin_menu.append([_('Manage Plugins'), '/plugins'])

def get_permissions():
    global installed
    try:
        files = glob.glob('plugins/[!_]*.py') #ignore files with "_" prefix
        pm = files.index(os.path.join('plugins','plugin_manager.py'))
        del files[pm] #  Remove the manager plugin from list
        #permissions is a parallel array containind either a 1 or 0 for each plugin
        permissions = [1 if os.access(f,os.X_OK) else 0 for f in files]
        #need to remove the "plugins/" path prefix from the file name
        installed = [f[len('plugins')+len(os.sep):] for f in files]
#        permissions = []
#        for f in files:
#            if os.access(f,os.X_OK):
#                permissions.append(1)
#            else :
#                permissions.append(0)
#        installed = [] #gotta remove plugins + os.sep
#        for f in files:
#           installed.append(f[len("plugins")+len(os.sep):])
        settings = dict(zip(installed, permissions))
        return settings
    except IOError:
        settings = {}
        return settings

def parse_manifest(plugin):
    try:
        with open ('plugins/manifests/'+plugin+'.manifest') as mf:
            mf_list = mf.readlines()
            sep = [i for i, s in enumerate(mf_list) if '###' in s][0]
            desc = ''.join(mf_list[:sep]).rstrip()
    #        print 'description: ', desc
            f_list = [line.strip() for line in mf_list[sep+2:]]
            print 'file list: ', f_list
            return (desc, f_list)
    except IOError:
        print "parse_manifest IOError"
        return ('', [])


def get_readme():
    response = urllib.urlopen('https://api.github.com/repos/Dan-in-CA/SIP_plugins/readme')
    data = response.read()
    d = json.loads(data)
    text = base64.b64decode(d['content'])
    t_list = text.split()
    sep = [i for i, s in enumerate(t_list) if '***' in s][0]
    plug_list = t_list[sep+1:]
    breaks = [i for i, s in enumerate(plug_list) if '---' in s]

    plugs = {}
    for i in  range(len(breaks)):
        if i < len(breaks)-1:
            plugs[plug_list[breaks[i]-1]] = ' '.join(plug_list[breaks[i]+1:breaks[i+1]-1])
        else:
            plugs[plug_list[breaks[i]-1]] = ' '.join(plug_list[breaks[i]+1:])
    return plugs


class plugins(ProtectedPage):
    """
    Load an html page for enabling or disabling plugins
    """

    def GET(self):
        settings = get_permissions()
        return template_render.plugins(settings)

class update_plugins(ProtectedPage):
    """
    Change plugin permissions or
    Delete selected plugins
    """

    def GET(self):
        global installed
        qdict = web.input()
        print 'qdict: ', qdict
        if qdict['btnId'] =="upd":
            for f in installed:
                fName = 'plugins/' + f
                i_mode = os.stat(fName).st_mode #mode bits XX...rwxrwxrwx
                if f in qdict:
                    os.chmod(fName, i_mode | 8) #enable group execute bit3 chmod g+x 
                else:
                    os.chmod(fName, i_mode & ~8) #disable group execute bit3 chmod g-x
                time.sleep(1)
            raise web.seeother('/restart')
        if qdict['btnId'] =="del":
            del_list = []
            for k in qdict.keys():  # Get plugins to delete
                if k[:3] == "del":
                    del_list.append(k[4:])
            for p in del_list:  # get files to delete for each plugin in list
                name = p.split('.')[0]
                desc, files = parse_manifest(name)
                for f in files:
                    victim = f.split()
                    if victim[0][-3:] == ".py":
                        b_code = victim[0].replace('.py', '.pyc')
                        os.remove(victim[1]+'/'+b_code)
                    os.remove(victim[1]+'/'+victim[0])
#            restart(1, True)
#            return template_render.restarting('/')
            raise web.seeother('/restart')


class browse_plugins(ProtectedPage):
    """
    Load an html page for choosing and installing plugins.
    """

    def GET(self):
        plug_dict = get_readme()
        return template_render.plugins_repo(plug_dict)

class install_plugins(ProtectedPage):
    """
    Install selected plugins from GitHub
    """

    def GET(self):
        qdict = web.input()
        print 'Install qdict: ', qdict
        for p in qdict.keys():  # Get plugins to install
            print p
#           https://raw.github.com/<username>/<repo>/<branch>/some_directory/file.r #### Example
            response = urllib.urlopen('https://raw.github.com/Dan-in-CA/SIP_plugins/master/'+p+'/'+p+'.manifest')
            data = response.readlines()
            sep = [i for i, s in enumerate(data) if '###' in s][0]
            file_list = [line.strip() for line in data[sep+2:]]
            short_list = [x for x in file_list if not 'data' in x and not 'manifest' in x]
            with open('plugins/manifests/'+p+'.manifest', 'w') as new_mf:
                new_mf.writelines(data)
            for f in short_list:
                pf = f.split()
                response = urllib.urlopen('https://raw.github.com/Dan-in-CA/SIP_plugins/master/'+p+'/'+pf[0])
                f_data = response.read()
                with open(pf[1]+'/'+pf[0], 'w') as next_file:
                    next_file.write(f_data)
        raise web.seeother('/plugins')

    class restart_page(ProtectedPage):
        """Restart system."""

        def GET(self):
            restart(2, True)
            return template_render.home()
