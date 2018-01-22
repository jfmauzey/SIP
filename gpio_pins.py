# -*- coding: utf-8 -*-

import os
import subprocess
import gv

###
#fall through logic to configure platform specific runtime requirements
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
    #map header connector pins to gpio names/nums
    if rev == 1:
        # map 26 physical pins (1based) with 0 for pins that do not have a gpio number
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,0,0,1,0,4,14,0,15,17,18,21,0,22,23,0,24,10,0,9,25,11,8,0,7]
        else:
            gv.pin_map = [0,0,0,0,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26]
    elif rev == 2:
        # map 26 physical pins (1based) with 0 for pins that do not have a gpio number
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,2,0,3,0,4,14,0,15,17,18,27,0,22,23,0,24,10,0,9,25,11,8,0,7]
        else:
            gv.pin_map = [0,0,0,0,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26]
    elif rev == 3:
        # map 40 physical pins (1based) with 0 for pins that do not have a gpio number
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,2,0,3,0,4,14,0,15,17,18,27,0,22,23,0,24,10,0,9,25,11,8,0,7,0,0,5,0,6,12,13,0,19,16,26,20,0,21]
        else:
            gv.pin_map = [0,0,0,3,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26,0,0,29,0,31,32,33,0,35,36,37,38,0,40]
    else:
        print 'Unknown pi pin revision.  Using pin mapping for rev 3'
        # map 40 physical pins (1based) with 0 for pins that do not have a gpio number
        if gv.use_pigpio:
            gv.pin_map = [0,0,0,2,0,3,0,4,14,0,15,17,18,27,0,22,23,0,24,10,0,9,25,11,8,0,7,0,0,5,0,6,12,13,0,19,16,26,20,0,21]
        else:
            gv.pin_map = [0,0,0,3,0,5,0,7,8,0,10,11,12,13,0,15,16,0,18,19,0,21,22,23,24,0,26,0,0,29,0,31,32,33,0,35,36,37,38,0,40]

except ImportError:
    try:
        import Adafruit_BBIO.GPIO as GPIO  # Required for accessing General Purpose Input Output pins on Beagle Bone Black
        gv.platform = 'bo'
        gv.pin_map = [None]*11 # map only the pins we are using
        gv.pin_map.extend(['P9_'+str(i) for i in range(11,17)])
    except ImportError:
        if os.name == 'nt':
            gv.platform = 'nt'
            gv.pin_map = [i for i in range(27)] # simulate 26 pins all mapped.
        else:
            print 'Error: gpio_pins - No GPIO module loaded for {} platform'.format(os.name)
            gv.platform = ''  # if no platform, allows program to still run.
            gv.pin_map = [i for i in range(27)] # assume 26 pins all mapped.  Maybe we should not assume anything, but...

###
#gv.platform and gv.pin_map are now defined correctly for the runtime of this module
###

###
#fall through logic to define interface functions to control the hardware
###

#the following two arrays paralell the gv.pin_map array
claimed_gpio_pins = [False] * len(gv.pin_map) 
shareable_gpio_pins = [False] * len(gv.pin_map) 

def map_gpio_pin(pinNum, shareable = False):
    if gv.pin_map[pinNum]: #pin is mappable if not 0 or None
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


if gv.platform == 'pi' and gv.use_pigpio:
    try:
        import pigpio
        pi = pigpio.pi()

        def config_gpio_output(pin):
            pi.set_mode(pin, pigpio.OUTPUT)
        
        def config_gpio_input(pin, pullup='off'):
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

        def gp_cleanup(header_pins = None): #untested
            if header_pins == None:  #unmap all claimed pins
                  header_pins = [x for x in range(len(gv.pin_map))]
            for i in header_pins:
                if claimed_gpio_pins[i]:
                    config_gpio_input(gv.pin_map[i]) #config pin as a high impedance input
                    unmap_gpio_pin(i)

    except ImportError: #assume default RPi libraries are available
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD) #IO channels are identified by header connector pin numbers. Pin numbers are 

        def config_gpio_output(pin):
            GPIO.setup(pin, GPIO.OUT)

        def config_gpio_input(pin, pullup='off'):
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
            if header_pins == None:  #unmap all claimed pins
                  header_pins = [x for x in range(len(gv.pin_map))]
            for i in header_pins:
                if claimed_gpio_pins[i]:
                    config_gpio_input(gv.pin_map[i]) #config pin as a high impedance input
                    unmap_gpio_pin(i)

