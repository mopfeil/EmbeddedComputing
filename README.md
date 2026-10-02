# EmbeddedComputing
Github für die Embedded Computing Vorlesung / Lab

Prerequisites for working with the robot:
• ET1 Hardware, Micro USB Charger (Phone charger).
• Basic Knowledge on remote access Control using a Wireless Access Point (WLAN AP).

IMPORTANT: Before powering the ET1 make sure that you have
positioned the ET1 so that it cannot fall of should it start to
move!

Preparation:
• Install the VNC Viewer using the link below.
https://www.realvnc.com/en/connect/download/viewer/raspberrypi/
• Use the link below as a guide on access point WLAN connection.
https://www.bitblokes.de/raspap-raspberry-pi-als-hotspot-access-point-wlan-wi-fi-benutzen
https://raspap.com

Startup:
Prepare the ET1 by either connecting the Raspberry PI to a USB Power Supply
directly on the Raspi Board (as shown at the handover) or by charging the 9V
Battery using the Micro USB Charging port and powering the Raspberry PI on using
the switches on the ET1. The Switch close to the USB Ports at the rear end of the
board switches the battery system on, powering the motors. To power the
Raspberry Pi from the battery you need to set the second switch close to the front
to the ON-Position (labelled on the board).

Powering the Raspberry Pi from the battery is problematic from the point of view 
that it will run out suddenly and could lead to loss of
unsaved work. However, if your power supply does not deliver enough current, the
networked connection might be unstable. Therefore if you find that connecting
through the wireless is not stable you might consider running it from the battery
instead.

a) Power the Raspberry Pi on and wait until the wireless access point comes
up. This might take a few minutes. Connect your Wireless Adapter to the ET1
using the WLAN AP.
SSID: raspi-webgui
Passwort: ChangeMe
IP-Adresse des Hotspots: 10.3.141.1
WebGUI (Administration)
10.3.141.1
User: admin
PW: secret

b) Using the VNC Viewer connect to the Raspberry Pi and access the desktop.

c) Verify the image has the necessary programs on.
Programs to Verify
Thonny (Python IDE)
C IDE
node.js
Firefox
