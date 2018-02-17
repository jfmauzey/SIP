# -*- coding: utf-8 -*-

class ValveControllerBaseType(object):
    def __init__(self, *args, **kwargs):
        pass

    def set_output(srvals):
        pass

class BBSR(ValveControllerBaseType):
    def __init__(self, num_stations=1, active_low_relay=False, num_boards=0):
        return super(ValveController, self).__init__(*args, **kwargs)

class ValveController(object):
    def __init__(self, vc_type='bbsr', num_stations=1, active_low_relay=False, num_boards=0):
        if vc_type == 'bbsr':
            vc = BBSR(num_stations, active_low_relay, num_boards)
        else:
            vc = None
        return vc