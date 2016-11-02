#!/usr/bin/env python
# -*- coding: utf-8 -*-
#23  Oct 2016

###########################################################################
# Copyright (c) 2015 iRobot Corporation
# Copyright (c) 2016 Charles Xu
#
# http://www.irobot.com/
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
#   Neither the name of iRobot Corporation nor the names
#   of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###########################################################################

###########################################################################
#   
#   The original tethered driving code works well for raspberry pi + irobot create.
#  
#   A few enhanced features:
# 
#   1. Implemented the speed up (Shift-L) and speed down(Crtl-L) function. 
#    (P.S. a Need for Speed fan.)
#  
#   2. For the Raspberry Pi, you can open a socket and connected it with the serial port with ser2net service.
#    You can get it by running:
#    $sudo apt-get install ser2net 
#    Then configure the IP address and port number by adding :
#    $sudo vim /etc/ser2net.conf
#    add the following line in ser2net.conf:
#    19910:telnet:14400:/dev/ttyUSB0:115200 8DATABITS NONE 1STOPBIT LOCAL banner
#    This maps the /dev/ttyUSB0 to the socket with port number 19910 
#    then restart the ser2net service
#    $sudo service ser2net restart
#    
#   3. USB camera for streaming:
#   Install vlc by
#   $ sudo apt-get install vlc
#   it needs to install video4linux2 
#   Initiate vlc streaming from USB camera: 
#   $cvlc --no-audio v4l2:///dev/video0 \
#   $--v4l2-width 1920 --v4l2-height 1080 \ 
#   $--v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1 \
#   $--sout '#standard{access=http{mime=multipart/x-mixed-replace; \
#   $boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8554/}' \ 
#   $-I dummy 
#
#   TODO:
#   
#
#    Tested envionments:
#    1. iRobot Create 2
#    2. Linux raspberrypi 4.4.11-v7+
#   
#    --Charles Xu (xuchi.int@gmail.com)
#
###########################################################################

from Tkinter import *
import tkMessageBox
import tkSimpleDialog

import os
import spur
import struct
import sys, glob # for listing serial ports
import getpass, telnetlib #for telnet

try:
    import serial
except ImportError:
    tkMessageBox.showerror('Import error', 'Please install pyserial.')
    raise

# Set host IP and ser2net port here

host = "192.168.1.10"
port = "19910"
username = "pi"
password = "raspberry"

# Set streaming port here
streamport = "8554"

telnetconnection = None

TEXTWIDTH = 40 # window width, in characters
TEXTHEIGHT = 16 # window height, in lines

VELOCITYCHANGE = 200
ACVECHANGE = 50
ROTATIONCHANGE = 300
ACROCHANGE = 75

helpText = """\
Supported Keys:
P\tPassive
S\tSafe
F\tFull
C\tClean
D\tDock
R\tReset
Space\tBeep
LeftShift\tSpeedUp
LeftCtrl\tSpeedDown
Arrows\tMotion

If nothing happens after you connect, try pressing 'P' and then 'S' to get into safe mode.
"""

