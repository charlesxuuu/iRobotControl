# iRobotControl
----------------
The original tethered driving code works well for directly operate on Raspberry Pi + iRobot Create. However, I still found a little bit inconvenience since I cannot remotely ssh to my Raspberry Pi and then use the python code to drive. This is because the GTinker implementation and the ssh environment cannot directly offload the keyboard event. So I made a few changes on the original code.

----------------
## Enhanced Features: 
 
1. Implemented the speed up (Shift-L) and speed down(Crtl-L) function. 
    (P.S. a Need for Speed fan.)
  
2. For the Raspberry Pi, you can open a socket and connected it with the serial port with ser2net service.
    You can get it by running:
    ```Bash
    $sudo apt-get install ser2net 
    ```
    Then configure the IP address and port number by adding :
    ```Bash
    $sudo vim /etc/ser2net.conf
    ```
    add the following line in ser2net.conf:
    ```Bash
    19910:telnet:14400:/dev/ttyUSB0:115200 8DATABITS NONE 1STOPBIT LOCAL banner
    ```
    This maps the /dev/ttyUSB0 to the socket with port number 19910 
    then restart the ser2net service
    ```Bash
    $sudo service ser2net restart
    ```
    
3. USB camera for streaming:

   Install vlc by
   ```Bash
   $ sudo apt-get install vlc
   ```
   It needs to install video4linux2. 

   Initiate vlc streaming from USB camera: 
   ```Bash
   $cvlc --no-audio v4l2:///dev/video0 \ 
   $--v4l2-width 1920 --v4l2-height 1080 \ 
   $--v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1 \ 
   $--sout '#standard{access=http{mime=multipart/x-mixed-replace; \ 
   $boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8554/}' \  
   $-I dummy 
   ```
   then you can access the video stream by http://localhost:8554/

## TODO: 
   A fully automatic setup script
 
## Tested Environments
   1. iRobot Create 2 
   2. Linux raspberrypi 4.4.11-v7+ 
   
####         Charles Xu (xuchi.int@gmail.com)
