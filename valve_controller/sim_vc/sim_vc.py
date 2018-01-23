
import valve_controller.valve_controller_factory as vcf
from valve_controller import vct_installed, vc_types
from gpio_pins import map_gpio_pin, config_gpio_output, gp_write, gp_cleanup

class SimulatedValveController(vcf.VirtualValveController):
    """description of class"""

    def __init__(self,nst=8, alr = False, quiet = False):
        super(SimulatedValveController, self).__init__(nst, alr, quiet)
        #TO DO: need to initialize outputs
        #self.setOutputs([0] * self.nst)
        self.pins = { #simulated mapping for hardare resources e.g. pins, busses, ...
            'pin_sr_dat' : 3,
            'pin_sr_clk' : 4,
            'pin_sr_noe' : 5,
            'pin_sr_lat' : 6
            }

    def cleanup_hw(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)

    def __del__(self):
        pins = [pin for pin in self.pins.itervalues()]
        gp_cleanup(pins)
        super(SimulatedValveController, self).__del__()

    @classmethod
    def descrip(cls):
        return 'sim_vc: Simulated Valve Controller sans hardware'


vct_installed['sim_vc'] = SimulatedValveController
vc_types['sim_vc'] = SimulatedValveController.descrip()
