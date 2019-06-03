# FLIR cameras and Python: An efficient multi-cam setup using a hardware trigger

This repository seeks to improve on current FLIR documentation for use of their robust and open-source cameras. This code was specifically created to be used on multi-camera setups running at "high" speeds (60 fps or so). While many FLIR cameras boast a high free-running FPS, saving captured images can be a challenge. This code improves on their provided approach by offloading a lot of the work via multithreading.

## How to use

1. Clone this repository and run the command ``FLIR_Multicam.py 1``. The boolean argument at the end indicates if you want to capture images or simply set the camera parameters. Use ``FLIR_Multicam.py 0`` to just set parameters.
2. Update ``params.txt`` with the relevant information needed for your acquisition (explained in more detail in the next section).
3. ``FLIR_Multicam.py`` needs the ``params.txt`` fileto work properly, so make sure to either run this command within the repository folder, or update the path to ``params.txt`` in FLIR_multicam.py (Line 12).

## Important things to know

- Make sure to have PySpin installed - you can find the Python packages [here](https://www.ptgrey.com/support/downloads). Currently, the official release is supported on Python 3.6, which I used for this implementation. 
- I wrote this code to be used specifically with the [Blackfly S Mono 1.6 MP USB3 Vision](https://www.ptgrey.com/blackfly-s-mono-16-mp-usb3-vision-sony-imx273), but the API is very flexible and should work with most of their USB cameras.
- This code automatically detects how many cameras are connected, and assumes you want to use all of them. If you don't want to, make sure to disconnect the USB cable.
- Make sure to use a hardware trigger compatible with the camera you are using. For the Blackfly S, a 3.3V square wave is sufficient, as long as the duty cycle isn't too short. I initially accomplished this with a function generator, but whatever signal you would like to use is fine.
- The params.txt file dictates (in this order)
1) How many images to be captured (per camera)
2) The exposure time of the camera in seconds
3) The length of the run (unused for now, but useful for auxillary purposes such as DAQ boards and other external measurements)
4) The folder for image storage
5) The image filename(s)
- The outputted .txt file also keeps record of frametimes, just in case you want to check for any dropped frames, frametime inconsistencies, or are capturing in a non-linear fashion.
- This implementation uses the primary hardware trigger for all cameras, instead of a secondary trigger via the pull-up resistor configuration. This is unneccesary, since you can simply send the same hardware signal to all cameras, and they will activate simultaneously. This also simplifies the code, as all cameras operate with the same trigger settings.
- Make sure to monitor your CPU usage while collecting. You'll get significant frametime inconsistencies if it's exceeding 85% or so.
- Don't keep the folder where you are writing images open in file explorer while acquiring. It puts unneccesary load on the CPU and may cause you to drop frames unneccesarily.

## Conclusions

This code is really useful for science and computer vision applications. Many people use multi-camera setups in my field of behavioral neuroscience research, and these cameras are a powerhouse when it comes to high-throughput imaging in a small form factor.

Thanks for reading!