elif gv.platform == 'pi' or gv.platform == 'bo':
    GPIO.setwarnings(False)
    if gv.platform == 'pi':
        GPIO.setmode(GPIO.BOARD) #IO channels are identified by header connector pin numbers. Pin numbers are 

    def config_gpio_output(pin):
        GPIO.setup(pin, GPIO.OUT)

    def config_gpio_input(pin, pullup='off'):
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
        if header_pins == None:  #unmap all claimed pins
              header_pins = [x for x in range(len(gv.pin_map))]
        for i in header_pins:
            if claimed_gpio_pins[i]:
                config_gpio_input(gv.pin_map[i]) #config pin as a high impedance input
                unmap_gpio_pin(i)

elif gv.platform == 'nt' or gv.platform == '': #use simulated IO
    def config_gpio_output(pin):
        pass

    def config_gpio_input(pin, pullup='off'):
        pass

    def gp_write(pin,val):
        pass

    def gp_read(pin):
        return 1      #dummy return for simulation

    def gp_cleanup(header_pins = None):
        '''The simulated cleanup only needs to unmap the used pins.
        Making the config calls is not needed. However the simulation
        runs truer to the actual code used to control physical hardware.'''

        if header_pins == None:  #unmap all claimed pins
              header_pins = [x for x in range(len(gv.pin_map))]
        for i in header_pins:
            if claimed_gpio_pins[i]:
                config_gpio_input(gv.pin_map[i]) #config pin as a high impedance input
                unmap_gpio_pin(i)

else: #Oppps! The dreaded configuration errror
    print 'Error: gpio_pins -- configuring platform "{}"'.format(gv.platform)
    print 'Should probably abort execution.'

###
#platform specific runtime config is complete
###

###
#Kludge: Pin allocation and setup should be moved out of gpio_pins
#e.g.    pin_rain_sense = gpio_pins.map_gpio_pin(8,shareable=False)
###
global pin_rain_sense

def config_pin_rain_sense():
    if gv.platform == 'pi':  # If this will run on Raspberry Pi:
        pin_rain_sense = map_gpio_pin(8,shareable=False)
    elif gv.platform == 'bo':  # If this will run on Beagle Bone Black:
        pin_rain_sense = map_gpio_pin(15,shareable=False)
    else: #for simulation
        pin_rain_sense = map_gpio_pin(1,shareable=False)
    config_gpio_input(pin_rain_sense, pullup='up')
    return pin_rain_sense

#global pin_relay
#def config_pin_relay():
#    if gv.platform == 'pi':  # If this will run on Raspberry Pi:
#        pin_relay = map_gpio_pin(10,shareable=False)
#    elif gv.platform == 'bo':  # If this will run on Beagle Bone Black:
#        pin_relay = map_gpio_pin(16,shareable=False)
#    else: #for simulation
#        pin_relay = map_gpio_pin(2,shareable=False)
#    config_gpio_output(pin_relay)
#    return pin_relay

from blinker import signal
zone_change = signal('zone_change')

def set_output():
    """
    Activate triacs according to shift register state.
    If using SIP with shift registers and active low relays, uncomment the line indicated below.
    """

    with gv.output_srvals_lock:
        gv.output_srvals = gv.srvals
        gv.vc.setOutput(gv.output_srvals)
        zone_change.send()
