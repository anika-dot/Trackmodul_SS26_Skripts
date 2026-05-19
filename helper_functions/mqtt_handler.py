import paho.mqtt.client as mqtt
import json

class MQTTHandler:
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
        print(f"[CONNECTING] {self.broker}:{self.port}")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def subscribe(self, topic, callback):
        self.callbacks[topic] = callback
        self.client.subscribe(topic)
        print(f"[SUBSCRIBED] {topic}")

    def publish(self, topic, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        print(f"[PUBLISH] {topic} -> {payload}")
        self.client.publish(topic, payload, qos=1)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print("[CONNECTED]")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"[RECV] {msg.topic} -> {payload}")

        for topic, callback in self.callbacks.items():
            if mqtt.topic_matches_sub(topic, msg.topic):
                callback(msg.topic, payload)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()