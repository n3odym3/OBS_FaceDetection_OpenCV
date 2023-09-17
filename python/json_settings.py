import json

with open("settings.json", 'r') as file:
    settings = json.load(file)

def save_json(settings):
    json_object = json.dumps(settings, indent=1)
    with open("settings.json", "w") as outfile:
        outfile.write(json_object)