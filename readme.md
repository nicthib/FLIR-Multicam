# FLIR cameras and Python: An efficient multi-cam setup using a hardware trigger

This repository seeks to improve on current FLIR documentation for use of their robust and open-source cameras. This code was specifically created to be used on multi-camera setups running at "high" speeds (60 fps or so). While many FLIR cameras boast a high free-running FPS, saving captured images can be a challenge. This code improves on their provided approach by offloading a lot of the work via multithreading.

## Important things to know

- Make sure to have PySpin installed - you can find the Python packages [here](https://www.ptgrey.com/support/downloads). Currently, the official release is supported on Python 3.6, which I used for this implementation. 
- I wrote this code to be used specifically with the [Blackfly S Mono 1.6 MP USB3 Vision](https://www.ptgrey.com/blackfly-s-mono-16-mp-usb3-vision-sony-imx273), but the API is very flexible and should work with most of their USB cameras.
- Make sure to use a hardware trigger compatible with the camera you are using. For the Blackfly S, a 3.3V square wave is sufficient, as long as the duty cycle isn't too short. I initially accomplished this with a function generator, but whatever signal you would like to use is fine.
- The params.txt file dictates (in this order)
1) How many images will be saved
2) The exposure time of the camera in seconds (which can limit the framerate)
3) The length of the run (unused for now, btu useful for auxillary purposes)
4) The folder for image storage
5) The prefix of the filename
- The outputted .txt file also keeps record of frametimes, just in case you want to check for any dropped frames, frametime inconsistencies, or are capturing in a non-linear fashion.

## Conclusions

This code is really useful for science and computer vision applications. Many people use multi-camera setups in my field of behavioral research, and these cameras are a powerhouse when it comes to high-throughput imaging in a small form factor.

Thanks for reading!