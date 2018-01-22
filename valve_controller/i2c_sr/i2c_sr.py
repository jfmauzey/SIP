import valve_controller.valve_controller_factory as vcf
from valve_controller import vct_installed, vc_types
from gpio_pins import map_gpio_pin, config_gpio_output, gp_write, gp_cleanup

class SliceOfPi_IOExpander(vcf.VirtualValveController):
    """description of class"""

    def __init__(self,nst=8, alr = False, quiet = False):
        super(SliceOfPi_IOExpander, self).__init__(nst, alr, quiet)
        #TO DO: need to initialize outputs
        #self.setOutputs([0] * self.nst)
        self.pins = {} #mapping for hardare resources e.g. pins, busses, ...

    def cleanup_hw(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)

    def __del__(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)
        super(SliceOfPi_IOExpander, self).__del__()

    @classmethod
    def descrip(cls):
        return 'i2c_sr: IO expander using one or more MCP2017'


vct_installed['i2c_sr'] = SliceOfPi_IOExpander
vc_types['i2c_sr'] = SliceOfPi_IOExpander.descrip()
