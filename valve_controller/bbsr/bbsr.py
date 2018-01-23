import valve_controller.valve_controller_factory as vcf
from valve_controller import vct_installed, vc_types

from gpio_pins import map_gpio_pin, config_gpio_output, gp_write, gp_cleanup
import gv

class BitBangShiftReg(vcf.VirtualValveController):
    """description of class"""

    def __init__(self, nst = 8, alr = False, quiet=False):
        super(BitBangShiftReg, self).__init__(nst, alr, quiet)
        self._setup_pins()
        self.setOutput([0] * self.nst)

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
        """Set the state of each output pin on the shift register from the srvals list."""
        self._write0(self.pin_sr_clk)
        self._write0(self.pin_sr_lat)
        for s in range(len(srvals)):
            self._write0(self.pin_sr_clk)
            if srvals[-1-s]:
                self._on(self.pin_sr_dat) #writes logical ON
            else:
                self._off(self.pin_sr_dat) #writes logical OFF
            self._write1(self.pin_sr_clk)
        self._write1(self.pin_sr_lat)
    
    def setOutput(self,vals):
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

        #allocate pins used by shift reg from the gpio pin mapper
        self.pin_sr_dat = map_gpio_pin(self.pins['pin_sr_dat'], shareable=False)
        self.pin_sr_clk = map_gpio_pin(self.pins['pin_sr_clk'], shareable=False)
        self.pin_sr_noe = map_gpio_pin(self.pins['pin_sr_noe'], shareable=False)
        self.pin_sr_lat = map_gpio_pin(self.pins['pin_sr_lat'], shareable=False)

        #Initialize hardware control for the gpio pins
        config_gpio_output(self.pin_sr_noe)
        config_gpio_output(self.pin_sr_clk)
        config_gpio_output(self.pin_sr_dat)
        config_gpio_output(self.pin_sr_lat)

        ### initial state for shift reg control pins
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
        super(BitBangShiftReg, self).__del__()

    @classmethod
    def descrip(cls):
        return 'bbsr: BitBanged shift reg compatible with OSPi/SIP'

vct_installed['bbsr'] = BitBangShiftReg
vc_types['bbsr'] = BitBangShiftReg.descrip()
