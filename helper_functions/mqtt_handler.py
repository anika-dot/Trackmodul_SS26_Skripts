'''
This module provides a simple wrapper around the Paho MQTT client to facilitate 
connecting to a broker, subscribing to topics, and publishing messages. It also 
allows registering callbacks for specific topics to handle incoming messages.
'''

import paho.mqtt.client as mqtt
import json

class MQTTHandler:
    '''
    MQTTHandler is a simple wrapper around the Paho MQTT client to manage connections,
    subscriptions, and message publishing.
    '''
    def __init__(self, broker, port, client_id):
        self.client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.callbacks = {}

        self.broker = broker
        self.port = port

    def connect(self):
        '''
        Connects to the MQTT broker and starts the network loop.
        '''
        print(f"[CONNECTING] {self.broker}:{self.port}")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def subscribe(self, topic, callback):
        '''
        Subscribes to a topic and registers a callback for incoming messages on that topic.
        '''
        self.callbacks[topic] = callback
        self.client.subscribe(topic)
        print(f"[SUBSCRIBED] {topic}")

    def publish(self, topic, payload):
        '''
        Publishes a message to a topic. Payload can be a string or a dictionary
        (which will be converted to JSON).
        '''
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        print(f"[PUBLISH] {topic} -> {payload}")
        self.client.publish(topic, payload, qos=1)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        '''
        Callback for when the client receives a connect response from the server.
        '''
        print("[CONNECTED]")

    def on_message(self, client, userdata, msg):
        '''
        Callback for when a PUBLISH message is received from the server.
        It checks if the topic matches any registered callbacks and calls the appropriate one.
        '''
        payload = msg.payload.decode()
        print(f"[RECV] {msg.topic} -> {payload}")

        for topic, callback in self.callbacks.items():
            if mqtt.topic_matches_sub(topic, msg.topic):
                callback(msg.topic, payload)

    def disconnect(self):
        '''
        Disconnects from the MQTT broker and stops the network loop.
        '''
        self.client.loop_stop()
        self.client.disconnect()
