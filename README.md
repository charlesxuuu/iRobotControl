# iRobotControl


The original tethered driving code works well for raspberry pi + irobot create. A few enhanced features: <br>
 
   1. Implemented the speed up (Shift-L) and speed down(Crtl-L) function. <br>
   (P.S. a Need for Speed fan.) <br>
  
   2. For the Raspberry Pi, you can open a socket and connected it with the serial port with ser2net service.<br>
   You can get it by running:<br>
   $sudo apt-get install ser2net <br>
   Then configure the IP address and port number by adding :<br>
   $sudo vim /etc/ser2net.conf<br>
   add the following line in ser2net.conf:<br>
   19910:telnet:14400:/dev/ttyUSB0:115200 8DATABITS NONE 1STOPBIT LOCAL banner<br>
   This maps the /dev/ttyUSB0 to the socket with port number 19910 <br>
   then restart the ser2net service<br>
   $sudo service ser2net restart<br>
    
   3. USB camera for streaming:<br>
   Install vlc by<br>
   $ sudo apt-get install vlc<br>
   it needs to install video4linux2 <br>
   Initiate vlc streaming from USB camera: <br>
   $cvlc --no-audio v4l2:///dev/video0 \ <br>
   $--v4l2-width 1920 --v4l2-height 1080 \ <br>
   $--v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1 \ <br>
   $--sout '#standard{access=http{mime=multipart/x-mixed-replace; \ <br>
   $boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8554/}' \  <br>
   $-I dummy  <br>

   TODO: <br><br><br>
   
 
    Tested envionments: <br>
    1. iRobot Create 2 <br>
    2. Linux raspberrypi 4.4.11-v7+ <br>
   
    --Charles Xu (xuchi.int@gmail.com)

###########################################################################
