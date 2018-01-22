
#for remote debug
#import ptvsd
#ptvsd.enable_attach('keys2kingdom')
#ptvsd.wait_for_attach()

import i18n
#check version info using git (if available)
import subprocess

major_ver = 3
minor_ver = 2
old_count = 747
ver_str = '%d.%d.%d' % (major_ver, minor_ver, old_count)
ver_date = '2015-01-09'

try:
    revision = int(subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']))
    ver_str = '%d.%d.%d' % (major_ver, minor_ver, (revision - old_count))
except Exception:
    print _('Could not use git to determine version!')
    revision = 999
    ver_str = '%d.%d.%d' % (major_ver, minor_ver, revision)

try:
    ver_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short']).strip()
except Exception:
    print _('Could not use git to determine date of last commit!')
    ver_date = '2015-01-09'

from gv import set_sip_version
set_sip_version(major_ver, minor_ver, old_count, ver_str, ver_date)

import plugins

try:
    print 'plugins loaded:'
except Exception:
    pass
for name in plugins.__all__:
    print ' ', name

import gv
gv.plugin_menu.sort(key=lambda entry: entry[0])

#  Keep plugin manager at top of menu
try:
    gv.plugin_menu.pop(gv.plugin_menu.index(['Manage Plugins', '/plugins']))
except Exception:
    pass

from valve_controller.valve_controller_factory import ValveControllerFactory as vcf
if gv.vc == None: #may be set by plugins to override default
    gv.vc = vcf(gv.sd['vct'], gv.sd['nst'], gv.sd['alr'])

from gpio_pins import set_output
from sip import timing_loop, app_start
import thread
import web  # the Web.py module. See webpy.org (Enables the Python SIP web interface)
thread.start_new_thread(timing_loop, ())

if gv.use_gpio_pins:
    set_output()    

#app = SIPApp_create()
#  disableShiftRegisterOutput()
#jfm move web.config.debug to follow import web
#web.config.debug = False  # Improves page load speed
#if web.config.get('_session') is None:
#    web.config._session = web.session.Session(app, web.session.DiskStore('sessions'),
#                                              initializer={'user': 'anonymous'})
#template_globals = {
#    'gv': gv,
#    'str': str,
#    'eval': eval,
#    'session': web.config._session,
#    'json': json,
#    'ast': ast,
#    '_': _,
#    'i18n': i18n,
#    'app_path': lambda p: web.ctx.homepath + p,
#    'web': web,
#}

#SIPApp_create()
#app.notfound = lambda: web.seeother('/')
#app.run()

app_start()