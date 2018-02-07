# -*- coding: utf-8 -*-
"""
This module provides the interface to the valve controller and to the rain
sense input.

set_output transfers the state of the global gv.sr_vals to activate sprinkler
valves.

This module provides a common interface to configure, control, and remove
access to the hardware pins attached to the platform.

There are five functions defined in this module that abstract the platform
differences and allow usage of the gpio hardware independent of the platform.
    gp_config_output(pin):
    gp_config_input(pin, pullup='off')
    gp_write(pin,val)
    gp_read(pin)
    gp_cleanup(header_pins = None)

Pins are identified by the number of the hardware connector pin number.
"""

import os
import subprocess
import gv

###
# Fall through logic to configure platform specific runtime requirements.
###

if gv.sd['pigpio']:
    try:
        subprocess.check_output("pigpiod", stderr=subprocess.STDOUT)
        gv.use_pigpio = True
    except Exception:
        print 'pigpio not configured'
        gv.use_pigpio = False       
else:
    gv.use_pigpio = False       

try:
    import RPi.GPIO as GPIO
    gv.platform = 'pi'
    rev = GPIO.RPI_REVISION
    # Map header connector pins to gpio names/nums.
    if rev == 1:
        # Map 26 physical pins (1based) with 0 for pins that do not have a gpio number.
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,0,0,1,0,4,14,0,15,17,18,21,0,22,23,0,24,10,0,9,25,11,8,0,7]
        else:
            gv.pin_map = [0,0,0,0,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26]
    elif rev == 2:
        # Map 26 physical pins (1based) with 0 for pins that do not have a gpio number.
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,2,0,3,0,4,14,0,15,17,18,27,0,22,23,0,24,10,0,9,25,11,8,0,7]
        else:
            gv.pin_map = [0,0,0,0,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26]
    elif rev == 3:
        # Map 40 physical pins (1based) with 0 for pins that do not have a gpio number.
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,2,0,3,0,4,14,0,15,17,18,27,0,22,23,0,24,10,0,9,25,11,8,0,7,0,0,5,0,6,12,13,0,19,16,26,20,0,21]
        else:
            gv.pin_map = [0,0,0,3,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26,0,0,29,0,31,32,33,0,35,36,37,38,0,40]
    else:
        print 'Unknown pi pin revision.  Using pin mapping for rev 3'
        # Map 40 physical pins (1based) with 0 for pins that do not have a gpio number.
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,2,0,3,0,4,14,0,15,17,18,27,0,22,23,0,24,10,0,9,25,11,8,0,7,0,0,5,0,6,12,13,0,19,16,26,20,0,21]
        else:
            gv.pin_map = [0,0,0,3,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26,0,0,29,0,31,32,33,0,35,36,37,38,0,40]

except ImportError:
    try:
        import Adafruit_BBIO.GPIO as GPIO  # Required for accessing General Purpose Input Output pins on Beagle Bone Black.
        gv.platform = 'bo'
        gv.pin_map = [None]*11 # Map only the pins we are using.
        gv.pin_map.extend(['P9_'+str(i) for i in range(11,17)])
    except ImportError:
        if os.name == 'nt':
            gv.platform = 'nt'
            gv.pin_map = [i for i in range(27)] # Simulate 26 pins all mapped.
        else:
            print 'Error: gpio_pins - No GPIO module loaded for {} platform'.format(os.name)
            gv.platform = ''  # If no platform, allows program to still run.
            gv.pin_map = [i for i in range(27)]  # Simulate 26 pins all mapped.

###
# gv.platform and gv.pin_map are now defined correctly for the runtime of this module.
###

###
# Fall through logic to define interface functions to control the hardware.
###

# The following two arrays paralell the gv.pin_map array.
claimed_gpio_pins = [False] * len(gv.pin_map) 
shareable_gpio_pins = [False] * len(gv.pin_map) 

def map_gpio_pin(pinNum, shareable = False):
    """
    Input: pinNum is integer value of the hardware connector.
    Returns: reference to a device hardware port or None if not mappable.
    """

    if gv.pin_map[pinNum]:  # Pin is mappable if not 0 or None.
        if claimed_gpio_pins[pinNum]:
            if shareable_gpio_pins[pinNum]:
                return gv.pin_map[pinNum]
            else:
                print "Error: pin #{} is allocated and not shareable".format(pinNum)
                return None
        else:
            claimed_gpio_pins[pinNum] = True
            shareable_gpio_pins[pinNum] = shareable
            return gv.pin_map[pinNum]
    else:
        print "Error: attempt to use pin #{}. Pin is not useable".format(pinNum)
        return None