class TetheredDriveApp(Tk):
    # static variables for keyboard callback -- I know, this is icky
    callbackKeyUp = False
    callbackKeyDown = False
    callbackKeyLeft = False
    callbackKeyRight = False
    callbackKeyLastDriveCommand = ''

    def __init__(self):
	global telnetconnection
        Tk.__init__(self)
        self.title("iRobot Create 2 Tethered Drive and Stream")
        self.option_add('*tearOff', FALSE)

        self.menubar = Menu()
        self.configure(menu=self.menubar)

        createMenu = Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label="Create", menu=createMenu)
        createMenu.add_command(label="Help", command=self.onHelp)
        createMenu.add_command(label="Quit", command=self.onQuit)

        self.text = Text(self, height = TEXTHEIGHT, width = TEXTWIDTH, wrap = WORD)
        self.scroll = Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)
        self.text.pack(side=LEFT, fill=BOTH, expand=True)
        self.scroll.pack(side=RIGHT, fill=Y)

        self.text.insert(END, helpText)

        self.bind("<Key>", self.callbackKey)
        self.bind("<KeyRelease>", self.callbackKey)


	try:
		print "Trying to connect " + host +":" +port
		telnetconnection = telnetlib.Telnet()
		telnetconnection.open(host, port)
		print "Connected. fileno:"+str(telnetconnection.fileno())
        except:
               print "Failed."
               tkMessageBox.showinfo('Failed', "Sorry, couldn't connect to " + str(port))


    # sendCommandASCII takes a string of whitespace-separated, ASCII-encoded base 10 values to send
    def sendCommandASCII(self, command):
        cmd = ""
        for v in command.split():
            cmd += chr(int(v))

        self.sendCommandRaw(cmd)

    # sendCommandRaw takes a string interpreted as a byte array
    def sendCommandRaw(self, command):
	global telnetconnection

        if telnetconnection is not None:
        	telnetconnection.write(command)
        else:
        	tkMessageBox.showerror('Not connected!', 'Not connected to a robot!')
                print "Not connected."

        print ' '.join([ str(ord(c)) for c in command ])
        self.text.insert(END, ' '.join([ str(ord(c)) for c in command ]))
        self.text.insert(END, '\n')
        self.text.see(END)

    # getDecodedBytes returns a n-byte value decoded using a format string.
    # Whether it blocks is based on how the connection was set up.
    def getDecodedBytes(self, n, fmt):
        global telnetconnection
        try:
            return struct.unpack(fmt, telnetconnection.read(n))[0]
        except struct.error:
            print "Got unexpected data from serial port."
            return None

    # get8Unsigned returns an 8-bit unsigned value.
    def get8Unsigned(self):
        return getDecodedBytes(1, "B")

    # get8Signed returns an 8-bit signed value.
    def get8Signed(self):
        return getDecodedBytes(1, "b")

    # get16Unsigned returns a 16-bit unsigned value.
    def get16Unsigned(self):
        return getDecodedBytes(2, ">H")

    # get16Signed returns a 16-bit signed value.
    def get16Signed(self):
        return getDecodedBytes(2, ">h")

    # A handler for keyboard events. Feel free to add more!
    def callbackKey(self, event):
	global VELOCITYCHANGE
	global ROTATIONCHANGE  
        k = event.keysym.upper()
        motionChange = False
	accerChange = False
      
	if event.type == '2': # KeyPress; need to figure out how to get constant
            if k == 'P':   # Passive
                self.sendCommandASCII('128')
            elif k == 'S': # Safe
                self.sendCommandASCII('131')
            elif k == 'F': # Full
                self.sendCommandASCII('132')
            elif k == 'C': # Clean
                self.sendCommandASCII('135')
            elif k == 'D': # Dock
                self.sendCommandASCII('143')
            elif k == 'SPACE': # Beep
                self.sendCommandASCII('140 3 1 64 16 141 3')
            elif k == 'R': # Reset
                self.sendCommandASCII('7')
            elif k == 'UP':
                self.callbackKeyUp = True
                motionChange = True
            elif k == 'DOWN':
                self.callbackKeyDown = True
                motionChange = True
            elif k == 'LEFT':
                self.callbackKeyLeft = True
                motionChange = True
            elif k == 'RIGHT':
                self.callbackKeyRight = True
                motionChange = True
            elif k == 'SHIFT_L':
		motionChange = True
		accerChange = True
		VELOCITYCHANGE  += ACVECHANGE
		ROTATIONCHANGE += ACROCHANGE

	    elif k == 'CONTROL_L':
		motionChange = True
		accerChange = True
		
		if VELOCITYCHANGE>=0:
		    VELOCITYCHANGE -= ACVECHANGE  
		else: 
		    VELOCITYCHANGE = 0
		    print VELOCITYCHANGE
		if ROTATIONCHANGE>=0:
		    ROTATIONCHANGE -= ACROCHANGE  
		else: 
		    ROTATIONCHANGE = 0
		    print ROTATIONCHANGE

            else:
                print repr(k), "not handled"
        elif event.type == '3': # KeyRelease; need to figure out how to get constant
            if k == 'UP':
                self.callbackKeyUp = False
                motionChange = True
            elif k == 'DOWN':
                self.callbackKeyDown = False
                motionChange = True
            elif k == 'LEFT':
                self.callbackKeyLeft = False
                motionChange = True
            elif k == 'RIGHT':
                self.callbackKeyRight = False
                motionChange = True
            elif k == 'SHIFT_L':
		motionChange = True
		accerChange = False
            elif k == 'CONTROL_L':
		motionChange = True
		accerChange = False

        if motionChange == True:
            velocity = 0
            velocity += VELOCITYCHANGE if self.callbackKeyUp is True else 0
            velocity -= VELOCITYCHANGE if self.callbackKeyDown is True else 0
            rotation = 0
            rotation += ROTATIONCHANGE if self.callbackKeyLeft is True else 0
            rotation -= ROTATIONCHANGE if self.callbackKeyRight is True else 0

            # compute left and right wheel velocities
            vr = velocity + (rotation/2)
            vl = velocity - (rotation/2)

            # create drive command
            cmd = struct.pack(">Bhh", 145, vr, vl)
            if cmd != self.callbackKeyLastDriveCommand:
                self.sendCommandRaw(cmd)
                self.callbackKeyLastDriveCommand = cmd

    def onHelp(self):
        tkMessageBox.showinfo('Help', helpText)

    def onQuit(self):
        if tkMessageBox.askyesno('Really?', 'Are you sure you want to quit?'):
            self.destroy()


if __name__ == "__main__":
    cmd = "cvlc --no-audio v4l2:///dev/video0 --v4l2-width 1920 --v4l2-height 1080 --v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1 --sout '#standard{access=http{mime=multipart/x-mixed-replace;boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8554/}' -I dummy"

    shell = spur.SshShell(host,username,password,missing_host_key=spur.ssh.MissingHostKey.accept)
    shell.spawn(["sh","-c",cmd])
    #os.system(cmd)
    app = TetheredDriveApp()
    app.mainloop()
