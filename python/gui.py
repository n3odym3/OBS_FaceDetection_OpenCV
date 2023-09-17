#!/usr/bin/env python

import PySimpleGUI as sg
from json_settings import *

sg.theme('DarkGrey9')

#Right clic menu
right_click_menu_def = [[], []]

#GUI process=========================================
def gui(window, from_gui, to_gui):
    event, values = '',''
    while True :  
        #Send events to the GUI queue----------------
        event, values = window.read(timeout=10)
        if not from_gui.full() and event != "__TIMEOUT__":
            from_gui.put((event,values))
        #Send events to the GUI queue----------------

        #Get events from the GUI queue---------------
        if not to_gui.empty() :
            updates  = to_gui.get_nowait()
            for update in updates :
                if update[0] == 'scenes-list' :
                    if len(update[1]) > 0 :
                        window[update[0]].update(values = update[1])
                        window[update[0]].update(update[1][-1])
                else :
                    window[update[0]].update(update[1])
        #Get events from the GUI queue---------------
#GUI process=========================================

#Top layout=========================================================
top_layout = [
    [   
        sg.Button('Pause', key='video-pause'),
        sg.Text('Speed', font=('Helvetica', 10)),
        sg.Slider(key='video-speed',size=(10,10),font=('Helvetica', 8),range=(500,1),default_value=20, orientation='h',enable_events = True),
        sg.Text(key='video-curfps', text='FPS : na')
    ],     
    [   
        sg.Checkbox('Show video', key='video-show', default=True, enable_events = True),
        sg.Checkbox('show FPS',key='video-fps', default=True,enable_events = True)
    ]
    ]
#Top layout=========================================================

#Video Tab ==========================================================
video_layout = [
    [sg.Text('Webcam',font=('Helvetica', 10, 'bold', 'underline'))],
    [
        sg.Text('Cam port'), sg.Spin([i for i in range(-1,11)], initial_value=9, k='video-camport'), 
        sg.OptionMenu(values=('1920x1080', '1280x720', '640x480'), default_value = '1280x720' , k='video-resolution'),
        sg.Button('Start webcam', key='video-startwebcam')
    ],
    [sg.Text('Face detection using Yunet', font=('Helvetica', 10, 'bold', 'underline'))],
    [   
        sg.Checkbox('Enable',key='yunet-enabled', default=False,enable_events = True),
        sg.Checkbox('OpenCL',key='yunet-gpu', default=False,enable_events = True),
        sg.Checkbox('Show scenes',key='scene-show', default=False,enable_events = True),
    ],
    [
        sg.Text('Last detection : None', key="scene-detection"),
    ]

]
#Video Tab ==========================================================

#Websocket Tab ======================================================
websocket_layout = [
    [
        sg.Text('Server : '),
        sg.Input(settings["obs_ws"]["server"] , key='obsws-server',size=(20, 1), expand_x=True)
    ],
    [
        sg.Text('Port : '),
        sg.Input(settings["obs_ws"]["port"] , key='obsws-port',size=(20, 1), expand_x=True)
    ],
    [
        sg.Text('Password : '),
        sg.Input(settings["obs_ws"]["password"] , key='obsws-password', password_char='*',size=(20, 1), expand_x=True)
    ],
    [
        sg.Button('Connect', key='obsws-connect'),
        sg.Button('Disconnect', key='obsws-disconnect'),
        sg.Text('Not connected', key="obsws-status"),
    ],
]
#Websocket Tab ======================================================

#MQTT Tab ===========================================================
mqtt_layout = [
    [
        sg.Text('Server : '),
        sg.Input(settings["mqtt"]["broker"] , key='mqtt-broker',size=(15, 1), expand_x=True),
        sg.Text('Port : '),
        sg.Input(settings["mqtt"]["port"] , key='mqtt-port',size=(5, 1), expand_x=True)
    ],
    [
        sg.Text('User : '),
        sg.Input(settings["mqtt"]["username"] , key='mqtt-username',size=(10, 1), expand_x=True),
        sg.Text('Pass : '),
        sg.Input(settings["mqtt"]["password"] , key='mqtt-password',size=(10, 1),password_char='*', expand_x=True)
    ],
    [
        sg.Text('Topic IN : '),
        sg.Input(settings["mqtt"]["topic_in"] , key='mqtt-topicin',size=(20, 1), expand_x=True)
    ],
    [
        sg.Text('Topic OUT : '),
        sg.Input(settings["mqtt"]["topic_out"] , key='mqtt-topicout',size=(20, 1), expand_x=True)
    ],
    [
        sg.Button('Connect', key='mqtt-connect'),
        sg.Button('Disconnect', key='mqtt-disconnect'),
    ],
]
#MQTT Tab ===========================================================

#Scene Tab ==========================================================
scenes_layout = [
    [sg.Text('Create new scenes', font=('Helvetica', 10, 'bold', 'underline'))],
    [
        sg.Text('Scene name : '),
        sg.Input("Scene name" , key='polygons-name',size=(20, 1), expand_x=True)],
    [   
        sg.Button('Reset selection', key='polygons-reset'),
        sg.Button('Save selection', key='polygons-save'),
        sg.Button('Show scenes', key='polygons-show')
        
    ],
    [sg.Text('Edit saved scenes', font=('Helvetica', 10, 'bold', 'underline'))],
    [
        sg.OptionMenu(values=('Demo 1','Demo 2'), default_value ='Demo 1',  key='scenes-list', size=(15,10)),
        sg.Button('Delete scene', key='polygons-delete')
    ],
]

#Scene Tab ==========================================================

#GUI LAYOUT=========================================================
layout = [ 
    top_layout,
    [
    sg.TabGroup([[
        sg.Tab('Video', video_layout),
        sg.Tab('Scenes', scenes_layout),
        sg.Tab('Websocket', websocket_layout),
        sg.Tab('MQTT', mqtt_layout),
        ]
    ],key='-TAB GROUP-', expand_x=True, expand_y=True)
    ]
    ]
#GUI LAYOUT=========================================================

#Windows creation
window = sg.Window('OBS face detection', layout ,right_click_menu=right_click_menu_def, right_click_menu_tearoff=True, grab_anywhere=True, resizable=True, margins=(0,0), use_custom_titlebar=False, finalize=False, keep_on_top=True, return_keyboard_events=True)