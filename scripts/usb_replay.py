# @author Dan Walkes
# @date 2017-07-13
# @brief Script to replay an exported wireshark pdml file through USB using Pyusb
#
import usb.core
import usb.util
import sys
import binascii
import time
from pdml_parse import PDMLParse

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class USBReplayException(Exception):
    pass

DEFAULT_TIMEOUT_MS = 1000
class USBReplay:

    def __init__(self,vid,pid):
        self.vid=vid
        self.pid=pid

    # Re-enumerate the device, waiting for it to be removed if it is currently attached
    # @return a dictionary defining the re-enumerated device
    #   'dev' is the device returned by usb.core
    #   'epin' is the in endpoint
    #   'epout' is the out endpoint
    def do_re_enumerate(self,first_enumerate=False):
        dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if dev is not None:
            if first_enumerate is True:
                print("Please power down device to start")
                sys.stdout.flush
            while (dev is not None):
                dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)

        if first_enumerate is True:
            print("Please power on device with USB connected")
            sys.stdout.flush
        # find our device
        dev = None
        while (dev is None):
            dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)

        if first_enumerate is True:
           print("Found device with VID " + str(VID) + " and PID " + str(PID))

        try:
            # Assumes first configuration is the only active one
            dev.set_configuration()
        except usb.core.USBError:
            logger.warn("Caught usb error attempting set configuration, attempting re-enumerate after 100ms wait")
            time.sleep(0.100)
            dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
            dev.set_configuration()

        # get an endpoint instance
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]

        epout = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match= \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT)

        assert epout is not None

        epin = usb.util.find_descriptor(
            intf,
            # match the first IN endpoint
            custom_match= \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN)

        assert epin is not None
        if first_enumerate is False:
            time.sleep(2)
        return { 'dev' : dev, 'epout' : epout, 'epin' : epin }

    def do_replay_sequence(self,pdml):
        packets=pdml.get_bulk_packet_sequence()
        dev_dict=self.do_re_enumerate(True)
        packet_count=1
        for packet in packets:
            if packet['type'] == 'bulk':
                if packet['direction'] == 'in':
                    # TODO: figure out why the last byte of data received is giving "pipe error"
                    len_bytes=(len(packet['data'])/2)
                    buffer=dev_dict['dev'].read(dev_dict['epin'],len_bytes,DEFAULT_TIMEOUT_MS)
                    asciibuffer=binascii.b2a_hex(buffer)
                    if not packet['data'].upper().startswith(asciibuffer.upper()):
                        raise USBReplayException("Expected data " + packet['data'].upper() + " with length " + str(len(packet['data'])/2) + " bytes but found " + asciibuffer.upper() + " at packet " + str(packet_count))
                    else:
                        logger.debug("Read packet " + str(packet_count) + " with data " + packet['data'])
                elif packet['direction'] == 'out':
                    dev_dict['dev'].write(dev_dict['epout'], binascii.a2b_hex(packet['data']), DEFAULT_TIMEOUT_MS)
                    logger.debug("Wrote packet " + str(packet_count) + " with data " + packet['data'])
                packet_count=packet_count+1
            elif packet['type'] == 'enumeration':
                if packet_count > 1:
                    logger.info("Starting re-enumeration")
                    dev_dict=self.do_re_enumerate()
                    logger.info("Re-enumeration complete")

    # Replay the USB sequence in @param file where the file is a PDML export wireshark pcap usb capture
    # class, see pdml_parse.py
    def replay(self,pdml):
        self.do_replay_sequence(pdml)



if __name__ == '__main__':
    # Hard coded to AM3517 VID/PID combo, probably should make this configurable if it's useful on other devices
    VID=0x0451
    PID=0xd009

    if len(sys.argv) != 2:
        print("usage: usb_replay <path_to_pdml_file>")
        exit(1)

    USBReplay(VID,PID).replay(PDMLParse(sys.argv[1]))
    print("complete with success")
