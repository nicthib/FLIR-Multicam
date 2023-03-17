import os
import re
import time
import threading
import sys
import PySpin
import yaml
import ruamel.yaml
from pathlib import Path
from numpy import mean, std, diff, round, argmax, histogram, arange, append
import termplotlib as tpl

# Version for general use
def read_config(configname):
    """
    Reads structured config file
    """
    ruamelFile = ruamel.yaml.YAML()
    path = Path(configname)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                cfg = ruamelFile.load(f)
        except Exception as err:
            if err.args[2] == "could not determine a constructor for the tag '!!python/tuple'":
                with open(path, 'r') as ymlfile:
                    cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
                    # write_config(configname, cfg)
    else:
        raise FileNotFoundError(
            "Config file is not found. Please make sure that the file exists and/or there are no unnecessary spaces in the path of the config file!")
    return (cfg)

# Change cwd to script folder
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Read cfg yaml file
cfg = read_config('params.yaml')
num_images = cfg['num_images']
exp_time = cfg['exp_time']
trigger_line = cfg['trigger_line']
bin_val = int(1)  # bin mode (WIP)
if cfg['file_path'] == 0:
    dir_list = os.listdir(dname)
    timestamp = time.localtime()
    timestamp = str(timestamp[0])+str(timestamp[1]).zfill(2)+str(timestamp[2]).zfill(2) # get year, month, day
    new_base_folder_name = 'images'+timestamp
    largest_recording_number = -1
    
    for folder in dir_list:
        if new_base_folder_name in folder:
            if int(folder.split('-')[-1]) > largest_recording_number:
                largest_recording_number = int(folder.split('-')[-1])
    im_savepath = os.path.join(dname, new_base_folder_name+"-"+str(largest_recording_number+1)) # increment from largest value
else:
    im_savepath = cfg['file_path']
orig_filename = cfg['file_name']
filename = re.sub('_',f'-{largest_recording_number+1}_',orig_filename,count=1)
framerate = cfg['framerate']

# Create webcam and aux save folder
if not os.path.exists(im_savepath):
    os.makedirs(im_savepath)
os.chdir(im_savepath)

# Thread process for saving images. This is super important, as the writing process takes time inline,
# so offloading it to separate CPU threads allows continuation of image capture
class ThreadWrite(threading.Thread):
    def __init__(self, data, out):
        threading.Thread.__init__(self)
        self.data = data
        self.out = out

    def run(self):
        # These commands are legacy, and not needed (kept for documentation)
        # image_result = self.data
        # image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
        self.data.Save(self.out)


