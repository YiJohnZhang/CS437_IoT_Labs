from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import json
import random

# AWS IoT endpoint and MQTT client configuration
MQTT_ENDPOINT = "a1g133r7lciy1a-ats.iot.us-west-2.amazonaws.com"
CLIENT_ID = "SmartCar01"

# MQTT topics
PUBLISH_TOPIC = "smartcar/data"            # Topic for sending sensor data
SUBSCRIBE_TOPIC = "smartcar/inference"     # Topic to receive Lambda inference results

# Paths to device certificates
ROOT_CA = "certs/AmazonRootCA1.pem"
PRIVATE_KEY = "certs/0cafd3d41f5430df50e44cf35f5a452d414ac1c49b40a12b1b4e65caf2444b40-private.pem.key"
CERT_FILE = "certs/0cafd3d41f5430df50e44cf35f5a452d414ac1c49b40a12b1b4e65caf2444b40-certificate.pem.crt"


# ------------------------------------------------------------------------------
# Callback function - executed whenever a message arrives on smartcar/inference
# ------------------------------------------------------------------------------
def inference_callback(client, userdata, message):
    payload = message.payload.decode()
    print("\nReceived inference result :")
    print(payload)
    print("\n\n")


# ------------------------------------------------------------------------------
# Generate simulated sensor data
# ------------------------------------------------------------------------------

def get_sensor_data():
    """
    Generates random sensor values for CO2 and speed.
    Returns:
        dict: A JSON-like dictionary with deviceId, co2, speed, timestamp.
    """
    return {
        "deviceId": CLIENT_ID,
        "co2": round(random.uniform(400, 2000), 2),     # Simulated CO2 (ppm)
        "speed": round(random.uniform(0, 2), 2),        # Simulated speed (m/s)
        "timestamp": int(time.time())                   # Unix timestamp
    }


# ------------------------------------------------------------------------------
# Main MQTT logic
# ------------------------------------------------------------------------------

def main():
    # Create the AWS IoT MQTT client
    client = AWSIoTMQTTClient(CLIENT_ID)
    client.configureEndpoint(MQTT_ENDPOINT, 8883)
    client.configureCredentials(ROOT_CA, PRIVATE_KEY, CERT_FILE)

    # Connect to AWS IoT Core
    print("\n\nConnecting to AWS IoT...\n")
    time.sleep(1)

    client.connect()
    print("Connected!\n")
    time.sleep(1)

    # --------------------------------------------------------------------------
    # Subscribe to inference results from Lambda
    # --------------------------------------------------------------------------
    client.subscribe(SUBSCRIBE_TOPIC, 0, inference_callback)
    print(f"Subscribed to {SUBSCRIBE_TOPIC}\n")
    time.sleep(1)

    # --------------------------------------------------------------------------
    # Continuously publish sensor data to AWS IoT Core
    # --------------------------------------------------------------------------
    while True:
        payload = get_sensor_data()
        print("Publishing:", payload)

        # Publish data to AWS IoT Core
        client.publish(PUBLISH_TOPIC, json.dumps(payload), 0)

        # Wait before sending the next sensor reading
        time.sleep(3)


# Entry point
if __name__ == "__main__":
    main()