def unmap_gpio_pin(pinNum):
    claimed_gpio_pins[pinNum] = False
    shareable_gpio_pins[pinNum] = False


if gv.platform == 'pi' and gv.use_pigpio:  # pigpio support for pi only.
    try:
        import pigpio
        pi = pigpio.pi()

        def gp_config_output(pin):
            pi.set_mode(pin, pigpio.OUTPUT)
        
        def gp_config_input(pin, pullup='off'):
            pi.set_mode(pin, pigpio.INPUT)
            if pullup == 'up':
                pi.set_pull_up_down(pin, pigpio.PUD_UP)
            elif pullup == 'down':
                pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
            else:
                pi.set_pull_up_down(pin, pigpio.PUD_OFF)

        def gp_write(pin,val):
            pi.write(pin,val)

        def gp_read(pin):
            return pi.read(pin)

        def gp_cleanup(header_pins = None):  # Untested.
            """
            Input: header_pins is list of integers corresponding
            to the hardware connector numbering.
            """
            if header_pins == None:  # Unmap all claimed pins.
                  header_pins = [x for x in range(len(gv.pin_map))]
            for i in header_pins:
                if claimed_gpio_pins[i]:
                    gp_config_input(gv.pin_map[i])  # Config pin as a high impedance input.
                    unmap_gpio_pin(i)

    except ImportError:  # Assume default RPi libraries are available.
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)  # IO channels are identified by header connector pin numbers.

        def gp_config_output(pin):
            GPIO.setup(pin, GPIO.OUT)

        def gp_config_input(pin, pullup='off'):
            if pullup == 'up':
                GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            elif pullup == 'down':
                GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            else:
                GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_OFF)
            
        def gp_write(pin,val):
            if val == 0:
                GPIO.output(pin,GPIO.LOW)
            else:
                GPIO.output(pin,GPIO.HIGH)

        def gp_read(pin):
            return GPIO.input(pin)

        def gp_cleanup(header_pins = None):
            """
            Input: header_pins is list of integers corresponding
            to the hardware connector numbering.
            """
            if header_pins == None:  # Unmap all claimed pins.
                  header_pins = [x for x in range(len(gv.pin_map))]
            for i in header_pins:
                if claimed_gpio_pins[i]:
                    gp_config_input(gv.pin_map[i])  # Config pin as a high impedance input.
                    unmap_gpio_pin(i)

elif gv.platform == 'pi' or gv.platform == 'bo':
    GPIO.setwarnings(False)
    if gv.platform == 'pi':
        GPIO.setmode(GPIO.BOARD)  # IO channels are identified by header connector pin numbers.

    def gp_config_output(pin):
        GPIO.setup(pin, GPIO.OUT)

    def gp_config_input(pin, pullup='off'):
        if pullup == 'up':
            GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        elif pullup == 'down':
            GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        else:
            GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_OFF)

    def gp_write(pin,val):
        if val == 0:
            GPIO.output(pin,GPIO.LOW)
        else:
            GPIO.output(pin,GPIO.HIGH)

    def gp_read(pin):
        return GPIO.input(pin)

    def gp_cleanup(header_pins = None):
        """
        Input: header_pins is list of integers corresponding
        to the hardware connector numbering.
        """
        if header_pins == None:  # Unmap all claimed pins.
              header_pins = [x for x in range(len(gv.pin_map))]
        for i in header_pins:
            if claimed_gpio_pins[i]:
                gp_config_input(gv.pin_map[i])  # Config pin as a high impedance input.
                unmap_gpio_pin(i)

elif gv.platform == 'nt' or gv.platform == '':  # Use simulated IO.
    def gp_config_output(pin):
        pass

    def gp_config_input(pin, pullup='off'):
        pass

    def gp_write(pin,val):
        pass

    def gp_read(pin):
        return 1  # Dummy return for simulation.

    def gp_cleanup(header_pins = None):
        """
        The simulated cleanup only needs to unmap the used pins.
        Making the config calls is not needed. However the simulation
        runs truer to the actual code used to control physical hardware.
        """

        if header_pins == None:  # Unmap all claimed pins.
              header_pins = [x for x in range(len(gv.pin_map))]
        for i in header_pins:
            if claimed_gpio_pins[i]:
                gp_config_input(gv.pin_map[i])  # Config pin as a high impedance input.
                unmap_gpio_pin(i)

else:  # Oppps! The dreaded configuration errror.
    print 'Error: gpio_pins -- configuring platform "{}"'.format(gv.platform)
    print 'Should probably abort execution.'

