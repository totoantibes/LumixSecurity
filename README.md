#Lumix Security
Turn your wifi enabled Lumix Camera into a security camera. This small script is an improvement(?) of a script shared in http://www.personal-view.com/talks/discussion/6703/control-your-gh3-from-a-web-browser-now-with-video-/p1 by http://www.personal-view.com/talks/profile/36673/cloudnein
Indeed 
* Some exception handling especially around the connection to the camera.
* Filter for the Panasonic UPNP server on the network (i initially was connecting to any UPNP service)
* added a thread that tells the camera that it is indeed connected to a live app every 10 sec.
* option to record a video (in camera) of x seconds after the detection of movement.
* handle in the GH4.py for various file formats (RW2 or JPG) given a new XML format that was released with GH5s camera.
* this is very much a "use at your own risks".
* a lot of paths in the pythons are hardcoded to my machine so please adapt them to your local
* play with the variable at the start of the monitor.py file to change behaviors.

known issues:
* threads may run wild even after the keyboard interrupt?
* recconnecting to the camera is sometimes flaky
* downloading of jpg from the camrera is not working completely well.
