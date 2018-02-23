# -*- coding: utf-8 -*-

from gpio_pins import map_gpio_pin, config_gpio_output, gp_write, gp_cleanup
import gv

from __future__ import print_function

vc_types = {
    'bbsr' : BBSR,
    'disabled' : None,
    'default' : BBSR,
    }

class ValveController(object):
    """
    Models the hardware interface that controls irrigation valve relays.
    Each valve controller has a set of attributes that define the stations
    controlled by the hardware. The number of stations may be modified by
    the user using the web interface. The user may also change the logic
    level associated with the meaning of "ON" (i.e. High True versus Low True
    logic).
    """

    def __init__(self, nst=8, alr=False, quiet=True):
        self.pins = {} #contains mapping for hardare resources e.g. pins, busses, ...
        if quiet:
          self._dbg = lambda *args, **kw: None
        else:
          self._dbg = lambda *args, **kw: print(*args,**kw)
        self.nst = nst
        self.alr = alr              # 1==ActiveLowRelay 0==ActiveHighRelay
        if self.alr == True:        #use low true logic
          self._on = self._write0
          self._off = self._write1
        else:                       #use high true logic
          self._on = self._write1
          self._off = self._write0

    def setActiveLow(self):         #use low true logic
        self._on = self._write0
        self._off = self._write1

    def setActiveHigh(self):       #use high true logic
        self._on = self._write1
        self._off = self._write0

    def _write0(self,pin):
        self._dbg("Simulated write 0 to pin {}".format(pin))

    def _write1(self,pin):
        self._dgb("Simulated write 1 to pin {}".format(pin))

    def setNumberStations(self, nst):
        self.nst = nst

    def set_output(self, values):
        pass

    def cleanup_hw(self):
        pass


class BBSR(ValveController):
    """
    BBSR uses four gpio pins to interface to a shift register implemented
    using one or more 74HC595 discreet parts. There is no feedback from the
    shift register to know if the 74HC595 device(s) is attached.
    """
    def __init__(self, nst = 8, alr = False, quiet=True):
        super(BBSR, self).__init__(nst, alr, quiet)
        self._setup_pins()
        self.set_output([0] * self.nst)

    def _write0(self,pin):
        gp_write(pin,0)

    def _write1(self,pin):
        gp_write(pin,1)

    def disableShiftRegisterOutput(self):
        """Disable output from shift register."""
        self._write1(self.pin_sr_noe)

    def enableShiftRegisterOutput(self):
        """Enable output from shift register."""
        self._write0(self.pin_sr_noe)

    def setShiftRegister(self,srvals):
        """
        Set the state of each output pin on the shift register from the srvals list.
        srvals uses high true logic: ON=1, OFF=0. The shift register code translates
        a station's logical state to the drive level required by the relay.  This is
        configured during station setup based on the seting of gv.sd['alr'].
        """
        self._write0(self.pin_sr_clk)
        self._write0(self.pin_sr_lat)
        for s in range(len(srvals)):
            self._write0(self.pin_sr_clk)
            if srvals[gv.sd['nst']-1-s]: # Shift bits in reverse order.
                self._on(self.pin_sr_dat) # Writes logical ON.
            else:
                self._off(self.pin_sr_dat) # Writes logical OFF.
            self._write1(self.pin_sr_clk)
        self._write1(self.pin_sr_lat)
    
    def set_output(self,vals):
        """Activate triacs according to shift register state."""
        self.disableShiftRegisterOutput()
        self.setShiftRegister(vals)
        self.enableShiftRegisterOutput()
    
    def _setup_pins(self):
        """
        Define and setup GPIO pins for shift register operation
        Maps the symbolic pin name to the physical hardware pin number
        and initializes the hardware resoures required.
        """
        if gv.platform == 'pi':  # If this will run on Raspberry Pi:
            self.pins['pin_sr_dat'] = 13 #Header pin number
            self.pins['pin_sr_clk'] = 7
            self.pins['pin_sr_noe'] = 11
            self.pins['pin_sr_lat'] = 15
        elif gv.platform == 'bo':  # If this will run on Beagle Bone Black:
            self.pins['pin_sr_dat'] = 11 #Header number for Connector P9
            self.pins['pin_sr_clk'] = 13
            self.pins['pin_sr_noe'] = 14
            self.pins['pin_sr_lat'] = 12
        else:                      # for simulation
            self.pins['pin_sr_dat'] = 3
            self.pins['pin_sr_clk'] = 4
            self.pins['pin_sr_noe'] = 5
            self.pins['pin_sr_lat'] = 6

        # Allocate pins used by shift reg from the gpio pin mapper.
        self.pin_sr_dat = map_gpio_pin(self.pins['pin_sr_dat'], shareable=False)
        self.pin_sr_clk = map_gpio_pin(self.pins['pin_sr_clk'], shareable=False)
        self.pin_sr_noe = map_gpio_pin(self.pins['pin_sr_noe'], shareable=False)
        self.pin_sr_lat = map_gpio_pin(self.pins['pin_sr_lat'], shareable=False)

        # Initialize hardware control for the gpio pins.
        config_gpio_output(self.pin_sr_noe)
        config_gpio_output(self.pin_sr_clk)
        config_gpio_output(self.pin_sr_dat)
        config_gpio_output(self.pin_sr_lat)

        ### Initial state for shift reg control pins.
        self._write1(self.pin_sr_noe)
        self._write0(self.pin_sr_clk)
        self._write0(self.pin_sr_dat)
        self._write0(self.pin_sr_lat)
    
    def cleanup_hw(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)

    def __del__(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)

    def __str__(self):
         return 'bbsr: Bit Banged Shift Register'

