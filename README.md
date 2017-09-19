# Pyusb Pcap Replay Overview and Purpose

This repository contains scripts originally written for bare metal programming of the [TI AM3517](http://www.ti.com/product/AM3517), a replacement for the
[TI's FLASHTOOL](http://www.ti.com/tool/FLASHTOOL).  The TI FLASHTOOL only supports specific host platforms (XP and Windows 7 32 bit).  The
scripts allow you to perform the same functions on any system with support for python and [pyusb](https://walac.github.io/pyusb/).  See [this thread](https://gforge.ti.com/gf/project/flash/forum/?_forum_action=ForumMessageBrowse&thread_id=4357&action=ForumBrowse&forum_id=665) for more information about the motivation and usage with the TI AM3517

Although it was originally intended for replacing the TI flash tool, this repository will be useful in any case that you'd like
to replay a USB sequence captured from another device with [usbpcap](http://desowin.org/usbpcap/tour.html), possibly useful for other
obsolete and no longer supported manufacturing tools.  You just need to set the VID and PID appropriately in usb_replay.py to correspond
to other devices

## Installing

### Windows
1. Install Python and ensure it is in your PATH
2. Open a git command prompt as Administrator (Git Bash, right click->Open as Administrator) and cd to the scripts directory
3. Run ```./install_windows.sh```
4. Download the [zadig](http://zadig.akeo.ie/) tool.
5. Open Zadig and select Device->Load Preset Device
6. Select the zadig.cfg file in the "config" directory of this repo
7. Click "Install Driver"
#### Windows 8.1 or later instructions
1. On Windows 8.1 or later, you will need to disable the BOS descriptor enumeration using a special registry key.  This is only necessary for the TI AM3517 bootloader, which doesn't support this descriptor.
* Open regedit and go to HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\usbflags\0451D0090000 (create this key if it doesn't exist).
* Add a Binary value with name "SkipBOSDescriptorQuery" and value 01 00 00 00
* On Windows 8.1 you may also need to install [KB 2967917](https://www.microsoft.com/en-us/download/details.aspx?id=43488).
This is not needed on Windows 10.
* See the video at [this link](https://www.youtube.com/watch?v=_Utrb5hNRZk) for details.

## Setup Capture
* Start by capturing a sequence of the programming operations performed by [TIs FLASHTOOL](http://www.ti.com/tool/FLASHTOOL).  Install this tool on a Windows XP or Windows 7 32 bit system.
* Download and install [wireshark](https://www.wireshark.org/) and [usbpcap](http://desowin.org/usbpcap/tour.html).  Use the instructions on the usbpcap site to configure usbpcap settings.

## Run Capture
1.  Start the capture on the usbpcap endpoint configured in the previous step.
2.  Run the TI Flash utility to capture the event you'd like to replay.
3.  Filter the trace to only contain data for the specified device if more than one device is included on the root hub.  Use a filter like:
```
usb.src == "2.3.0" || usb.src == "2.3.1" || usb.dst == "2.3.0" || usb.dst == "2.3.1"
```
Where 2.3.0 and 2.3.1 are the endpoints shown in the wireshark "Source" and "Destination" columns for the device you want to capture.
4.  Use File->Export Specified Packets to export the filtered data to a .pcap file.
5.  Open the pcap file with filtered content
6.  Export to the PDML format in wireshark using File->Export Packet Dissections->as XML - "PDML" packet details file
rt to this format using File->Export Packet Dissections->as XML - "PDML" packet details file
 * Make sure "Packet Details" include "All expanded"
 * Make sure "Packet Bytes" checkbox is checked.
 * Make sure "Packet Details" include "All expanded"
 * Make sure "Packet Bytes" checkbox is checked.

## Replay capture file
Once you've captured the file on the XP or Windows 7 32 bit machine, you can replay the trace on any system supporting python and pyusb
1. Connect the usb otg port to the PC
2. Run ```python usb_replay.py <path_to_pdml_file>``` where <path_to_pdml_file> is the path to the file captured using pcap and expored to PDML as described above.
3. Connect the device when prompted by the script.
4. When using the development board, ensure the dip switches are set such that USB boot attempts will occur early in the boot sequence.  Switch setting 1 and 4 on puts USB boot first in the boot sequence.


## Troubleshooting/Known Issues
* On my Windows 10 system, approximately 1 in 10 attempts I see a USBError during initial enumeration.  Errors are "Access denied (insufficient permissions)"
* If you see "Entity Not Found" continuously, retry the Zadig driver install steps.
