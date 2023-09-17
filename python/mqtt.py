#!/usr/bin/env python
import paho.mqtt.client as mqtt

def mqtt_callback(client, from_mqtt, message):
    from_mqtt.put((message.topic,message.payload.decode("utf-8")))

def mqtt_handler(settings, from_mqtt, to_mqtt):
    client = mqtt.Client("mqtt_client")
    client.username_pw_set(settings['username'], settings['password'])
    client.connect(settings['broker'],settings['port'])
    client.subscribe(settings['topic_in'])
    client.user_data_set(from_mqtt)
    client.on_message = mqtt_callback

    while True :
        client.loop()
        if not to_mqtt.empty():
            topic, payload =  to_mqtt.get()
            client.publish(topic, payload)