# Capturing is also threaded, to increase performance
class ThreadCapture(threading.Thread):
    def __init__(self, cam, camnum, nodemap):
        threading.Thread.__init__(self)
        self.cam = cam
        self.camnum = camnum

    def run(self):
        times = []
        t1 = []
        if framerate != 'hardware':
            nodemap = self.cam.GetNodeMap()

        if self.camnum == 0:
            primary = 1
        else:
            primary = 0

        for i in range(num_images):
            fstart = time.perf_counter_ns()
            try:
                #  Retrieve next received image
                if framerate == 'hardware':
                    image_result = self.cam.GetNextImage()
                else:
                    node_softwaretrigger_cmd = PySpin.CCommandPtr(nodemap.GetNode('TriggerSoftware'))
                    if not PySpin.IsAvailable(node_softwaretrigger_cmd) or not PySpin.IsWritable(
                            node_softwaretrigger_cmd):
                        print('Unable to execute trigger. Aborting...')
                        return False
                    node_softwaretrigger_cmd.Execute()
                    image_result = self.cam.GetNextImage()

                times.append(time.perf_counter_ns())
                if i == 0 and primary == 1:
                    t1 = time.perf_counter_ns()
                    print('*** ACQUISITION STARTED ***\n')

                if i == int(num_images - 1) and primary == 1:
                    t2 = time.perf_counter_ns()
                if primary:
                    # using .zfill to add leading zeros to frame idx, for better compatibility with ffmpeg commands
                    print('COLLECTING IMAGE ' + str(i + 1).zfill(len(str(num_images))) + ' of ' + str(num_images), end='\r') 
                    sys.stdout.flush()
                    
                # using .zfill to add leading zeros to frame idx, for better compatibility with ffmpeg commands
                fullfilename = filename + '_' + str(i + 1).zfill(len(str(num_images))) + '_cam' + str(self.camnum) + '.jpg'
                background = ThreadWrite(image_result, fullfilename)
                background.start()
                image_result.Release()
                ftime = time.perf_counter_ns() - fstart
                if framerate != 'hardware':
                    if ftime < 1 / framerate:
                        time.sleep(1 / framerate - ftime)

            except PySpin.SpinnakerException as ex:
                print('Error (577): %s' % ex)
                return False

        self.cam.EndAcquisition()
        if primary:
            frame_diff_times = diff(times)*1e-6 #append(diff(times)*1e-6,15)
            interframe_mean = mean(frame_diff_times) # ms
            round_interframe_mean = int(round(interframe_mean))
            interframe_devs = frame_diff_times-round_interframe_mean # ms
            largest_interframe_dev = max(interframe_devs, key=abs)
            number_of_dropped_frames = sum(interframe_devs>=round_interframe_mean-1)
            interframe_std = std(frame_diff_times) # ms
            # interframe_max = max(frame_diff_times) # ms
            # interframe_min = min(frame_diff_times) # ms
            print("Number of frames captured: ",num_images)
            print(f'Software-computed frame rate: {str(round(num_images/((t2 - t1)*1e-9),decimals=4))}')
            print(f"Software-computed interframe statistics: {interframe_mean.round(decimals=4)} +/- {interframe_std.round(decimals=4)} ms")
            print(f"Largest interframe deviation: {largest_interframe_dev.round(decimals=4)} ms")
            print(f"Largest deviation found for frame #: {argmax(abs(interframe_devs))}")
            print(f"Number of deviations more than 0.1ms: {sum(interframe_devs>0.1)}")
            print(f"Number of deviations more than 0.5ms: {sum(interframe_devs>0.5)}")
            print(f"Number of deviations more than 1ms: {sum(interframe_devs>1)}")
            print(f"Number of deviations more than {round_interframe_mean-1}ms (likely dropped frames): {number_of_dropped_frames}")
            counts, bin_edges = histogram(frame_diff_times)#bins=arange(interframe_min-0.2,interframe_max+0.2,0.2)) # keep bin size flexible
            fig = tpl.figure()
            fig.hist(counts, bin_edges,force_ascii=False, orientation="horizontal")
            fig.show()
            if number_of_dropped_frames > 0:
                # color red with \033 stop and color codes
                print(f'\033[1;31m Weird recording! {number_of_dropped_frames} dropped frame(s) detected. D: \033[0;0m' )
            else:
                print('\033[1;32m Good recording! No dropped frames detected. :D \033[0;0m')
        # Save frametime data
        with open(filename + '_t' + str(self.camnum) + '.txt', 'a') as t:
            for item in times:
                t.write(str(item) + ',\n')

