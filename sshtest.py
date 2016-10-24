from paramiko import SSHClient

host = "192.168.1.10"
username = "pi"


client = SSHclient()
client.load_system_host_keys()
client.connect(host, username)
cmd = "cvlc --no-audio v4l2:///dev/video0 --v4l2-width 1920 --v4l2-height 1080 --v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1 --sout '#standard{access=http{mime=multipart/x-mixed-replace;boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8554/}' -I dummy &"

stdin,stdout,stderr = client.exec_command(cmd)


