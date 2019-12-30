from . import gstreamer
import threading
import enum
import numpy as np

class CameraManager:
    def __init__(self):
        self.camClasses = []
    
    def newCam(self,device):
        newCamClass = Cam(device)
        self.camClasses.append(newCamClass)
        return newCamClass
    
    def closeAll(self):
        for camClass in self.camClasses:
            camClass.stopPipeline()
            camClass.removeAllPipelines()
            self.camClasses.remove(camClass)
    
    def close(self,camClass):
        camClass.stopPipeline()
        camClass.removeAllPipelines()
        self.camClasses.remove(camClass)
    
    def __len__():
        return len(camClasses)

class Cam:
    def __init__(self,device):
        self.started = False
        self.pipeline = str(GStreamerPipelines.SRC).format(device)
        self.signals = {}
        self.streams = {}
    
    def on_buffer(self, data, streamName):
        self.streams[streamName].newData(data)
        
    def getImage(self):
        if self.streamType is GStreamerPipelines.RGB:
            self.newdata = False
            nparr = np.frombuffer(self.data, dtype=np.uint8)
            image = nparr.reshape(self.res[1], self.res[0], 3)
            return(image)
        else:
            print("Can't return image of H264 stream")
            return(None)
    
    def addPipeline(self,pipeline,res,fps,sinkName):

        pipeline = getattr(GStreamerPipelines, pipeline)
        self.pipeline += " " + str(pipeline).format(res[0],res[1],fps,sinkName)
        
        self.signals[sinkName] = {'new-sample': gstreamer.new_sample_callback(self.on_buffer,sinkName),'eos' : gstreamer.on_sink_eos}
        self.streams[sinkName] = StreamValue()
        return(self.streams[sinkName])
    
    def removePipeline(self,sinkName):
        del self.streams[sinkName]
        del self.signals[sinkName]
    
    def removeAllPipelines(self):
        self.streams.clear()
        self.signals.clear()
        
    def startPipeline(self):
        self.thread = threading.Thread(target=gstreamer.run_pipeline,args=(self.pipeline,self.on_buffer,self.signals))
        self.thread.start()
        self.started = True
    
    def stopPipeline(self):
        gstreamer.quit()
        self.thread.join()

    def __bytes__(self):
        self.newdata = False
        return self.data
    def __bool__(self):
        return self.newdata


class StreamValue():
    def __init__(self):
        self.data = None
        self.updatedData = False
        self.listeners = []
    
    def __bytes__(self):
        self.updatedData = False
        return self.data
    
    def __bool__(self):
        return self.updatedData
    
    def newData(self,data):
        self.data = data
        for listener in self.listeners:
           listener.write(self.data)
        self.updatedData = True

    def addListener(self,obj):
       self.listeners.append(obj)

class GStreamerPipelines(enum.Enum):
    SRC = "v4l2src device=/dev/video{0} ! tee name=t"
    H264 = "t. ! queue max-size-buffers=1 leaky=downstream ! video/x-raw,format=YUY2,width={0},height={1},framerate={2}/1 ! videoconvert ! x264enc speed-preset=ultrafast tune=zerolatency threads=4 key-int-max=5 bitrate=1000 aud=False bframes=1 ! video/x-h264,profile=baseline ! h264parse ! video/x-h264,stream-format=byte-stream,alignment=nal ! appsink name={3} emit-signals=True max-buffers=1 drop=False sync=False"
    RGB = "t. ! queue ! glfilterbin filter=glbox ! video/x-raw,format=RGB,width={0},height={1},framerate={2}/1 ! appsink name={3} emit-signals=True max-buffers=1 drop=True sync=False"
    MJPEG = "t. ! queue ! video/x-raw,format=YUY2,width={0},height={1},framerate={2}/1 ! jpegenc quality=20 ! appsink name={3} emit-signals=True"

    def __str__(self):
        return self.value