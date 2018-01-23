from __future__ import print_function

class VirtualValveController(object):
    """
    Models the hardware interface that controls irrigation valve relays.
    Each valve controller has a set of attributes that define the stations
    controlled by the hardware. The number of stations may be modified by
    the user using the web interface. The user may also change the logic
    level associated with the meaning of "ON" (i.e. High True versus Low True
    logic).
    """

    def __init__(self, nst=8, alr=False, quiet=False):
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

    def setOutput(self, values):
        pass

    def cleanup_hw(self):
        pass

    @classmethod
    def descrip(cls):
        return 'virtual: VirtualValveController used for demo and debug'

from valve_controller import vct_installed

def ValveControllerFactory(vct,nst=8,alr=False):
    if vct in vct_installed:
        vc = vct_installed[vct](nst,alr,quiet=False)
    elif vct == 'virtual':
        vc = VirtualValveController(nst,alr,quiet=True)
    elif vct == 'none':
        vc = VirtualValveController(nst,alr,quiet=True) #jfm need none handling
    else:
        vc = VirtualValveController(nst,alr)
    print("Creating {} ValveController".format(vct))
    return(vc)

#    import bbsr
#    import i2c_sr

#    if vct == 'bbsr':
#        vc = bbsr.BitBangShiftReg(nst,alr)
#    elif vct == 'i2c_sr':
#        vc = i2c_sr.SliceOfPi_IOExpander(nst,alr)
#    elif vct == 'simulated':
#        vc = VirtualValveController(nst,alr,quiet=False)
#    elif vct == 'virtual':
#        vc = VirtualValveController(nst,alr,quiet=True)
#    elif vct == 'none':
#        vc = VirtualValveController(nst,alr,quiet=True) #jfm need none handling
#    else:
#        vc = VirtualValveController(nst,alr)
#    print("Creating {} ValveController".format(vct))
#    return(vc)