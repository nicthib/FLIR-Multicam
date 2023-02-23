# FLIR Multicam: An efficient multi-cam setup using a hardware trigger/freerun capture and python

This repository seeks to improve on current FLIR documentation for use of their robust and open-source cameras. This code was specifically created to be used on multi-camera setups running at "high" speeds (60 fps or so). While many FLIR cameras boast a high free-running FPS, saving captured images can be a challenge. This code improves on their provided approach by offloading a lot of the work via multithreading.

## How to use

1. Clone this repository
2. Edit ``params.yaml`` with the relevant information needed for your acquisition. The default fields configure for a freerun capture for 5 seconds at 30 fps, and an exposure time of 10ms. The ``file_path`` field will write images to the cloned repository location until you update it.
3. Run the command ``FLIR_Multicam.py 1``. The boolean argument at the end indicates if you want to capture images or simply set the camera parameters. Use ``FLIR_Multicam.py 0`` to just set parameters.

## Important things to know

- Make sure to have PySpin installed - you can find the Python packages [here](https://www.ptgrey.com/support/downloads). Currently, the official release is supported on Python 3.6, which I used for this implementation. 
- I wrote this code to be used specifically with the [Blackfly S Mono 1.6 MP USB3 Vision](https://www.flir.com/products/blackfly-s-usb3/?model=BFS-U3-16S2M-CS), but the API is very flexible and should work with most of their USB cameras.
- This code automatically detects how many cameras are connected, and assumes you want to use all of them. If you don't want to, make sure to disconnect the USB cable.
- Make sure to use a hardware trigger compatible with the camera you are using. For the Blackfly S, a 3.3V square wave is sufficient, as long as the duty cycle isn't too short. I initially accomplished this with a function generator, but whatever signal you would like to use is fine. (Note that for most Blackfly S cameras, the black wire is the input and the blue wire is ground).
- The params.yaml file can be edited, but make sure to keep the fieldnames the same to prevent any errors. The "framerate" field can be set to "hardware" for extrenal hardware triggering, or a number for freerun mode.
- The outputted .txt file(s) also keeps record of frametimes, just in case you want to check for any dropped frames, frametime inconsistencies, or are capturing in a non-linear fashion.
- This implementation uses the primary hardware trigger for all cameras, instead of a secondary trigger via the pull-up resistor configuration. This is simpler, since you can simply send the same hardware signal to all cameras, and they will activate simultaneously. This also simplifies the code, as all cameras operate with the same trigger settings.
- Make sure to monitor your CPU usage while collecting. You'll get significant frametime inconsistencies if it's exceeding 85% or so.
- Don't keep the folder where you are writing images open in file explorer while acquiring. It puts unneccesary load on file explorer and may cause you to drop frames unneccesarily.

## Conclusions

This code is really useful for science and computer vision applications. Many people use multi-camera setups in my field of behavioral neuroscience research, and these cameras are a powerhouse when it comes to high-throughput imaging in a small form factor.

Thanks for reading!