class VC_SIM(ValveController):
    """
    VC_SIM uses four simulated pins to allow the SIP application to run on
    any platform:
      Platforms that do not have IO.
      Can be used for testing.
      Can be used for training to learn how use the SIP app.
         How programs schedule stations.
         How programs multiple programs behave when using seq or concurrent mode.
         How manual mode interacts with program scheduling.
    """
        self._setup_pins()
        self.set_output([0] * self.nst)
    def __init__(self,nst=8, alr = False, quiet = False):
        super(VC_SIM, self).__init__(nst, alr, quiet)
        self._setup_pins()
        self.set_output([0] * self.nst)

    def cleanup_hw(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)

    def __del__(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)
        super(VC_SIM, self).__del__()

    def __str__(self):
        return 'vc_sim: Simulated Valve Controller sans hardware'

    def _write0(self,pin):
        gp_write(pin,0)

    def _write1(self,pin):
        gp_write(pin,1)

    def disableShiftRegisterOutput(self):
        """Disable output from shift register."""
        self._write1(self.pin_sr_noe)

    def enableShiftRegisterOutput(self):
        """Enable output from shift register."""
        self._write0(self.pin_sr_noe)

    def setShiftRegister(self,srvals):
        """
        Set the state of each output pin on the shift register from the srvals list.
        srvals uses high true logic: ON=1, OFF=0. The shift register code translates
        a station's logical state to the drive level required by the relay.  This is
        configured during station setup based on the seting of gv.sd['alr'].
        """
        self._write0(self.pin_sr_clk)
        self._write0(self.pin_sr_lat)
        for s in range(len(srvals)):
            self._write0(self.pin_sr_clk)
            if srvals[gv.sd['nst']-1-s]: # Shift bits in reverse order.
                self._on(self.pin_sr_dat) # Writes logical ON.
            else:
                self._off(self.pin_sr_dat) # Writes logical OFF.
            self._write1(self.pin_sr_clk)
        self._write1(self.pin_sr_lat)
    
    def set_output(self,vals):
        self.disableShiftRegisterOutput()
        self.setShiftRegister(vals)
        self.enableShiftRegisterOutput()
    
    def _setup_pins(self):
        """
        Define and setup simulated GPIO pins for shift register operation.
        """
        self.pins['pin_sr_dat'] = 1
        self.pins['pin_sr_clk'] = 2
        self.pins['pin_sr_noe'] = 3
        self.pins['pin_sr_lat'] = 4

        # Allocate pins used by shift reg from the gpio pin mapper.
        self.pin_sr_dat = map_gpio_pin(self.pins['pin_sr_dat'], shareable=False)
        self.pin_sr_clk = map_gpio_pin(self.pins['pin_sr_clk'], shareable=False)
        self.pin_sr_noe = map_gpio_pin(self.pins['pin_sr_noe'], shareable=False)
        self.pin_sr_lat = map_gpio_pin(self.pins['pin_sr_lat'], shareable=False)

        # Initialize hardware control for the gpio pins.
        config_gpio_output(self.pin_sr_noe)
        config_gpio_output(self.pin_sr_clk)
        config_gpio_output(self.pin_sr_dat)
        config_gpio_output(self.pin_sr_lat)

        ### Initial state for shift reg control pins.
        self._write1(self.pin_sr_noe)
        self._write0(self.pin_sr_clk)
        self._write0(self.pin_sr_dat)
        self._write0(self.pin_sr_lat)


###
# vc_types maps the Valve Controller name (key) to the class constructor.
### 

vc_types = {
    'bbsr' : BBSR,
    'disable' : None,
    'default' : BBSR,
    'vc_sim' : VC_SIM
    }