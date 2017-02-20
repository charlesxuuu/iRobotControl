import spur
from threading import Thread

host = "192.168.1.10"
username = "pi"
password = "raspberry"


shell = spur.SshShell(host,username,password)

cmd = "cvlc --no-audio v4l2:///dev/video0 --v4l2-width 1920 --v4l2-height 1080 --v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1 --sout '#standard{access=http{mime=multipart/x-mixed-replace;boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8554/}' -I dummy"
shell.spawn(["sh","-c",cmd])

print "ok"
	
