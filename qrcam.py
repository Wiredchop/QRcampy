import cv2
import numpy as np
from enum import Enum
from threading import Thread,Lock, Event

class Cameramodes(Enum):
    '''This Enum is used to choose and set the mode of the camera. 
    They have been chosen to reflect the size of the touchscreen'''
    W800H480 = (800,480)
    W800H400 = (800,400)
    W800H320 = (800,320)
    W640H480 = (640,480)
    W640H400 = (640,400)
    W640H320 = (640,320)
    def __init__(self,width,height):
        self.width = width
        self.height = height

class cam_params:
    '''A parameters class for the QRcam class, contains options for the operation of the class
    
        mode:   Specify operating resolution of camera (default = 640 x 400)
        annotate:   Specify whether to annotate the camera image when a QR code found (default = True)
        stop_after_detect:  Specify whether to stop camera after QR code successfully detect (default = True)'''
    mode: Cameramodes
    annotate: bool
    stop_after_detect: bool
    def __init__(self,mode = Cameramodes.W640H400,annotate = True, stop_after_detect = False ):
        self.mode = mode
        self.annotate = annotate
        self.stop_after_detect = stop_after_detect
class QRcam:
    '''Main Class to view camera output and get information from detected QR codes'''
    
    parameters: cam_params
    cap: cv2.VideoCapture
    frame: np.ndarray
    detector: cv2.QRCodeDetector
    _lock: Lock
    _ID: str
    _ID_detected: Event
    
    def __init__(self,parameters: cam_params): 
        cam_mode = parameters.mode
        self.parameters = parameters       
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_mode.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_mode.height)
        #Create an empty image frame in case camera is not started before frame is used
        self.frame = np.zeros([cam_mode.width,cam_mode.height,3],dtype=np.uint8)
        
        # QR code detection object
        self.detector = cv2.QRCodeDetector()
        
        #Objects for threading
        self.cam_thread = Thread(target=self.camera_thread,args=())
        self._lock = Lock()
        self._ID_detected = Event()
        self._ID = ''
        
    def start_camera(self):
        '''This starts a separate thread that captures frames from the camera
        It also runs through the QR code detector, adding annotation if set in parameters'''
        self.cam_thread.daemon = True
        self.cont = True
        self.cam_thread.start()
    def stop_camera(self):
        self.cont = False
        self.cap.release()
    def reset_detection(self):
        '''Will reset the event detecting QR codes
        Use in case when incorrect ID is found. Won't stop the camera thread
        
        This method CLEARS the ID value so make sure you have a copy first'''
        self._ID_detected.clear()
        self._ID = ''
        
    def camera_thread(self):
        if not self.is_running:
            raise Exception("Camera is not running")
        while self.cont:
            #Lock so getting image is protected
            # get the image
            status, frame = self.cap.read()
            if status:               
                data, bbox, _ = self.detector.detectAndDecode(self.frame)
                if(bbox is not None and self.parameters.annotate):
                    for i in range(len(bbox)):
                        cv2.line(frame, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), color=(255,
                                0, 255), thickness=2)
                        cv2.putText(frame, data, (int(bbox[0][0][0]), int(bbox[0][0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 255, 0), 2)
                if(data != ''):
                    self._ID_detected.set()
                    self._ID = data
                    if(self.parameters.stop_after_detect):
                        self.stop_camera()
                    
                with self._lock:
                    self.frame = frame
                
                
                
    def get_image(self) -> np.ndarray:
        with self._lock:
            #Copying the frame so access errors aren't created-
            #Not sure about handling potential memory leaks in Python?
            #frame_copy = self.frame.copy()
            return self.frame 
            
    @property
    def is_running(self) -> bool:
        '''Check whether camera is running, boolean output'''
        return self.cap.isOpened()
    
    @property
    def id_found(self) -> bool:
        '''Returns True when data found from QR code'''
        return self._ID_detected.is_set()

    @property
    def ID(self) -> str:
        '''The ID data found in the QR code'''
        return self._ID