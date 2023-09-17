import json

def save_json(settings):
    json_object = json.dumps(settings, indent=1)
    with open("./settings.json", "w") as outfile:
        outfile.write(json_object)

try:
    with open("./settings.json", 'r') as openfile:
        settings = json.load(openfile)
except :
    settings = {
        "yunet": {
            "model": "./face_detection_yunet_2023mar.onnx"
        },
        "mqtt": {
            "broker": "192.168.1.100",
            "port": 1883,
            "username": "user",
            "password": "password",
            "topic_in": "facedetect/in",
            "topic_out": "facedetect/out"
        },
        "obs_ws": {
            "server": "192.168.1.10",
            "port": "4455",
            "password": "password"
        },
        "scenes": {}
    }
    save_json(settings)

