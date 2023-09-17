#!/usr/bin/env python
import multiprocessing
import cv2
from gui import *
from functions import *
from mqtt import *
from obsws import *

#Multiprocessing Queues==============
#By running the GUI in a different process, the window will stay responsive even if the OpenCV processing slow down the code
from_gui = multiprocessing.Queue(10)
to_gui = multiprocessing.Queue(10)
from_mqtt = multiprocessing.Queue(10)
to_mqtt = multiprocessing.Queue(10)
gui_process = multiprocessing.Process(target=gui, args=(window,from_gui,to_gui,), name='gui')
to_gui_list = []
lastscene = ""
mqtt_process = None
#Multiprocessing Queues==============

video = Video(0, None)
yunet_detector =  YunetDetector(model=settings["yunet"]["model"])
obs_ws = OBS_WS()
scenes = Scenes(settings["scenes"])

#OpenCV mouse callback=====================================================================
#This function is triggered when you interact with the video using your mouse
def mouse_callback(event, x, y, flags, params):
    global frame
    match event :
        case cv2.EVENT_LBUTTONDOWN :
            frame = scenes.clic(frame, (x,y))
            cv2.imshow('Frame', frame)
#OpenCV mouse callback=====================================================================

#MAIN =====================================================================================
if __name__ == '__main__' : 
    multiprocessing.freeze_support()
    
    gui_process.start() #Start the GUI process
    
    gui_event, gui_values = "",{} #Events ans state of the GUI
    to_gui_list.append(('scenes-list', list(settings["scenes"]))) #Update the "scene" option menu from the saved scenes

    while True:
        if not from_gui.empty() : #Get events from GUI queue
            gui_event, gui_values = from_gui.get()
        
        if gui_event in (None, 'Exit'): #Exit the script when the GUI window is closed
            break
        
        #Video-------------------------------------------------------------------------------------
        if video.defined : 
            if video.pause is False :
                ret, frame = video.read()
                if ret : #Video is still running    
                    if gui_values['video-fps'] and gui_values['video-show'] : #Display the framerate on the frame
                        video.draw_fps(frame)

                    if gui_values['yunet-enabled'] :  #Yunet detection
                        result = yunet_detector.detect(frame) #Seach fo faces in the frame
                        for head in result : #Iterate over the results
                            for scene in scenes.polygons : #Test for all the saved scenes
                                poly = np.array(scenes.polygons[scene], dtype=np.int32).reshape((-1, 1, 2)) #Convert the scene keypoints in a polygon
                                head_position = cv2.pointPolygonTest(poly, np.array(head, dtype=np.float32), False ) #Chech if the head is inside the scene polygon
                                if head_position == 1 and lastscene != scene: #Send the scene name
                                    print("New scene : ", scene)
                                    to_gui_list.append(('scene-detection', "Last detection : {}".format(scene)))
                                    obs_ws.set_scene(scene)
                                    if mqtt_process and mqtt_process.is_alive() :
                                        to_mqtt.put((settings["mqtt"]["topic_out"], str(scene)) )
                                    lastscene = scene #Prevent spamming the scane name if the face stay in the same scene

                    if gui_values['scene-show'] :
                        frame = scenes.show_polygons(frame)

                    if gui_values['video-show'] : #Create/display and resize the image window
                        cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
                        cv2.resizeWindow('Frame', 1280, 720)
                        cv2.imshow('Frame', frame)
                    
                    #Send the current framerate to the GUI
                    current_fps = "FPS : {0:.1f}".format(video.fps) 
                    to_gui_list.append(('video-curfps', current_fps))
                
                else : #Close the window when the video end
                    video.stop()
                    cv2.destroyAllWindows()
            
            if gui_values['video-show'] : #Handle the window and keyboard inputs
                key = cv2.waitKey(int(gui_values['video-speed']))
        #Video-------------------------------------------------------------------------------------
        
        #Handle GUI events-------------------------------------------------------------------------
        eventsplit = gui_event.split('-') #evensplit contain the "group"[0] and "topic"[1] of the event
        match eventsplit[0] : #Match the groups
            
            case 'video': #Match the topics of the video group
                match eventsplit[1] :
                    case 'pause' : #Play/pause the video
                        if video.defined :
                            video.pause = not video.pause
                            video.pauseframe = frame.copy()
                    
                    case 'startwebcam' : #Start the video capture from a webcam
                        webcam_index = gui_values['video-camport'] 
                        print("Starting webcam : {}".format(webcam_index))
                        video = Video(webcam_index, None)

                        video.set_resolution(tuple(map(int, gui_values['video-resolution'].split('x')))) #Set the video resolution (720p by default)
                        ret, frame = video.read() #Read the first frame

                        #Create and resize a window and add the mouse callback (only if Show video is ticked) 
                        if gui_values['video-show']:
                            cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
                            cv2.resizeWindow('Frame', 1280, 720)
                            cv2.setMouseCallback('Frame', mouse_callback)

                        video.defined = True
                    
                    case 'show': #Show/hide the OpenCV window
                        if gui_values['video-show']: #Create/Display the window
                            cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
                            cv2.resizeWindow('Frame', 1280, 720)
                            cv2.setMouseCallback('Frame', mouse_callback)
                        else :
                            cv2.destroyAllWindows()

            case 'yunet' : #Match the topics of the face detection group
                match eventsplit[1] :
                    case 'gpu' : #Switch between CPU/GPU processing
                        yunet_detector.gpu = gui_values['yunet-gpu']
        
            case "obsws" : #Match the topics of the OBS WS group
                match eventsplit[1]:
                    case "connect": #Connect to OBS
                        settings["obs_ws"] = {
                            "server" : gui_values["obsws-server"],
                            "port" : gui_values["obsws-port"],
                            "password" : gui_values["obsws-password"],
                        }
                        save_json(settings)
                        to_gui_list.append(('obsws-status', obs_ws.connect(settings["obs_ws"])))

                    case "disconnect": #Disconnect
                        to_gui_list.append(('obsws-status', obs_ws.disconnect())) 

            case "mqtt" : #Match the topics of the MQTT group
                match eventsplit[1] :
                    case "connect" : #Connect to the MQTT broker
                        settings["mqtt"] = {
                            "broker": gui_values["mqtt-broker"],
                            "port" : int(gui_values["mqtt-port"]),
                            "username" : gui_values["mqtt-username"],
                            "password" : gui_values["mqtt-password"],
                            "topic_in": gui_values["mqtt-topicin"],
                            "topic_out": gui_values["mqtt-topicout"],
                        }
                        save_json(settings)
                        mqtt_process = multiprocessing.Process(target=mqtt_handler, args=(settings["mqtt"],from_mqtt,to_mqtt))
                        mqtt_process.start()

                    case "disconnect" : #Disconnect
                        if mqtt_process and mqtt_process.is_alive() :
                            mqtt_process.kill()

            case "polygons" : #Match the topics of the polygon (scene) group
                if video.defined :
                    ret, frame = video.read() #Get a new frame
                    if ret : 
                        video.pauseframe = frame.copy() #Save the frame (to reset anotations)
                        match eventsplit[1] :
                            case "reset" : #Save the current selection
                                scenes.reset()
                                frame = video.pauseframe
                        
                            case "save" : #Save the current selection  
                                scenes.save(gui_values['polygons-name'] )
                                scenes.reset()
                                settings["scenes"] = scenes.polygons
                                to_gui_list.append(('scenes-list', list(settings["scenes"])))
                                save_json(settings)
                                frame = scenes.show_polygons(video.pauseframe)
                            
                            case "show" : #Show all the selections
                                video.pauseframe = frame.copy()
                                frame = scenes.show_polygons(video.pauseframe)
                                
                            case "delete" : #Delete the selected scene
                                if gui_values["scenes-list"] in settings["scenes"]:
                                    del settings["scenes"][gui_values["scenes-list"]]
                                    to_gui_list.append(('scenes-list', list(settings["scenes"])))
                                    save_json(settings)
                                    frame = scenes.show_polygons(video.pauseframe)

                        cv2.imshow('Frame', frame)
        #Handle GUI events-------------------------------------------------------------------------
               
        if len(to_gui_list)>0 and not to_gui.full() : #Update the GUI   
            to_gui.put(to_gui_list)
        
        #Clear the GUI envent and updates
        to_gui_list = []
        gui_event = 'none'
    #GUI-----------------------------------------------------------------------------------

    #EXIT------------------
    video.stop()
    gui_process.terminate()
    obs_ws.disconnect()
    cv2.destroyAllWindows()
    #EXIT------------------
#MAIN =====================================================================================





