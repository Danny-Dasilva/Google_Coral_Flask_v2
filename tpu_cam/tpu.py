import os.path
from TPUCameraManager.TPUCameraManager import CameraManager
camMan = CameraManager() #Creates new camera manager object
streamStarted = False
cameras = {"USB":1,"CSI":0}

streamingCamera = "CSI" #Change this for a differnt camera

def start_stream(cam):
        
    if os.path.exists('/dev/video{0}'.format(cameras[cam])):
        try:
            USBCam = camMan.newCam(cameras[cam]) #Creates new USB-camera
            CV = USBCam.addPipeline('H264',(640,480),30,"CV") #Creates an RGB stream at 30 fps and 640x480 for openCV Change RGB for H264 or MJPEG
            USBCam.startPipeline()
            
        except:
            pass
        while True:
            if CV:
                yield bytes(CV) #RGB Byte Stream that can be converted to a numpy arra

            elif not os.path.exists('/dev/video{0}'.format(cameras[cam])):
                print("Closing Camera")
                camMan.close(USBCam)
                

            

t = start_stream(streamingCamera)
for byte in t:
    print(len(byte))

def start_recording(self, obj, format, profile, inline_headers, bitrate, intra_period):
        def on_buffer(data, _):
            for byte in t:
                print(len(byte))
                #obj.write(byte)
            

       