###
# platform specific runtime config is complete.
###

def config_pin_rain_sense():
    if gv.platform == 'pi':  # If this will run on Raspberry Pi.
        prs = map_gpio_pin(8,shareable=False)
    elif gv.platform == 'bo':  # If this will run on Beagle Bone Black.
        prs = map_gpio_pin(15,shareable=False)
    else:  # For simulation.
        prs = map_gpio_pin(5,shareable=False)
    gp_config_input(prs, pullup='up')
    return prs

def config_pin_relay():
    if gv.platform == 'pi':  # If this will run on Raspberry Pi.
        pr = map_gpio_pin(10,shareable=False)
    elif gv.platform == 'bo':  # If this will run on Beagle Bone Black.
        pr = map_gpio_pin(16,shareable=False)
    else:  # For simulation.
        pr = map_gpio_pin(6,shareable=False)
    gp_config_output(pr)
    return pr

###
# Kludge: Pin allocation and setup should be moved out of gpio_pins.
#         Mapping should be done in the module that uses the pin(s).
#  Note: use_gpio_pins does not effect use of relay.
###

pin_relay = config_pin_relay()

from blinker import signal
zone_change = signal('zone_change')

def setup_pins():
    """
    Define and setup GPIO pins for shift register operation
    """

    global pin_sr_dat
    global pin_sr_clk
    global pin_sr_noe
    global pin_sr_lat

    try:
        if gv.platform == 'pi':  # If this will run on Raspberry Pi.
            pin_sr_dat = map_gpio_pin(13,shareable=False)
            pin_sr_clk = map_gpio_pin(7,shareable=False)
            pin_sr_noe = map_gpio_pin(11,shareable=False)
            pin_sr_lat = map_gpio_pin(15,shareable=False)
        elif gv.platform == 'bo':  # If this will run on Beagle Bone Black.
            pin_sr_dat = map_gpio_pin(11,shareable=False)
            pin_sr_clk = map_gpio_pin(13,shareable=False)
            pin_sr_noe = map_gpio_pin(14,shareable=False)
            pin_sr_lat = map_gpio_pin(12,shareable=False)
        else:  # Use simulated IO.
            pin_sr_dat = map_gpio_pin(1,shareable=False)
            pin_sr_clk = map_gpio_pin(2,shareable=False)
            pin_sr_noe = map_gpio_pin(3,shareable=False)
            pin_sr_lat = map_gpio_pin(4,shareable=False)

        gp_config_output(pin_sr_noe)
        gp_config_output(pin_sr_clk)
        gp_config_output(pin_sr_dat)
        gp_config_output(pin_sr_lat)
        gp_write(pin_sr_noe,1)
        gp_write(pin_sr_clk,0)
        gp_write(pin_sr_dat,0)
        gp_write(pin_sr_lat,0)
            
    except AttributeError:
        pass

def disableShiftRegisterOutput():
    """
    Disable (tristate) output from shift register.
    On first call initializes the hardware pins used for the shift reg.
    """

    try:  # Check to see if this is the first time this function is called.
        pin_sr_noe
    except NameError:
        if gv.use_gpio_pins:
            setup_pins()
    try:
        gp_write(pin_sr_noe, 1)
    except Exception:
        pass


def enableShiftRegisterOutput():
    """
    Enable output from shift register.
    """

    try:
        gp_write(pin_sr_noe, 0)
    except Exception:
        pass


def setShiftRegister(srvals):
    """
    Set the state of each output pin on the shift register from the srvals list.
    """

    try:
        gp_write(pin_sr_clk, 0)
        gp_write(pin_sr_lat, 0)
        for s in range(gv.sd['nst']):
            gp_write(pin_sr_clk, 0)
            if srvals[gv.sd['nst']-1-s]:
                gp_write(pin_sr_dat, 1)
            else:
                gp_write(pin_sr_dat, 0)
            gp_write(pin_sr_clk, 1)
        gp_write(pin_sr_lat, 1)
    except Exception:
        pass


def set_output():
    """
    Write contents of shift register to the valve controller hardware outputs.
    """

    with gv.output_srvals_lock:
        gv.output_srvals = gv.srvals
        if gv.sd['alr']:
            gv.output_srvals = [1-i for i in gv.output_srvals]  # Invert logic of shift registers.
        disableShiftRegisterOutput()
        setShiftRegister(gv.output_srvals)  # gv.srvals stores shift register state.
        enableShiftRegisterOutput()
        zone_change.send()
