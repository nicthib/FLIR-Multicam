# FLIR-Multicam: An efficient multi-cam setup using a hardware trigger/freerun capture and python

This repository seeks to improve on current FLIR documentation for use of their robust and open-source cameras. This code was specifically created to be used on multi-camera setups running at "high" speeds (up to 125 fps has been tested). While many FLIR cameras boast a high free-running FPS, saving captured images can be a challenge. This code improves on their provided approach by offloading a lot of the work via multithreading.

## Intallation Instructions

Download and install BOTH latest Spinnaker SDK and Spinnaker Python (PySpin) for your OS and CPU architecture:
   - https://flir.app.boxcn.net/v/SpinnakerSDK/folder/68522911814

#### Linux System Setup (Ubuntu 16.04 - 22.04)   
  - Download, unzip, and Install PySpin 3.0 with latest, correct versions:
    - For example: https://flir.app.boxcn.net/v/SpinnakerSDK/folder/186861727823
    - `cd ~/Downloads`
    - `tar -xzf spinnaker_python-3.0.0.118-cp38-cp38-linux_x86_64.tar.gz` # <-- Warning: ensure correct versions
    - `cd spinnaker_python-3.0.0.118-cp38-cp38-linux_x86_64`
    - `pip install spinnaker_python-3.0.0.118-cp38-cp38-linux_x86_64.whl`

#### Windows System Setup (Windows 10/11)
- Install Chocolately in an administrative PowerShell:
  - https://chocolatey.org/install#install-step2
- Install Python:
  - `choco install python --version=3.10.8`
- Install Git:
  - `choco install poshgit`
- Update pip:
  - `python -m pip install -U pip`
- Download, unzip, and Install PySpin 3.0 with latest, correct versions:
  - https://flir.app.boxcn.net/v/SpinnakerSDK/folder/73501875299
  - Open a PowerShell window, then:
    - `Expand-Archive $HOME/Downloads/spinnaker_python-3.0.0.118-cp310-cp310-win_amd64.zip -DestinationPath $HOME/Downloads/spinnaker_python-3.0.0.118-cp310-cp310-win_amd64`
    - `cd $HOME/Downloads/spinnaker_python-3.0.0.118-cp310-cp310-win_amd64`
    - `python -m pip install spinnaker_python-3.0.0.118-cp310-cp310-win_amd64.whl`

#### Clone FLIR-Multicam
- `git clone https://github.com/nicthib/FLIR-Multicam.git`
- `cd FLIR-Multicam`
- `python -m pip install -r requirements.txt`

## Usage Instructions

1. Edit ``params.yaml`` with the relevant information needed for your acquisition, but make sure to keep the fieldnames the same to prevent any errors. The default fields configure for a freerun capture for 5 seconds at 30 fps, and an exposure time of 10ms. The ``file_path`` field will write images to the cloned repository location until you update it. If `hardware` is set for the `framerate` field, all detected cameras will be put into a "Trigger Wait" state when `FLIR_Multicam.py` is executed. Otherwise, if a number is set for `framerate`, it will freerun capture at that rate.
2. Run the command ``python FLIR_Multicam.py 1``. The boolean argument at the end indicates if you want to capture images or simply set the camera parameters. Use ``python FLIR_Multicam.py 0`` to just set parameters.

## Important Things to Know
- I wrote this code to be used specifically with the [Blackfly S Mono 1.6 MP USB3 Vision](https://www.flir.com/products/blackfly-s-usb3/?model=BFS-U3-16S2M-CS), but the API is very flexible and should work with most of their USB cameras.
- This code automatically detects how many cameras are connected, and assumes you want to use all of them. If you don't want to, make sure to disconnect the USB cable.
- Make sure to use a hardware trigger compatible with the camera you are using. For the Blackfly S, a 3.3V square wave is sufficient, as long as the duty cycle isn't too short (should be ~50%). I initially accomplished this with a function generator, but whatever signal you would like to use is fine (e.g. an Arduino digital output). (Note that for most Blackfly S cameras, the black wire is the input and the blue wire is ground, although other configurations are shown https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras/).
- This code computes several statistics on frametimes for validation, and immediately plots a timing histogram after recording. In addition, outputted `.txt` file(s) also keep record of frametimes, just in case you need to check for dropped frames, frametime inconsistencies, or are capturing in a non-linear fashion.
- This implementation uses the primary hardware trigger for all cameras, instead of a secondary trigger via the pull-up resistor configuration. This is simpler, since you can simply send the same hardware signal to all cameras, and they will activate simultaneously. This also simplifies the code, as all cameras operate with the same trigger settings.
- It is also possible to configure all camera's connections as secondaries, and trigger off of the green channel, using the brown channel as ground.
- Make sure to monitor your CPU usage while collecting. You'll get significant frametime inconsistencies if it's exceeding 85% or so.
- Don't keep the folder where you are writing images open in file explorer while acquiring. It puts unneccesary load on file explorer and may cause you to drop frames unneccesarily.
- If the camera is dropping frames, increasing the priority of the main python process may help.
  - Linux Only:
    - Set High Priority: `sudo nice -n -20 su -c 'python FLIR_Multicam.py 1' $USER"`
    - Set Realtime Priority: `sudo chrt -f 99 /home/$USER/miniconda3/envs/ratloco/bin/python FLIR_Multicam.py 1`
  - Windows Only:
    - With PowerShell, inside the `FLIR-Multicam` repo folder:
      - ``Start-Process python -ArgumentList "FLIR_Multicam.py 1"; cmd.exe /c "wmic process where name=`"python.exe`" CALL setpriority 128"``
      - Set 32 for Normal, 32768 for Above Normal, 128 for High, 256 for Realtime 

## Conclusions

This code is really useful for science and computer vision applications. Many people use multi-camera setups in my field of behavioral neuroscience research, and these cameras are a powerhouse when it comes to high-throughput imaging in a small form factor.

Thanks for reading!
