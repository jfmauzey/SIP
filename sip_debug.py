#sip_debug.py for starting with remote debugging

#for remote debug
import ptvsd
ptvsd.enable_attach('keys2kingdom')
ptvsd.wait_for_attach()

from sip import sip_begin
sip_begin()
