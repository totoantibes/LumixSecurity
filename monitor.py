#!/usr/bin/env python

import gh4, urllib.request, urllib.parse, urllib.error, time, socket, threading, io, sys, urllib.parse, ssdp
from PIL import Image, ImageOps, ImageStat, ImageChops

errimg = Image.open(open('D:\lumixsecurity\err.jpg','rb'))

my_ip = '192.168.1.37'
my_stream_port = 12345

# do you want to save the images that are streamed and trigger the capture?
save_preview = True

# record video
record_video = True

#how many seconds should the video be recorded 
video_time = 2

# take a picture when the threshold is exceeded? (choose either video or capture)
do_capture = False

# download pictures when it's quiet?
do_get = True

# If we've been capturing for "longest_capture_time" or we did some captures
# but haven't since "window_after_last_capture", we pause and download what
# we have taken so far so they can go to the cloud.
longest_capture_time = 60.0
window_after_last_capture = 60.0

# after receiving "avgwindow" images from the stream, I average the deltas
# and compare against for the threshold
avgwindow = 8

# if the diff is higher than the last average * "motion_threshold", I take
# pictures
motion_threshold = 1.75




found_pana = False

while [ 1 ]:
    serv = ssdp.discover('urn:schemas-upnp-org:device:MediaServer:1')
    if serv :
        print('found service discover')
        for target in serv:
            print(target.server)
            if (target.server.find("Panasonic-UPnP")!=-1):
                (cam_ip, cam_port) = urllib.parse.urlparse(target.location).netloc.split(':')
                found_pana = True
                print ('found pana')
                break
    if found_pana:  break
cam_port = int(cam_port)
print('found camera, IP: %s' % cam_ip)

stream_flag = True
stream_thread = None
stream_lock = threading.Lock()
stream_socket = None

def stream_callback():
    global stream_flag
    print('stream thread starting')
    while 1:
        if not stream_flag: break
    try:
        u = urllib.request.urlopen('http://%s/cam.cgi?mode=startstream&value=%d' % (cam_ip, my_stream_port))
        u.close()
        u = None
    except Exception as e:
      print('stream: %s' % e)
      time.sleep(2)
      print('stream thread terminating')

def stop_stream():
    global stream_socket, stream_thread, stream_flag, stream_lock

    if stream_flag == False or not stream_thread: return


    print('stopping stream')
    stream_lock.acquire()
    stream_flag = False
    stream_thread.join()
    stream_thread = None
    stream_socket.close()
    stream_socket = None
    print('stream stopped')
    stream_lock.release()

imgtime = time.time()

def start_stream():
    global stream_lock, stream_thread, stream_flag, stream_socket
    print('starting stream')
    stream_lock.acquire()
    if stream_thread:
        print('stream thread already running')
        return
    while True:
        try :
            urllib.request.urlretrieve('http://%s/cam.cgi?mode=setsetting&type=liveviewsize&value=vga' % cam_ip, 'D:\\lumixsecurity\\buffer')
            urllib.request.urlretrieve('http://%s/cam.cgi?mode=camcmd&value=recmode' % cam_ip, 'D:\\lumixsecurity\\buffer2')
        except:
            time.sleep(0.5)
        else:
            break
    time.sleep(0.5)
    stream_flag = True
    stream_thread = threading.Thread(target=stream_callback)
    stream_thread.daemon = True
    stream_thread.start()
    print('stream started')
    stream_lock.release()

    stream_socket = connect()
    imgtime = time.time()

def restart_stream():
    stop_stream()
    start_stream()

def polling():
    count_iterations = 0
    while True: 
        time.sleep(10) # Sleep for 10 sec  
        count_iterations +=1
        try :
            urllib.request.urlretrieve('http://%s/cam.cgi?mode=getstate' % cam_ip, 'D:\\lumixsecurity\\buffer') #
        except:
            print(' error in polling thread %d ' % count_iterations)
    return True

polling_thread = threading.Thread(target=polling)
polling_thread.daemon = True
try:
    polling_thread.start()
except (KeyboardInterrupt, SystemExit):
    sys.exit()
    
##def deadman():
##    global imgtime, stream_flag
##    while 1:
##        if stream_flag and time.time() > imgtime + 20.0:
##            print('deadman killing stream')
##            restart_stream()
##        else:
##            time.sleep(1)

##deadman_thread = threading.Thread(target=deadman)
##deadman_thread.daemon = True
##try:
##    deadman_thread.start()
##except (KeyboardInterrupt, SystemExit):
##    cleanup_stop_thread()
##    sys.exit()
alarm_state = 'disarmed'
last_capture = 0
first_capture = None
last_download = 0

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((my_ip, my_stream_port))
    s.settimeout(10)
    return s

start_stream()

previewcount = 0
skipcount = 0
previmg = None
prevavg = 100.0
avg = 0.0
avgcount = 0
while 1:
    t = time.time()
    try:
        data = stream_socket.recv(1024 * 512 * 1) # 0.5MB
        data = data[data.find(b'\xff\xd8'):]
    except socket.timeout:
        restart_stream()
        continue
    if not data:
        restart_stream()
        continue
    if data[-2:] != b'\xff\xd9':
        print('no end of jpeg found from stream')
        continue
    img = Image.open(io.BytesIO(data))
    grayimg = ImageOps.grayscale(img)
    if not previmg:
        previmg = grayimg
        continue
    d = ImageStat.Stat(ImageChops.difference(previmg, grayimg))
    m = d.mean[0]
    if m < 0.1: continue # often get repeating frames, ignore
    d = ImageStat.Stat(ImageChops.difference(errimg, img))
    if d.mean[0] < 0.1:
        print('errimg')
        restart_stream()
        imgtime = time.time()
        continue
    imgtime = time.time()
    avg = avg + m
    avgcount = avgcount + 1
    if avgcount >= avgwindow:
        prevavg = avg / avgcount
        avg = 0
        avgcount = 0
    if skipcount > 0:
        skipcount -= 1
        continue
    print('pre average is %f' % prevavg)
    if m > prevavg * motion_threshold:
        print('mean = %f' % (m / prevavg))
        if save_preview: img.save('%d-%s.jpg' % (previewcount, time.strftime('%Y%m%d-%H%M%S')), 'jpeg')
        previewcount += 1 
        if do_capture:
            try :
                urllib.request.urlretrieve('http://%s/cam.cgi?mode=camcmd&value=capture' % cam_ip, 'D:\\lumixsecurity\\buffer3')
                last_capture = t
            except Exception as e:
                time.sleep(2)
            if not first_capture: first_capture = t
            elif do_get:
                if (first_capture and t > first_capture + longest_capture_time) or (t > last_capture + window_after_last_capture and last_capture > last_download):
                    print('getting pics')
                    stop_stream()
                    gh4.get_new_pics(cam_ip)
                    previmg = None
                    skipcount=5
                    start_stream()
                    last_download = t
                    first_capture = None
        elif record_video :
            #stop_stream()
            while 1: 
                try:
                    urllib.request.urlretrieve('http://%s/cam.cgi?mode=camcmd&value=video_recstart' % cam_ip,'D:\\lumixsecurity\\buffer3')
                except:
                    time.sleep(0.5)
                else:
                    break
            time.sleep(video_time)
            while 1: 
                try:
                    urllib.request.urlretrieve('http://%s/cam.cgi?mode=camcmd&value=video_recstop' % cam_ip,'D:\\lumixsecurity\\buffer3')
                except:
                    time.sleep(0.5)
                else:
                    break
            skipcount=7
            #start_stream()
    previmg = grayimg
