from Return import CameraManager, GStreamerPipelines
import os
camMan = CameraManager() #Creates new camera manager object
streamStarted = False
cameras = {"USB":1,"CSI":0}

streamingCamera = "CSI" #Change this for a differnt camera


if os.path.exists(f'/dev/video{cameras[streamingCamera]}'):
    print('true')

    USBCam = camMan.newCam(cameras[streamingCamera]) #Creates new USB-camera
    pipeline = USBCam.addPipeline(GStreamerPipelines.H264,(640,480),30,"CV") #Creates an RGB stream at 30 fps and 640x480 for openCV Change RGB for H264 or MJPEG
    print(pipeline)