import json
import boto3

# IoT Data Plane client (used to publish messages back to AWS IoT Core)
iot_client = boto3.client("iot-data", region_name="us-west-2")

# Topic where inference results will be published
INFERENCE_TOPIC = "smartcar/inference"


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    # ----------------------------------------------------------------------
    # Parse incoming message
    # When an IoT Rule triggers Lambda, the payload might appear in:
    #   - event["payload"] (string or Base64 encoded)
    #   - or directly inside the event object depending on the Rule settings.
    # ----------------------------------------------------------------------
    try:
        message = event

        # If IoT Rule wraps data in "payload", decode it
        if "payload" in event:
            message = json.loads(event["payload"])

        # Extract fields with safe defaults
        device_id = message.get("deviceId", "Unknown")
        co2 = message.get("co2", None)
        speed = message.get("speed", None)
        timestamp = message.get("timestamp", None)

    except Exception as e:
        print("Error parsing message:", e)
        return {"statusCode": 400, "body": "Invalid input format"}

    # ----------------------------------------------------------------------
    # Simple inference logic
    # You can replace this with more advanced CO₂ analysis or ML models.
    # ----------------------------------------------------------------------
    if co2 is None:
        result = "NO_DATA"
    elif co2 < 800:
        result = "GOOD"
    elif co2 < 1500:
        result = "MODERATE"
    else:
        result = "BAD"

    # Build inference result message
    inference_result = {
        "deviceId": device_id,
        "co2": co2,
        "speed": speed,
        "timestamp": timestamp,
        "inference": result
    }

    # ----------------------------------------------------------------------
    # Publish inference result to the IoT topic
    # SmartCar or Greengrass components can subscribe to this topic
    # to receive real-time inference updates.
    # ----------------------------------------------------------------------
    iot_client.publish(
        topic=INFERENCE_TOPIC,
        qos=0,
        payload=json.dumps(inference_result)
    )

    print("Published inference:", inference_result)

    # ----------------------------------------------------------------------
    # Return result to Lambda caller
    # IoT Rule does not require this return value, but it is useful for testing.
    # ----------------------------------------------------------------------
    return {
        "statusCode": 200,
        "body": json.dumps(inference_result)
    }
