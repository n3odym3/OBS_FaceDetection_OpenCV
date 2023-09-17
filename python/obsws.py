from obswebsocket import obsws, requests

class OBS_WS : 
    client = None
    
    def connect(self, config):
        try :
            if self.client :
                self.client.disconnect()
            self.client = obsws(config["server"], config["port"],config["password"])
            self.client.connect()
        except :
            self.client = None
            return "Error !"
        return "Connected"
    
    def disconnect(self):
        if self.client : 
            self.client.disconnect()
            self.client = None
        return "Disconnected"

    def set_scene(self, scene_name):
        if self.client :
            self.client.call(requests.SetCurrentProgramScene(sceneName=scene_name))