def configure_cam(cam, camnum):
    result = True
    if camnum == 0:
        print('*** CONFIGURING CAMERA(S) ***\n')
    try:
        nodemap = cam.GetNodeMap()
        # Ensure trigger mode off
        # The trigger must be disabled in order to configure whether the source
        # is software or hardware.
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
            print('Unable to disable trigger mode 129 (node retrieval). Aborting...')
            return False

        node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
            print('Unable to disable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())

        node_trigger_source = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSource'))
        if not PySpin.IsAvailable(node_trigger_source) or not PySpin.IsWritable(node_trigger_source):
            print('Unable to get trigger source 163 (node retrieval). Aborting...')
            return False

        # Set primary camera trigger source to cfg['trigger_line'] (hardware trigger)
        if framerate == 'hardware':
            node_trigger_source_set = node_trigger_source.GetEntryByName(trigger_line)
            if camnum == 0:
                print('Trigger source set to hardware...\n')
        else:
            node_trigger_source_set = node_trigger_source.GetEntryByName('Software')
            if camnum == 0:
                print('Trigger source set to software, framerate = %i...\n' % framerate)

        if not PySpin.IsAvailable(node_trigger_source_set) or not PySpin.IsReadable(
                node_trigger_source_set):
            print('Unable to set trigger source (enum entry retrieval). Aborting...')
            return False

        node_trigger_source.SetIntValue(node_trigger_source_set.GetValue())
        node_trigger_mode_on = node_trigger_mode.GetEntryByName('On')

        if not PySpin.IsAvailable(node_trigger_mode_on) or not PySpin.IsReadable(node_trigger_mode_on):
            print('Unable to enable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_on.GetValue())

        # Set acquisition mode to continuous
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
            return False

        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                node_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
            return False

        # Retrieve integer value from entry node
        acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        # Retrieve Stream Parameters device nodemap
        s_node_map = cam.GetTLStreamNodeMap()

        # Retrieve Buffer Handling Mode Information
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsAvailable(handling_mode) or not PySpin.IsWritable(handling_mode):
            print('Unable to set Buffer Handling mode (node retrieval). Aborting...\n')
            return False

        handling_mode_entry = PySpin.CEnumEntryPtr(handling_mode.GetCurrentEntry())
        if not PySpin.IsAvailable(handling_mode_entry) or not PySpin.IsReadable(handling_mode_entry):
            print('Unable to set Buffer Handling mode (Entry retrieval). Aborting...\n')
            return False

        # Set stream buffer Count Mode to manual
        stream_buffer_count_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferCountMode'))
        if not PySpin.IsAvailable(stream_buffer_count_mode) or not PySpin.IsWritable(stream_buffer_count_mode):
            print('Unable to set Buffer Count Mode (node retrieval). Aborting...\n')
            return False

        stream_buffer_count_mode_manual = PySpin.CEnumEntryPtr(stream_buffer_count_mode.GetEntryByName('Manual'))
        if not PySpin.IsAvailable(stream_buffer_count_mode_manual) or not PySpin.IsReadable(
                stream_buffer_count_mode_manual):
            print('Unable to set Buffer Count Mode entry (Entry retrieval). Aborting...\n')
            return False

        stream_buffer_count_mode.SetIntValue(stream_buffer_count_mode_manual.GetValue())

        # Retrieve and modify Stream Buffer Count
        buffer_count = PySpin.CIntegerPtr(s_node_map.GetNode('StreamBufferCountManual'))
        if not PySpin.IsAvailable(buffer_count) or not PySpin.IsWritable(buffer_count):
            print('Unable to set Buffer Count (Integer node retrieval). Aborting...\n')
            return False

        # Set new buffer value to the max
        max_buffer_count = buffer_count.GetMax()
        if camnum==0:
            print(f"Setting buffer count to: {max_buffer_count}")
        buffer_count.SetValue(max_buffer_count)

        # max_packet_size = cam.DiscoverMaxPacketSize()
        # from pdb import set_trace; set_trace()
        # Retrieve and modify resolution (WIP)
        # node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
        # if PySpin.IsAvailable(node_width) and PySpin.IsWritable(node_width):
        #     width_to_set = int(1440 / bin_val)
        #     node_width.SetValue(width_to_set)
        #     if camnum == 0:
        #         print('Width set to %i...' % node_width.GetValue())
        # else:
        #     if camnum == 0:
        #         print('Width not available, width is %i...' % node_width.GetValue())
        #
        # node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
        # if PySpin.IsAvailable(node_height) and PySpin.IsWritable(node_height):
        #     height_to_set = int(1080 / bin_val)
        #     node_height.SetValue(height_to_set)
        #     if camnum == 0:
        #         print('Height set to %i...' % node_height.GetValue())
        # else:
        #     if camnum == 0:
        #         print('Width not available, height is %i...' % node_height.GetValue())

        # Access trigger overlap info
        node_trigger_overlap = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerOverlap'))
        if not PySpin.IsAvailable(node_trigger_overlap) or not PySpin.IsWritable(node_trigger_overlap):
            print('Unable to set trigger overlap to "Read Out". Aborting...')
            return False

        # Retrieve enumeration for trigger overlap Read Out
        if framerate == 'hardware':
            node_trigger_overlap_ro = node_trigger_overlap.GetEntryByName('ReadOut')
        else:
            node_trigger_overlap_ro = node_trigger_overlap.GetEntryByName('Off')

        if not PySpin.IsAvailable(node_trigger_overlap_ro) or not PySpin.IsReadable(
                node_trigger_overlap_ro):
            print('Unable to set trigger overlap (entry retrieval). Aborting...')
            return False

        # Retrieve integer value from enumeration
        trigger_overlap_ro = node_trigger_overlap_ro.GetValue()

        # Set trigger overlap using retrieved integer from enumeration
        node_trigger_overlap.SetIntValue(trigger_overlap_ro)

        # Access exposure auto info
        node_exposure_auto = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
        if not PySpin.IsAvailable(node_exposure_auto) or not PySpin.IsWritable(node_exposure_auto):
            print('Unable to get exposure auto. Aborting...')
            return False

        # Retrieve enumeration for trigger overlap Read Out
        node_exposure_auto_off = node_exposure_auto.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_exposure_auto_off) or not PySpin.IsReadable(
                node_exposure_auto_off):
            print('Unable to get exposure auto "Off" (entry retrieval). Aborting...')
            return False

        # Set exposure auto to off
        node_exposure_auto.SetIntValue(node_exposure_auto_off.GetValue())

        # Access exposure info
        node_exposure_time = PySpin.CFloatPtr(nodemap.GetNode('ExposureTime'))
        if not PySpin.IsAvailable(node_exposure_time) or not PySpin.IsWritable(node_exposure_time):
            print('Unable to get exposure time. Aborting...')
            return False

        # Set exposure float value
        node_exposure_time.SetValue(exp_time * 1000000)
        if camnum == 0:
            print('Exposure time set to ' + str(exp_time * 1000) + 'ms...')

    # General exception
    except PySpin.SpinnakerException as ex:
        print('Error (237): %s' % ex)
        return False

    return result


def config_and_acquire(camlist):
    thread = []
    for i, cam in enumerate(camlist):
        cam.Init()
        configure_cam(cam, i)
        nodemap = cam.GetNodeMap()
        cam.BeginAcquisition()
        thread.append(ThreadCapture(cam, i, nodemap))
        thread[i].start()

    if framerate == 'hardware':
        print('*** WAITING FOR FIRST TRIGGER... ***\n')

    for t in thread:
        t.join()

    for i, cam in enumerate(camlist):
        reset_trigger(cam)
        cam.DeInit()


# Config camera params, but don't begin acquisition
def config_and_return(camlist):
    for i, cam in enumerate(camlist):
        cam.Init()
        configure_cam(cam, i)

    for i, cam in enumerate(camlist):
        reset_trigger(cam)
        cam.DeInit()

# Trigger reset
def reset_trigger(cam):
    nodemap = cam.GetNodeMap()
    try:
        result = True
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
            print('Unable to disable trigger mode 630 (node retrieval). Aborting...')
            return False

        node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
            print('Unable to disable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())

    except PySpin.SpinnakerException as ex:
        print('Error (663): %s' % ex)
        result = False

    return result

# Main writing loop
def main():
    # Check write permissions
    try:
        test_file = open('test.txt', 'w+')
    except IOError:
        print('Unable to write to current directory. Please check permissions.')
        return False

    test_file.close()
    os.remove(test_file.name)
    result = True
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()

    print('Number of cameras detected: %d' % num_cameras)

    # Multicamera handling
    if num_cameras == 0:
        cam_list.Clear()
        system.ReleaseInstance()
        print('Not enough cameras! Goodbye.')
        return False
    elif num_cameras > 0 and int(sys.argv[1]) == 1:
        config_and_acquire(cam_list)
    else:
        config_and_return(cam_list)

    # Clear cameras and release system instance
    cam_list.Clear()
    system.ReleaseInstance()

    print('DONE')
    time.sleep(.5)
    print('Goodbye :)')
    time.sleep(.5)
    return result

if __name__ == '__main__':
    main()
