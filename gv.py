#!/usr/bin/python
# -*- coding: utf-8 -*-


##############################
#### Revision information ####
major_ver = None
minor_ver = None
old_count = None
ver_str = None
ver_date = None

def set_sip_version(maj_v, min_v, old_c, v_str, v_date):
    major_ver = maj_v
    iminor_ver = min_v
    old_count = old_c
    ver_str = v_str
    ver_date = v_date
  

#####################
#### Global vars ####

# Settings Dictionary.  A set of vars kept in memory and persisted in a file.
# Edit this default dictionary definition to add or remove "key": "value" pairs
# or change defaults.
# note old passwords stored in the "pwd" option will be lost - reverts to
# default password.
import i18n
from calendar import timegm
import json
import time
from threading import RLock

#load the persistent gv.sd data from disk
sd = { #create defaults for initial dictionary
    u"en": 1,
    u"seq": 1,
    u"ir": [0],
    u"iw": [0],
    u"rsn": 0,
    u"htp": 80,
    u"nst": 8,
    u"rdst": 0,
    u"loc": u"",
    u"tz": 48,
    u"tf": 1,
    u"rs": 0,
    u"rd": 0,
    u"mton": 0,
    u"lr": 100,
    u"sdt": 0,
    u"mas": 0,
    u"wl": 100,
    u"bsy": 0,
    u"lg": 0,
    u"urs": 0,
    u"nopts": 13,
    u"pwd": u"b3BlbmRvb3I=",
    u"password": u"",
    u"ipas": 0,
    u"rst": 1,
    u"mm": 0,
    u"mo": [0],
    u"rbt": 0,
    u"mtoff": 0,
    u"nprogs": 1,
    u"nbrd": 1,
    u"tu": u"C",
    u"snlen": 32,
    u"name": u"SIP",
    u"theme": u"basic",
    u"show": [255],
    u"salt": "sZJ@LZ^!w1NGG|qg_zz>X\\jMR2#L#0e#Io[9gjW?'Ek:[Q087izk~\\{8!>/)27{}",
    u"password": "e74a224d3277c87785d284286f230ae5f5ee940d",
    u"lang": u"default",
    u"idd": 0,
    u"pigpio": 0,
    u"alr":0,
    u"vct": u"default"
}

try: #load sd with content from persistent storage
    with open('./data/sd.json', 'r') as sdf:
        try:
            sd_temp = json.load(sdf)
        except ValueError as e:
            print 'Error: JSON fails to parse "./data/sd.json resetting to defaults"'
            print e
            try:
                with open('./data/sd.json', 'w') as sdf:  # save sd to file
                    json.dump(sd, sdf, indent=4, sort_keys=True)
            except IOError:
                #should this be fatal -- persistent config fails.  All config
                #defaults
                print 'Error: unable to read or write config file "./data/sd.json"'

        else: #use data read from persistent storage to override defaults
            for key in sd:
                if key in sd_temp:  # replace default values in sd with values from file
                    sd[key] = sd_temp[key]

except IOError:  # file does not exist
    try: # create file using defaults
        with open('./data/sd.json', 'w') as sdf:  # save file
            json.dump(sd, sdf, indent=4, sort_keys=True)
    except IOError:
        #should this be fatal -- persistent config fails.  All config defaults
        print 'Error: unable to write config to "./data/sd.json"'

# setup gv properties not stored on disk
vc = None    
platform = ''  # must be done before the following import because gpio_pins will try to set
               # it
               # need to check if this is still true. Verify gpio_pins doesn't depend on
               # platform being defined
from valve_controller import vc_types

#jfm let valve_controller assign meaning to 'default'
vc_types[u'default'] = u'bbsr'
if sd['vct'] == u'default':
    sd['vct'] = vc_types[u'default']


def load_programs():
    """
    Load program data into memory from /data/programs.json file if it exists.
    otherwise create an empty programs data list (gv.pd).
    
    """
    global pd
    try:
        with open('./data/programs.json', 'r') as pf:
            pd = json.load(pf)
    except IOError:
        pd = []  # A config file -- return default and create file if not found.
        with open('./data/programs.json', 'w') as pf:
            json.dump(pd, pf, indent=4, sort_keys=True)
    return pd

