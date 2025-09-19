
# Minqiang Liu(mliu110@illinois.edu), Yi Zhang(yjzhang2@illinois.edu)

# Object Detection.py
# Compose Picamera2 + Ultrasonic + Servo (with a servo angle range) into a single-shot perception unit.
# Returns: (label: str, score: float, distance_cm: float|None, servo_angle: int)


from __future__ import annotations
from typing import Tuple, Optional
import time
import os
import numpy as np
from PIL import Image

# External deps
from servo import Servo
from ultrasonic import Ultrasonic
from motor import Ordinary_Car  # not used here
from picamera2 import Picamera2

# -------------------------------
# Keras classifier (path-based)
# -------------------------------
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model

class TrafficClassifier:
    def __init__(self):
        self.model_path = "mobilenetv2_custom.keras"
        self.img_size = (224, 224)
        self.class_names = ["stop sign", "traffic cone", "traffic lights", "walker"]
        self.model = load_model(self.model_path)

    def ImagePredict(self, img_path: str):
        # Load and resize the image to the model's expected size
        img = image.load_img(img_path, target_size=self.img_size)
        arr = image.img_to_array(img).astype(np.float32)
        arr = np.expand_dims(arr, axis=0)
        probs = self.model.predict(arr, verbose=0)[0]
        idx = int(np.argmax(probs))
        label = self.class_names[idx]
        score = float(probs[idx])
        return label, score

# -------------------------------
# Core class
# -------------------------------
class PerceptionUnit:
    def __init__(
        self,
        picam2: Picamera2,
        ultrasonic: Ultrasonic,
        servo: Servo,
        angle_min: int,
        angle_max: int,
        pic_detection: TrafficClassifier,
        servo_channel: str = "0",
        settle_sec: float = 0.12,
        shots_dir: str = "pic",
    ):
        if angle_min > angle_max:
            raise ValueError("angle_min must be <= angle_max")
        self.picam2 = picam2
        self.ultrasonic = ultrasonic
        self.servo = servo
        self.angle_min = int(angle_min)
        self.angle_max = int(angle_max)
        self.pic_detection = pic_detection
        self.servo_channel = servo_channel
        self.settle_sec = float(settle_sec)
        self.shots_dir = shots_dir
        os.makedirs(self.shots_dir, exist_ok=True)

        # Track current angle to avoid unnecessary movements if you call move_to with same angle
        self._current_angle: Optional[int] = None

    def _clamp_angle(self, angle: int) -> int:
        return max(self.angle_min, min(self.angle_max, int(angle)))

    def move_to(self, angle: int) -> int:
        """Move servo to angle WITHOUT any capture."""
        angle_used = self._clamp_angle(angle)
        if self._current_angle != angle_used:
            self.servo.set_servo_pwm(self.servo_channel, angle_used)
            self._current_angle = angle_used
        return angle_used

    def _capture_and_save(self, save_path: str) -> str:
        """Capture frame, save to disk, return path."""
        frame_uint8 = self.picam2.capture_array("main")  # (H, W, 3), uint8, RGB
        # Ensure 224x224 for classifier
        img224 = Image.fromarray(frame_uint8).resize((224, 224))
        img224.save(save_path)
        return save_path

    def capture_predict(self) -> Tuple[str, float, Optional[float], int, str]:
        """
        Capture an image at the CURRENT angle (servo is NOT moved here),
        then run prediction and read distance.
        Returns: label, score, distance_cm, angle_used, img_path
        """
        if self._current_angle is None:
            raise RuntimeError("Servo angle is unknown. Call move_to(angle) first.")

        # unique filename per shot
        timestamp = int(time.time() * 1000)   # ms
        img_path = os.path.join(self.shots_dir, f"frame_{self._current_angle}_{timestamp}.jpg")
        img_path = self._capture_and_save(img_path)

        label, score = self.pic_detection.ImagePredict(img_path)
        distance_cm = self.ultrasonic.get_distance()
        return label, score, distance_cm, self._current_angle, img_path


# -------------------------------
# Main for quick testing
# -------------------------------
def main():
    # 1) Camera
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_still_configuration(
            main={"format": "RGB888", "size": (224, 224)}
        )
    )
    picam2.start()
    time.sleep(0.5)  # Let exposure settle

    # 2) Sensors / Actuators
    ultrasonic = Ultrasonic()
    servo = Servo()

    # 3) Classifier
    detector = TrafficClassifier()

    # 4) Perception unit
    unit = PerceptionUnit(
        picam2=picam2,
        ultrasonic=ultrasonic,
        servo=servo,
        angle_min=0,
        angle_max=90,
        pic_detection=detector,
        servo_channel="0",
        settle_sec=0.12,
        shots_dir="pic",
    )

    try:
        while True:
            # Forward sweep: 45 -> 50
            for angle in range(45, 51, 1):
                angle_used = unit.move_to(angle)            # MOVE ONLY (no capture)
                time.sleep(unit.settle_sec)                 # wait to be stable
                label, score, dist_cm, a, path = unit.capture_predict()  # capture+predict at stable angle
                print(f"[{time.strftime('%H:%M:%S')}] angle={a}\u00B0 | label={label}, score={score:.3f}, distance_cm={dist_cm}, img={os.path.basename(path)}")
                time.sleep(1)

            # Backward sweep: 50 -> 45
            for angle in range(50, 44, -1):
                angle_used = unit.move_to(angle)            # MOVE ONLY (no capture)
                time.sleep(unit.settle_sec)                 # wait to be stable
                label, score, dist_cm, a, path = unit.capture_predict()  # capture+predict at stable angle
                print(f"[{time.strftime('%H:%M:%S')}] angle={a}\u00B0 | label={label}, score={score:.3f}, distance_cm={dist_cm}, img={os.path.basename(path)}")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt received. Exiting...")

    finally:
        try:
            ultrasonic.close()
        except:
            pass
        try:
            picam2.stop()
        except:
            pass
        print("[INFO] Done.")


if __name__ == "__main__":
    main()
