#!/usr/bin/env python

import cv2
import time 
import numpy as np

class Video:
	def __init__(self,port, api):
		#Video init
		self.video = cv2.VideoCapture(port,api)
		self.port = port
		self.defined = False
		self.pauseframe = None

		#Get and save the video informations
		self.theo_fps = self.video.get(cv2.CAP_PROP_FPS)
		self.resolution = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
		self.totframe = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
		self.framenum = 0
		self.pause = False

		#FPS counter
		self.now = 0
		self.last = 0
		self.fps = 0
		self.fps_mean_imgcounter = 0
		self.fps_txtpos = (5,25)
		self.fps_txtcolor = (0,0,0)
		self.fps_txtsize = 0.75
		self.fps_txtthick = 2

	#Read the next frame
	def read(self):
		ret, frame = self.video.read()
		self.framenum += 1
		self.calc_fps()
		return ret, frame

	#Set the reading at a specific frame
	def set_frame(self, frame):
		self.video.set(cv2.CAP_PROP_POS_FRAMES, frame)

	#Stop the video and release the camera
	def stop(self):
		self.defined = False
		self.video.release()

	#Set video resolution (for webcam)
	def set_resolution(self, resolution):
		self.video.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
		self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

	#Calc the current framerate
	def calc_fps(self):
		self.now = time.time()
		delta = self.now - self.last
		if delta > 0 :
			self.fps = 1/delta
			self.last = self.now
		return self.fps

	#Draw the current framerate on the frame
	def draw_fps(self,frame):
		cv2.putText(frame, "{:.1f} FPS".format(self.fps), self.fps_txtpos, cv2.FONT_HERSHEY_DUPLEX, self.fps_txtsize, self.fps_txtcolor , self.fps_txtthick, cv2.LINE_AA)
		return frame
			
class YunetDetector :
	landmark_color = [
        (255,   0,   0), # right eye
        (  0,   0, 255), # left eye
        (  0, 255,   0), # nose tip
        (255,   0, 255), # right mouth corner
        (  0, 255, 255)  # left mouth corner
    	]
	gpu = False
			
	def __init__(self,model):
		self.detector = cv2.FaceDetectorYN.create(
			model=model,
			config="",
			input_size=[320,320],
			score_threshold=0.9,
			nms_threshold=0.5,
			top_k=5
    		)

	def detect(self, frame):
		h, w, _ = frame.shape
		self.detector.setInputSize([w, h])
		nosepos = []

		if self.gpu :
			gpu_frame = cv2.UMat(frame)
			result,faces= self.detector.detect(gpu_frame)
			faces = faces.get()
		else :
			result,faces= self.detector.detect(frame)
		
		for det in (faces if faces is not None else []):
			bbox = det[0:4].astype(np.int32)
			cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 255, 0), 2)

			conf = det[-1]
			cv2.putText(frame, '{:.4f}'.format(conf), (bbox[0], bbox[1]+12), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 255))

			landmarks = det[4:14].astype(np.int32).reshape((5,2))
			for id, landmark in enumerate(landmarks):
				cv2.circle(frame, landmark, 2, self.landmark_color[id], 2)
			
			nosepos.append(tuple(landmarks[2]))

		return nosepos

class Scenes : 
	clicnr = 0 
	clics = []
	lastclic = (0,0)

	def __init__(self, polygons):
		self.polygons = polygons

	def clic(self, frame, pos):
		clic = tuple(pos)
		
		if self.clicnr > 0 :
			cv2.line(frame, self.lastclic,clic, (0,0,255), 3,cv2.LINE_AA)
			self.lastclic = pos
		else :
			self.lastclic = pos

		self.clics.append(clic)
		self.clicnr +=1
		
		return frame

	def save(self, name):
		if len(self.clics)> 0 :
			self.polygons[name] = self.clics

	def reset(self):
		self.clicnr = 0 
		self.clics = []

	def show_polygons(self, frame):
		tempframe = frame.copy()
		if self.polygons :
			for polygon in self.polygons :
				poly = np.array(self.polygons[polygon], dtype=np.int32).reshape((-1, 1, 2))
				cv2.polylines(tempframe, [poly], True, (0,0,255), 3, cv2.LINE_AA)
				M = cv2.moments(poly)
				cX = int(M["m10"] / M["m00"])
				cY = int(M["m01"] / M["m00"])
				cv2.putText(tempframe, str(polygon), (cX,cY), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255))
		
		return tempframe