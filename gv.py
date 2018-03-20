#!/usr/bin/python
# -*- coding: utf-8 -*-


##############################
#### Revision information ####
import subprocess

major_ver = 3
minor_ver = 2
old_count = 747

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

# Load the persistent gv.sd data from disk.
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


###
# Functions to deal with persistent storage used for user configurable
# options and preferences.
###

def update_default_sd():
    """
    Load default overrides from persitent storage "data/sd.json"
    Will overwrite any value in gv.sd[] with the value retrieved
    from the persistent file.
    """
    global sd

    try: # Load sd with content from persistent storage.
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
                    # Should this be fatal -- persistent config fails.  All config
                    # set to defaults.
                    print 'Error: unable to read or write config file "./data/sd.json"'

            else: # Use data read from persistent storage to override defaults.
                for key in sd:
                    if key in sd_temp:  # Replace default values in sd with values from file.
                        sd[key] = sd_temp[key]

    except IOError:  # File does not exist.
        try: # Create file using defaults.
            with open('./data/sd.json', 'w') as sdf:  # Save file.
                json.dump(sd, sdf, indent=4, sort_keys=True)
        except IOError:
            # Should this be fatal -- persistent config fails.  All config
            # set only by defaults. No persistent user config.
            print 'Error: unable to write config to "./data/sd.json"'


def jsave(data, fname):
    """
    Save data to a json file.
    """
    with open('./data/' + fname + '.json', 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)


def station_names():
    """
    Load station names from  data/stations.json file if it exists
    otherwise create file with defaults.
    
    Return station names as a list.
    Does not trap write errors if failure to write to persistent storage.
    """
    try:
        with open('./data/snames.json', 'r') as snf:
            return json.load(snf)
    except IOError:
        stations = [u"S01", u"S02", u"S03", u"S04", u"S05", u"S06", u"S07", u"S08"]
        jsave(stations, 'snames')
        return stations


def load_programs():
    """
    Load program data into memory from /data/programs.json file if it exists.
    otherwise create an empty programs data list.
    
    Return program data list (gv.pd).
    Does not trap write errors if failure to write to persistent storage.
    """
    try:
        with open('./data/programs.json', 'r') as pf:
            pd = json.load(pf)
    except IOError:
        pd = []  # A config file -- return default and create file if not found.
        with open('./data/programs.json', 'w') as pf:
            json.dump(gv.pd, pf, indent=4, sort_keys=True)
    return pd


###
# Load user configurable defaults from persistent storage.
###

update_default_sd()       # Override default sd[] with values from ./data/sd.json.
snames = station_names()  # Load station names from ./data/snames.json.
pd = load_programs()      # Load program data from ./data/programs.json.


###
# Setup gv properties not stored on disk.
###

# Hardware setup and ownership is done using config file and plugins setup.
# use_gpio_pins is kludge to force bit_bang shift register to not affect any
# I/O interfaces.  e.g. allow the plugin relay_board to assume ownership of
# valve interface.
# Allow gpio use for bit_bang shift register. No effect on rain_sense or relay.
use_gpio_pins = True

use_pigpio = sd['pigpio']
platform = ''  # Must be defined before importing gpio_pins where it is set.
vc_types = None # Will be copy of vc_types defined in valve_controller.

nowt = time.localtime()
now = timegm(nowt)
tz_offset = int(time.time() - timegm(time.localtime()))  # Compatible with Javascript (negative tz shown as positive value).
plugin_menu = []  # Empty list of lists for plugin links (e.g. ['name', 'URL']).

srvals = [0] * (sd['nst'])  # Shift Register values.
output_srvals = [0] * (sd['nst'])  # Shift Register values last set by set_output().
output_srvals_lock = RLock()
rovals = [0] * sd['nbrd'] * 7  # Run Once durations.
plugin_data = {}  # Empty dictionary to hold plugin based global data.
ps = []  # Program schedule (used for UI display).
for i in range(sd['nst']):
    ps.append([0, 0])

pon = None  # Program on (Holds program number of a running program).
sbits = [0] * (sd['nbrd'] + 1)  # Used to display stations that are on in UI.

rs = []  # Run schedule.
for j in range(sd['nst']):
    rs.append([0, 0, 0, 0])  # Scheduled start time, scheduled stop time, duration, program index.

lrun = [0, 0, 0, 0]  # Station index, program number, duration, end time (Used in UI).
scount = 0  # Station count, used in set station to track on stations with master association.

vc = None    # Valve Controller instance or None

###
# The options list configures paramaters for the web GUI.
###
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
    [_("Individual Duration"), "boolean", "idd", _("Allow each station to have its own run time in programs."), _("Station Handling")],
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
