#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 23  Oct 2016

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
import ttk
import tkSimpleDialog
import spur
import struct
from threading import Thread
import time
import telnetlib  # for telnet

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

connection = None
instruction_num = 0

TEXTWIDTH = 40  # window width, in characters
TEXTHEIGHT = 16  # window height, in lines

VELOCITYCHANGE = 100
ACVECHANGE = 50
ROTATIONCHANGE = 100
ACROCHANGE = 50


introText = """\
iRobot Create 2 Control Panel

*************************************
1. Set up the connection
2. Set up motion and parameters
3. Begin to Drive or switch to manual drving mode
*************************************
\n
"""



helpText = """\
Supported keys for manual driving:
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

If nothing happens after you connect, try pressing 'P' and then 'S' to get into safe mode.\n
"""


class TetheredDriveApp(Tk):
    # static variables for keyboard callback -- I know, this is icky
    callbackKeyUp = False
    callbackKeyDown = False
    callbackKeyLeft = False
    callbackKeyRight = False
    callbackKeyLastDriveCommand = ''

    global connection
    global host
    global port
    global username
    global password
    global streamport

    def __init__(self):


        Tk.__init__(self)
        self.title("iRobot Create 2 Control Panel")
        self.option_add('*tearOff', FALSE)

        self.menubar = Menu()
        self.configure(menu=self.menubar)

        create_Menu = Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label="Menu", menu=create_Menu)
        create_Menu.add_command(label="Help", command=self.onHelp)
        create_Menu.add_command(label="Quit", command=self.onQuit)

        # Create Control frame
        self.control_frame = Frame(self)
        self.control_frame.grid(row=0)

        self.connection_text = Label(self.control_frame, text="Connection", font=("", 10))
        self.connection_text.pack(side=TOP)
        # Create arameter_frame inside control frame
        self.param_frame = Frame(self.control_frame)

        self.param_frame.pack(side=TOP)


        self.host_text = Label(self.param_frame, text="Host")
        self.host_text.grid(row=1)
        self.host_input = Entry(self.param_frame, bd=5)
        self.host_input.grid(row=1, column=1)
        self.host_input.insert(END, host)

        self.port_text = Label(self.param_frame, text="Port")
        self.port_text.grid(row=2)
        self.port_input = Entry(self.param_frame, bd=5)
        self.port_input.grid(row=2, column=1)
        self.port_input.insert(END, port)

        self.username_text = Label(self.param_frame, text="Username")
        self.username_text.grid(row=3)
        self.username_input = Entry(self.param_frame, bd=5)
        self.username_input.grid(row=3, column=1)
        self.username_input.insert(END, username)

        self.pwd_text = Label(self.param_frame, text="Password")
        self.pwd_text.grid(row=4)
        self.pwd_input = Entry(self.param_frame, show="*", bd=5)
        self.pwd_input.grid(row=4, column=1)
        self.pwd_input.insert(END, password)

        self.stream_text = Label(self.param_frame, text="Stream port")
        self.stream_text.grid(row=5)
        self.stream_input = Entry(self.param_frame, bd=5)
        self.stream_input.grid(row=5, column=1)
        self.stream_input.insert(END, streamport)

        self.connect_button = Button(self.control_frame, text="Connect", command=lambda:self.connectRobot())
        self.connect_button.pack(side=LEFT, padx=5, pady=2)
        self.disconnect_button = Button(self.control_frame, text="Disconnect", command=lambda:self.disconnectRobot())
        self.disconnect_button.pack(side=LEFT, padx=5, pady=2)
        self.stream_button = Button(self.control_frame, text="Stream", command=lambda:self.startStream())
        self.stream_button.pack(side=LEFT, padx=5, pady=2)

        # Create Drive Frame
        self.plandrive_frame = Frame(self)
        self.plandrive_frame.grid(row=1)
        self.connection_text = Label(self.plandrive_frame, text="Drive", font=("", 10))
        self.connection_text.pack(side=TOP)

        # Create param2_frame inside control frame
        self.param2_frame = Frame(self.plandrive_frame)
        self.param2_frame.pack(side=TOP)

        self.motion_text = Label(self.param2_frame, text="Motion", pady=5)
        self.motion_text.grid(row=1)
        self.motion_value = StringVar()
        self.motion_box = ttk.Combobox(self.param2_frame, textvariable=self.motion_value)
        self.motion_box['values'] = ('Cycle', 'Straight', 'Turn', 'Planned path')
        self.motion_box.current(0)
        self.motion_box.grid(row=1, column=1)
        self.motion_box.bind("<<ComboboxSelected>>", self.newMotionSelection)


        self.speed_text = Label(self.param2_frame, text="Speed (mm/s)")
        self.speed_text.grid(row=2)
        self.speed_input = Entry(self.param2_frame, bd=5)
        self.speed_input.grid(row=2, column=1)

        self.rotation_text = Label(self.param2_frame, text=" Radius (mm)")
        self.rotation_text.grid(row=3)
        self.rotation_input = Entry(self.param2_frame, bd=5)
        self.rotation_input.grid(row=3, column=1)

        self.time_text = Label(self.param2_frame, text="  Time (s) ")
        self.time_text.grid(row=4)
        self.time_input = Entry(self.param2_frame, bd=5)
        self.time_input.grid(row=4, column=1)


        self.drive_button = Button(self.plandrive_frame, text="Drive", command=lambda:self.drive(self.motion_box.get(), self.speed_input.get(), self.rotation_input.get(), self.time_input.get()))
        self.drive_button.pack(side=LEFT, padx=5, pady=2)

        self.manual_button = Button(self.plandrive_frame, text="Manual", command=lambda:self.initialManualDrive())
        self.manual_button.pack(side=LEFT, padx=5, pady=2)
        self.stopmanual_button = Button(self.plandrive_frame, text="Stop Manual", command=lambda:self.stopManualDrive())
        self.stopmanual_button.pack(side=LEFT, padx=5, pady=2)


        self.log_frame = Frame(self)
        self.log_frame.grid(column=1,row=0,rowspan=2)

        self.logtext = Label(self.log_frame, text="Log", font=("", 10))
        self.logtext.pack(side=TOP)


        self.log = Text(self.log_frame, height=TEXTHEIGHT, width=TEXTWIDTH, wrap=WORD)
        self.scroll = Scrollbar(self.log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=self.scroll.set)
        self.log.pack(side=LEFT, fill=BOTH, expand=True)
        self.scroll.pack(side=RIGHT, fill=Y)
        self.log.insert(END, introText)
        self.log.see(END)

        #self.bind("<Key>", self.callbackKey)
        #self.bind("<KeyRelease>", self.callbackKey)

        #self.connectRobot()

    def connectRobot(self):
        global instruction_num
        global connection

        self.log.insert(END, "[" + str(instruction_num) + "] Trying to connect " + host + ":" + port + "\n")
        self.log.see(END)
        instruction_num += 1
        connection = telnetlib.Telnet()

        try:
            connection.open(host, port)

        except:
            self.log.insert(END, "Failed.")
            self.log.see(END)
            tkMessageBox.showinfo('Failed', "Sorry, couldn't connect to " + str(port))

        # into safe mode
        self.log.insert(END, "Connected. \n\n")
        self.log.see(END)
        self.sendCommandASCII('131')
        # beep
        self.sendCommandASCII('140 3 1 64 16 141 3')

    def disconnectRobot(self):
        global connection
        global instruction_num
        if connection is None:
            tkMessageBox.showerror('Not connected!', 'Not connected to a robot!')
            self.log.insert(END, "[" + str(instruction_num) + "] Not connected.\n\n")
            self.log.see(END)
            instruction_num += 1
            return

        connection.close()
        connection = None
        self.log.insert(END, "[" + str(instruction_num) + "] Close connection." + "\n\n")
        self.log.see(END)
        instruction_num += 1


    def startStream(self):

        global connection
        global instruction_num

        if connection is None:
            tkMessageBox.showerror('Not connected!', 'Not connected to a robot!')
            self.log.insert(END, "[" + str(instruction_num) + "] Not connected.\n\n")
            self.log.see(END)
            instruction_num += 1
            return

        thread = Thread(target=self.stream_thread, args=())
        thread.daemon = True
        thread.start()

        self.log.insert(END, "[" + str(instruction_num) + "] Start Streaming. \n  http://" + str(host) + ":" + str(streamport) + "\n\n")
        self.log.see(END)
        instruction_num += 1

    def stream_thread(self):
        cmd = """cvlc --no-audio v4l2:///dev/video0\
             --v4l2-width 1920 --v4l2-height 1080
             --v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1
             --sout '#standard{access=http{mime=multipart/x-mixed-replace;
             boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8554/}'
             -I dummy"""

        shell = spur.SshShell(host, username, password, missing_host_key=spur.ssh.MissingHostKey.accept)
        shell.spawn(["sh", "-c", cmd])





    def initialManualDrive(self):

        global connection
        global instruction_num

        if connection is None:
            tkMessageBox.showerror('Not connected!', 'Not connected to a robot!')
            self.log.insert(END, "[" + str(instruction_num) + "] Not connected.\n\n")
            self.log.see(END)
            instruction_num += 1
            return


        self.bind("<Key>", self.callbackKey)
        self.bind("<KeyRelease>", self.callbackKey)
        self.log.insert(END, "[" + str(instruction_num) + "] Start Manual Driving.\n\n")
        self.log.insert(END, helpText)
        self.log.see(END)
        instruction_num += 1



    def stopManualDrive(self):
        global connection
        global instruction_num

        if connection is None:
            tkMessageBox.showerror('Not connected!', 'Not connected to a robot!')
            self.log.insert(END, "[" + str(instruction_num) + "] Not connected.\n\n")
            self.log.see(END)
            instruction_num += 1
            return

        self.unbind("<Key>")
        self.unbind("<KeyRelease>")
        self.log.insert(END, "[" + str(instruction_num) + "] Stop Manual Driving\n\n")
        self.log.see(END)
        instruction_num += 1


    # sendCommandASCII takes a string of whitespace-separated, ASCII-encoded base 10 values to send
    def sendCommandASCII(self, command):
        cmd = ""
        for v in command.split():
            cmd += chr(int(v))

        self.sendCommandRaw(cmd)

    # sendCommandRaw takes a string interpreted as a byte array
    def sendCommandRaw(self, command):

        global connection
        global instruction_num

        if connection is None:
            tkMessageBox.showerror('Not connected!', 'Not connected to a robot!')
            self.log.insert(END, "[" + str(instruction_num) + "] Not connected.\n\n")
            self.log.see(END)
            instruction_num += 1
            return

        connection.write(command)
        #print ' '.join([str(ord(c)) for c in command])

        self.log.insert(END, "[" + str(instruction_num) + "]" + ' '.join([str(ord(c)) for c in command]))
        self.log.insert(END, '\n\n')
        self.log.see(END)
        instruction_num += 1
        # getDecodedBytes returns a n-byte value decoded using a format string.
        # Whether it blocks is based on how the connection was set up.

    def getDecodedBytes(self, n, fmt):
        global connection
        try:
            return struct.unpack(fmt, connection.read(n))[0]
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

        if event.type == '2':  # KeyPress; need to figure out how to get constant
            if k == 'P':  # Passive
                self.sendCommandASCII('128')
            elif k == 'S':  # Safe
                self.sendCommandASCII('131')
            elif k == 'F':  # Full
                self.sendCommandASCII('132')
            elif k == 'C':  # Clean
                self.sendCommandASCII('135')
            elif k == 'D':  # Dock
                self.sendCommandASCII('143')
            elif k == 'SPACE':  # Beep
                self.sendCommandASCII('140 3 1 64 16 141 3')
            elif k == 'R':  # Reset
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
                VELOCITYCHANGE += ACVECHANGE
                ROTATIONCHANGE += ACROCHANGE

            elif k == 'CONTROL_L':
                motionChange = True
                accerChange = True

                if VELOCITYCHANGE >= 0:
                    VELOCITYCHANGE -= ACVECHANGE
                else:
                    VELOCITYCHANGE = 0
                    print VELOCITYCHANGE

                if ROTATIONCHANGE >= 0:
                    ROTATIONCHANGE -= ACROCHANGE
                else:
                    ROTATIONCHANGE = 0
                    print ROTATIONCHANGE
            #else:
                #print repr(k), "not handled"

        elif event.type == '3':  # KeyRelease; need to figure out how to get constant
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
            vr = velocity + (rotation / 2)
            vl = velocity - (rotation / 2)

            # create drive command
            cmd = struct.pack(">Bhh", 145, vr, vl)
            if cmd != self.callbackKeyLastDriveCommand:
                self.sendCommandRaw(cmd)
                self.callbackKeyLastDriveCommand = cmd

    def drive(self, motion, param1, param2, param3):
        global connection
        global instruction_num

        if connection is None:
            tkMessageBox.showerror('Not connected!', 'Not connected to a robot!')
            self.log.insert(END, "[" + str(instruction_num) + "] Not connected.\n\n")
            self.log.see(END)
            instruction_num += 1
            return






        if motion == "Cycle":
            if self.isValidSpeed(param1) and self.isValidRadius(param2) and self.isValidTime(param3) is True:
                self.driveCycle(int(param1), int(param2), int(param3))


        elif motion == "Straight" :
            if self.isValidSpeed(param1) and self.isValidTime(param3) is True :
                self.driveStraight(int(param1), int(param3))

        elif motion == "Turn" :
            if self.isValidSpeed(param1) and self.isValidDirection(param2) and self.isValidTime(param3) is True :
                self.driveTurn(int(param1), int(param2), int(param3))

        elif motion == "Planned path":
            if self.isValidFilepath(param1) is True :
                #TODO:
                return

    def isValidSpeed(self, param):
        try:
            speed = int(param)
        except ValueError:
            tkMessageBox.showerror('Invalid parameter', 'Not valid speed parameter!')
            return

        if -500<= int(speed) <=500 :
            return True
        else :
            tkMessageBox.showerror('Speed limitation', 'Backward [-500mm/s, 500mm/s] Forward')
            return False

    def isValidRadius(self, param):
        try:
            radius = int(param)
        except ValueError:
            tkMessageBox.showerror('Invalid parameter', 'Not valid radius parameter!')
            return

        if -2000<= radius <=2000 :
            return True
        else :
            tkMessageBox.showerror('Radius limitation', 'Right [-2000mm, 2000mm] Left')
            return False

    def isValidDirection(self, param):
        try:
            direction = int(param)
        except ValueError:
            tkMessageBox.showerror('Invalid parameter', 'Direction is either 1 (clockwise) or -1 (counterclockwise)')
            return

        if direction==-1 or direction==1 :
            return True
        else :
            tkMessageBox.showerror('Direction', 'Direction is either 1 (clockwise) or -1 (counterclockwise)')
            return False



    def isValidTime(self, param):
        try:
            runtime = int(param)
        except ValueError:
            tkMessageBox.showerror('Invalid parameter', 'Not valid time parameter!')
            return
        if runtime >= 0 :
            return True
        else :
            tkMessageBox.showerror('Time limitation', '[0s, ...)')
            return False

    def isValidFilepath(self, filepath):
        #TODO:
        return True




    def driveCycle(self, velocity, radius, runtime):
        cmd = struct.pack(">Bhh", 137, velocity, radius)
        self.sendCommandRaw(cmd)
        self.log.insert(END, "Cycle. Speed:" + str(velocity) + "mm/s\tRadius:" + \
                        str(radius) + "mm\tTime:" + \
                        str(runtime) + "s\n\n" )
        time.sleep(runtime)
        cmd = struct.pack(">Bhh", 137, 0, 0)
        self.sendCommandRaw(cmd)



    def driveStraight(self, velocity, runtime):
        cmd = struct.pack(">Bhh", 137, velocity, 0)
        self.sendCommandRaw(cmd)
        self.log.insert(END, "Straight. Speed:" + str(velocity) + "mm/s\tTime:" + \
                        str(runtime) + "s\n\n")
        time.sleep(runtime)
        cmd = struct.pack(">Bhh", 137, 0, 0)
        self.sendCommandRaw(cmd)

    def driveTurn(self, velocity, direction, runtime):
        strdirection = None
        if direction == 1:
            cmd = struct.pack(">Bhh", 137, velocity, int('01', 16))
            strdirection = "Counter Clockwise"
        elif direction == -1:
            cmd = struct.pack(">Bhh", 137, velocity, -1) # -1 complement: 0xFFFF
            strdirection = "Clockwise"
        self.sendCommandRaw(cmd)
        self.log.insert(END, "Turn. Speed:" + str(velocity) + "mm/s\tDirection:" + strdirection + "\tTime:" + \
                        str(runtime) + "s\n\n")
        time.sleep(runtime)
        cmd = struct.pack(">Bhh", 137, 0, 0)
        self.sendCommandRaw(cmd)

    def newMotionSelection(self, event):
        motion = self.motion_box.get()
        if motion == "Cycle":
            self.speed_text['text']="Speed (mm/s)"
            self.rotation_text['text']=" Radius (mm)"
            self.time_text['text']="  Time (s) "

        elif motion == "Straight" :
            self.speed_text['text']="Speed (mm/s)"
            self.rotation_text['text']="    Null    "
            self.time_text['text']="  Time (s) "

        elif motion =="Turn" :
            self.speed_text['text']="Speed (mm/s)"
            self.rotation_text['text']=" Direction  "
            self.time_text['text']="  Time (s) "

        elif motion =="Planned path":
            self.speed_text['text']="     File path    "
            self.rotation_text['text'] = "    Null    "
            self.time_text['text'] = "    Null    "

    def onHelp(self):
        tkMessageBox.showinfo('Help', helpText)


    def onQuit(self):
        if tkMessageBox.askyesno('Really?', 'Are you sure you want to quit?'):
            self.destroy()


if __name__ == "__main__":
    # os.system(cmd)
    app = TetheredDriveApp()
    app.mainloop()
