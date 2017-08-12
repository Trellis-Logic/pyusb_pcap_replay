# @author Dan Walkes
# @date 2017-07-13
# @brief Script to parse PDML file output from Wireshark from
#       USB PDML captures
#
import xml.etree.ElementTree as ET
import sys
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A class for parsing PDML files from Wireshark
class PDMLParse:
    def __init__(self,filename):
        self.filename=filename

    def get_root(self):
        tree=ET.parse(self.filename)
        return tree.getroot()

    # @param root element for parsing packets from a wireshark PDML file
    # @return an array of packet dictionaries with
    #   ['type'] = 'control' for USB control packet or  'bulk' for bulk transfer
    #   ['direction'] = 'in' or 'out' depending on USB direction WRT host
    #   ['data'] = hex data in ASCII format
    def get_packets(self):
        root=self.get_root()
        packets=[]
        for packet in root.iter('packet'):
            usb_pkt = {}
            for child in packet:
                if child.attrib['name'] == 'usb':
                    proto=child
                    for child in proto:
                        if child.attrib['name'] == 'usb.transfer_type':
                            if child.attrib['value'] == '02':
                                usb_pkt['type']='control'
                            else:
                                usb_pkt['type']='bulk'
                        # Newer versions of wireshark use endpoint_addresss instead of endpoint_number
                        if child.attrib['name'] == 'usb.endpoint_number' or child.attrib['name'] == 'usb.endpoint_address':
                            if child.attrib['showname'].find('Direction: IN') is not -1:
                                usb_pkt['direction'] = 'in'
                            else:
                                usb_pkt['direction']='out'
                elif child.attrib['name'] == 'fake-field-wrapper' and 'type' in usb_pkt :
                    proto=child
                    for child in proto:
                        if child.attrib['name'] == 'usb.capdata':
                            usb_pkt['data'] = child.attrib['value']
            if usb_pkt is not None:
                packets.append(usb_pkt)
        return packets

    # @return a reordered version of @param sequece with @param move_transfer after
    # @param after_transfer
    # I originally thought the bulk transfer sequences might be out of order in the pcap trace
    # on further investigation I found they were note
    # Here's an example of how you can use this function to test reordering
    #    self.reorder_transfer(get_bulk_packet_sequence(self),{'type': 'bulk', 'direction': 'in',
    #                                 'data': '4f4b41593a20657870656374696e6720646f776e6c6f616400'},
    #                                {'type': 'bulk', 'direction': 'out', 'data': '00000000'})
    def reorder_transfer(self,sequence,move_transfer,after_transfer):
        newsequence=sequence
        try:
            move_index=newsequence.index(move_transfer)
            beforesequence=newsequence[0:move_index]
            aftersequence=newsequence[move_index+1:]
            after_index=aftersequence.index(after_transfer)
            aftersequence.insert(after_index+1,move_transfer)
            newsequence=beforesequence+aftersequence
        except ValueError:
            logger.warn("Did not find move transfer " + str(move_transfer) + " and after transfer " + str(after_transfer) + " in trace")
        return newsequence

    # @return an array of packet dictionaries with
    #   ['type'] = 'enumeration' for (re)enumeration sequences or  'bulk' for bulk transfer
    #   ['direction'] = 'in' or 'out' depending on USB direction WRT host
    #   ['data'] = hex data in ASCII format
    def get_bulk_packet_sequence(self):
        packets=self.get_packets()
        bulksequence=[]
        in_enumeration=False
        for packet in packets:
            if packet['type'] is 'bulk':
                bulksequence.append(packet)
                in_enumeration=False
            elif packet['type'] is 'control':
                if in_enumeration is not True:
                    bulksequence.append({'type':'enumeration'})
                    in_enumeration=True
        return bulksequence

    def dump_usb_data(self,packets):
        for packet in packets:
            print(packet)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("usage: pdml_parse <path_to_pdml_file>")
    else:
        parser=PDMLParse(sys.argv[1])
        print("USB Data:")
        parser.dump_usb_data(parser.get_packets())
        print("Bulk packet sequence:")
        bulk_sequence=parser.get_bulk_packet_sequence()
        parser.dump_usb_data(bulk_sequence)