def station_names():
    """
    Load station names from /data/stations.json file if it exists
    otherwise create file with defaults.
    
    Return station names as a list.
    
    """
    try:
        with open('./data/snames.json', 'r') as snf:
            return json.load(snf)
    except IOError:
        stations = [u"S01", u"S02", u"S03", u"S04", u"S05", u"S06", u"S07", u"S08"]
        jsave(stations, 'snames')
        return stations

nowt = time.localtime()
now = timegm(nowt)
tz_offset = int(time.time() - timegm(time.localtime())) # compatible with Javascript (negative tz shown as positive value)
plugin_menu = []  # Empty list of lists for plugin links (e.g.  ['name', 'URL'])
srvals = [0] * (sd['nst'])  # Shift Register values
output_srvals = [0] * (sd['nst'])  # Shift Register values last set by set_output()
output_srvals_lock = RLock()  # Safe threading access when setting state of relays
rovals = [0] * sd['nbrd'] * 7  # Run Once durations
snames = station_names()  # Load station names from file
pd = load_programs()  # Load program data from file
plugin_data = {}  # Empty dictionary to hold plugin based global data
ps = []  # Program schedule (used for UI display)
for i in range(sd['nst']):
    ps.append([0, 0])

pon = None  # Program on (Holds program number of a running program)
sbits = [0] * (sd['nbrd'] + 1)  # Used to display stations that are on in UI

rs = []  # run schedule
for j in range(sd['nst']):
    rs.append([0, 0, 0, 0])  # scheduled start time, scheduled stop time, duration, program index

lrun = [0, 0, 0, 0]  # station index, program number, duration, end time (Used in UI)
scount = 0  # Station count, used in set station to track on stations with master association.
use_gpio_pins = True

options = [
    [_("System name"), "string", "name", _("Unique name of this SIP system."), _("System")],
    [_("Location"), "string", "loc", _("City name or zip code. Use comma or + in place of space."), _("System")],
    [_("Language"),"list","lang", _("Select language."),_("System")],
#    [_("Time zone"), "int", "tz", _("Example: GMT-4:00, GMT+5:30 (effective after reboot.)"), _("System")],
    [_("24-hour clock"), "boolean", "tf", _("Display times in 24 hour format (as opposed to AM/PM style.)"), _("System")],
    [_("HTTP port"), "int", "htp", _("HTTP port."), _("System")],
    [_("Use pigpio"), "boolean", "pigpio", _("GPIO Library to use. Default is RPi.GPIO"), _("System")],    
    [_("Water Scaling"), "int", "wl", _("Water scaling (as %), between 0 and 100."), _("System")],
    [_("Disable security"), "boolean", "ipas", _("Allow anonymous users to access the system without a password."), _("Change Password")],
    [_("Current password"), "password", "opw", _("Re-enter the current password."), _("Change Password")],
    [_("New password"), "password", "npw", _("Enter a new password."), _("Change Password")],
    [_("Confirm password"), "password", "cpw", _("Confirm the new password."), _("Change Password")],
    [_("Sequential"), "boolean", "seq", _("Sequential or concurrent running mode."), _("Station Handling")],
    [_("Individual Duration"), "boolean", "idd", _("Allow each station to have its own rum time in programs."), _("Station Handling")],
    [_("Extension boards"), "int", "nbrd", _("Number of extension boards."), _("Station Handling")],
    [_("Station delay"), "int", "sdt", _("Station delay time (in seconds), between 0 and 240."), _("Station Handling")],
    [_("Active-Low Relay"), "boolean", "alr", _("Using active-low relay boards connected through shift registers"), _("Station Handling")],
    [_("Valve Controller"), "vc_enum", "vct", _("Specifies hardware interface for relay boards"), _("Station Handling")],
    [_("Master station"), "int", "mas",_( "Select master station."), _("Configure Master")],
    [_("Master on adjust"), "int", "mton", _("Master on delay (in seconds), between +0 and +60."), _("Configure Master")],
    [_("Master off adjust"), "int", "mtoff", _("Master off delay (in seconds), between -60 and +60."), _("Configure Master")],
    [_("Use rain sensor"), "boolean", "urs", _("Use rain sensor."), _("Rain Sensor")],
    [_("Normally open"), "boolean", "rst", _("Rain sensor type."), _("Rain Sensor")],
    [_("Enable logging"), "boolean", "lg", _("Log all events - note that repetitive writing to an SD card can shorten its lifespan."), _("Logging")],
    [_("Max log entries"), "int", "lr", _("Length of log to keep, 0=no limits."), _("Logging")]
]
