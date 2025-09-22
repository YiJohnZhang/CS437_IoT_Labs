# Minqiang Liu(mliu110@illinois.edu), Yi Zhang(yjzhang2@illinois.edu)
#
# A* grid driving with concurrent perception.
# If a "stop sign" is detected within 20cm, pause 3s and then continue.
# Servo sweep limited to 45–50 degrees while driving; initial angle is 45°.

import time
import math
import argparse
import threading
import os
import numpy as np
from heapq import heappush, heappop
from typing import Tuple, Optional

from motor import Ordinary_Car
from servo import Servo
from ultrasonic import Ultrasonic
from picamera2 import Picamera2

from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from PIL import Image

# --------------------------- Constants ----------------------------------------
SAFE_SPEED = 600
TURN_SPEED = 1000

CM_PER_SEC = 50.0
DEG_PER_SEC = 95.0

POSE_SETTLE_SEC = 0.0
TURN_PAUSE_SEC = 0.5
TURN_AFTER_PAUSE_SEC = 3.0
MAX_RUNTIME_SEC = 180.0

CELL_CM = 20.0
ORIGIN = (0, 0)
START_YAW_DEG = 0.0

# Perception/stop settings
STOP_LABEL = "stop sign"
STOP_DISTANCE_CM = 20.0   # match the requirement: stop if < 20 cm
STOP_HOLD_SEC = 3.0
SERVO_MIN = 45
SERVO_MAX = 50
SERVO_STEP = 5

# Forward driving polling granularity (to react quickly to stop events)
DRIVE_POLL_DT = 0.05  # seconds

# --------------------------- Motor helpers -----------------------------------
def stop(car: Ordinary_Car):
    car.set_motor_model(0, 0, 0, 0)

def forward_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(SAFE_SPEED + 300, SAFE_SPEED, SAFE_SPEED, SAFE_SPEED)
    time.sleep(max(0.0, seconds))
    stop(car)

def forward_time_slice(car: Ordinary_Car, seconds: float):
    car.set_motor_model(SAFE_SPEED + 300, SAFE_SPEED, SAFE_SPEED, SAFE_SPEED)
    time.sleep(max(0.0, seconds))
    # intentional: no stop() here (used inside polling loop)

def backward_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(-SAFE_SPEED, -SAFE_SPEED, -SAFE_SPEED, -SAFE_SPEED)
    time.sleep(max(0.0, seconds))
    stop(car)

def spin_left_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(-TURN_SPEED - 300, -TURN_SPEED, TURN_SPEED, TURN_SPEED)
    time.sleep(max(0.0, seconds))
    stop(car)

def spin_right_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(TURN_SPEED, TURN_SPEED, -TURN_SPEED - 300, -TURN_SPEED)
    time.sleep(max(0.0, seconds))
    stop(car)

def drive_forward_cm(car: Ordinary_Car, cm: float):
    if abs(cm) < 1e-3:
        return
    secs = abs(cm) / max(1e-6, CM_PER_SEC)
    if cm > 0:
        forward_time(car, secs)
    else:
        backward_time(car, secs)

def rotate_in_place_deg(car: Ordinary_Car, deg: float):
    if abs(deg) < 1.0:
        return
    secs = abs(deg) / max(1e-6, DEG_PER_SEC)
    if deg > 0:
        spin_left_time(car, secs)
    else:
        spin_right_time(car, secs)

# --------------------------- A* Planner --------------------------------------
DIRS = [(-1,0), (1,0), (0,-1), (0,1)]  # N/S/W/E

def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def astar(grid: np.ndarray, start, goal):
    """Compute A* path on occupancy grid (0=free,1=obstacle)."""
    h, w = grid.shape
    sx, sy = start; gx, gy = goal
    if not (0 <= sx < h and 0 <= sy < w and 0 <= gx < h and 0 <= gy < w):
        return None
    if grid[gx, gy] == 1:
        return None

    gscore = {start: 0}
    fscore = {start: heuristic(start, goal)}
    came = {}
    pq = []
    heappush(pq, (fscore[start], start))

    while pq:
        _, cur = heappop(pq)
        if cur == goal:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            return path[::-1]
        cx, cy = cur
        for dx, dy in DIRS:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < h and 0 <= ny < w):
                continue
            if grid[nx, ny] == 1:
                continue
            tentative = gscore[cur] + 1
            if tentative < gscore.get((nx, ny), 1e9):
                came[(nx, ny)] = cur
                gscore[(nx, ny)] = tentative
                fscore[(nx, ny)] = tentative + heuristic((nx, ny), goal)
                heappush(pq, (fscore[(nx,ny)], (nx,ny)))
    return None

# --------------------------- Utils -------------------------------------------
def print_ascii_grid(grid: np.ndarray, path=None, start=None, goal=None):
    """Pretty-print the grid (0=free ' ', 1=obstacle '#'). Optionally overlay path."""
    h, w = grid.shape
    path_set = set(path) if path else set()
    rows = []
    for r in range(h):
        line = []
        for c in range(w):
            if start and (r, c) == start:
                ch = 'S'
            elif goal and (r, c) == goal:
                ch = 'G'
            elif (r, c) in path_set:
                ch = '.'
            else:
                ch = '#' if grid[r, c] == 1 else ' '
            line.append(ch)
        rows.append(''.join(line))
    print("[GRID]")
    for row in rows:
        print(row)

# --------------------------- Perception signal --------------------------------
class StopSignal:
    """One-shot signal from perception to navigator."""
    def __init__(self):
        self._evt = threading.Event()
        self._lock = threading.Lock()

    def request_stop(self):
        with self._lock:
            self._evt.set()

    def consume_if_set(self) -> bool:
        with self._lock:
            if self._evt.is_set():
                self._evt.clear()
                return True
            return False

# --------------------------- Detection classes --------------------------------
class TrafficClassifier:
    def __init__(self):
        self.model_path = "mobilenetv2_custom.keras"
        self.img_size = (224, 224)
        # Make sure this ordering matches your trained model!
        self.class_names = ["stop sign", "traffic cone", "traffic lights", "walker"]
        self.model = load_model(self.model_path)

    def ImagePredict(self, img_path: str):
        img = image.load_img(img_path, target_size=self.img_size)
        arr = image.img_to_array(img).astype(np.float32)
        arr = np.expand_dims(arr, axis=0)
        probs = self.model.predict(arr, verbose=0)[0]
        idx = int(np.argmax(probs))
        label = self.class_names[idx]
        score = float(probs[idx])
        return label, score

class PerceptionUnit:
    def __init__(self, picam2: Picamera2, ultrasonic: Ultrasonic, servo: Servo,
                 angle_min: int, angle_max: int, pic_detection: TrafficClassifier,
                 servo_channel: int = 0, settle_sec: float = 0.12, shots_dir: str = "pic"):
        if angle_min > angle_max:
            raise ValueError("angle_min must be <= angle_max")
        self.picam2 = picam2
        self.ultrasonic = ultrasonic
        self.servo = servo
        self.angle_min = int(angle_min)
        self.angle_max = int(angle_max)
        self.pic_detection = pic_detection
        self.servo_channel = int(servo_channel)
        self.settle_sec = float(settle_sec)
        self.shots_dir = shots_dir
        os.makedirs(self.shots_dir, exist_ok=True)
        self._current_angle: Optional[int] = None

    def _clamp_angle(self, angle: int) -> int:
        return max(self.angle_min, min(self.angle_max, int(angle)))

    def move_to(self, angle: int) -> int:
        angle_used = self._clamp_angle(angle)
        if self._current_angle != angle_used:
            self.servo.set_servo_pwm(self.servo_channel, angle_used)
            self._current_angle = angle_used
        return angle_used

    def _capture_and_save(self, save_path: str) -> str:
        # Capture raw RGB frame and persist a 224x224 JPEG for classification
        frame_uint8 = self.picam2.capture_array("main")  # (H, W, 3) RGB uint8
        Image.fromarray(frame_uint8).resize((224, 224)).save(save_path)
        return save_path

    def capture_predict(self) -> Tuple[str, float, Optional[float], int, str]:
        if self._current_angle is None:
            raise RuntimeError("Servo angle is unknown. Call move_to(angle) first.")
        ts = int(time.time() * 1000)
        img_path = os.path.join(self.shots_dir, f"frame_{self._current_angle}_{ts}.jpg")
        img_path = self._capture_and_save(img_path)
        label, score = self.pic_detection.ImagePredict(img_path)
        distance_cm = self.ultrasonic.get_distance()
        return label, score, distance_cm, self._current_angle, img_path

# --------------------------- Perception worker --------------------------------
class PerceptionWorker(threading.Thread):
    """
    Sweeps servo between 45–50°, captures frames, classifies, and signals stop when:
      label == "stop sign" AND distance_cm < 20.
    """
    def __init__(self, stop_event: threading.Event, stop_signal: StopSignal,
                 angle_min: int = SERVO_MIN, angle_max: int = SERVO_MAX, step: int = SERVO_STEP,
                 shots_dir: str = "pic"):
        super().__init__(daemon=True)
        self.stop_event = stop_event
        self.stop_signal = stop_signal
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.step = step
        self.shots_dir = shots_dir
        self.picam2 = None
        self.ultrasonic = None
        self.servo = None
        self.detector = None
        self.unit: Optional[PerceptionUnit] = None

    def _init_hardware(self):
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_still_configuration(
            main={"format": "RGB888", "size": (224, 224)}
        ))
        self.picam2.start()
        time.sleep(0.5)
        self.ultrasonic = Ultrasonic()
        self.servo = Servo()
        self.detector = TrafficClassifier()
        self.unit = PerceptionUnit(self.picam2, self.ultrasonic, self.servo,
                                   self.angle_min, self.angle_max, self.detector,
                                   servo_channel=0, settle_sec=0.12, shots_dir=self.shots_dir)
        # --- Set initial servo angle to 45° (angle_min) ---
        try:
            self.unit.move_to(self.angle_min)
            time.sleep(self.unit.settle_sec)
            print(f"[DETECT] Servo initialized to {self.angle_min}°.")
        except Exception as e:
            print(f"[DETECT] Failed to set initial servo angle: {e}")

    def run(self):
        try:
            self._init_hardware()
            print("[DETECT] Perception thread started (45–50° sweep).")
        except Exception as e:
            print(f"[DETECT] Init failed: {e}")
            return

        try:
            while not self.stop_event.is_set():
                # Forward sweep
                for angle in range(self.angle_min, self.angle_max + 1, self.step):
                    if self.stop_event.is_set(): break
                    self.unit.move_to(angle)
                    time.sleep(self.unit.settle_sec)
                    label, score, dist, a, path = self.unit.capture_predict()
                    print(f"[DETECT {time.strftime('%H:%M:%S')}] a={a}° | {label} {score:.3f} | dist={dist:.1f}cm")
                    if label == STOP_LABEL and (dist is not None) and dist < STOP_DISTANCE_CM:
                        print(f"[DETECT] STOP condition met: {label}, {dist:.1f}cm")
                        self.stop_signal.request_stop()

                # Backward sweep
                for angle in range(self.angle_max, self.angle_min - 1, -self.step):
                    if self.stop_event.is_set(): break
                    self.unit.move_to(angle)
                    time.sleep(self.unit.settle_sec)
                    label, score, dist, a, path = self.unit.capture_predict()
                    print(f"[DETECT {time.strftime('%H:%M:%S')}] a={a}° | {label} {score:.3f} | dist={dist:.1f}cm")
                    if label == STOP_LABEL and (dist is not None) and dist < STOP_DISTANCE_CM:
                        print(f"[DETECT] STOP condition met: {label}, {dist:.1f}cm")
                        self.stop_signal.request_stop()

        finally:
            try:
                if self.ultrasonic: self.ultrasonic.close()
            except: pass
            try:
                if self.picam2: self.picam2.stop()
            except: pass
            print("[DETECT] Perception thread stopped.")

# --------------------------- Navigator ---------------------------------------
class Navigator:
    def __init__(self, car: Ordinary_Car, stop_signal: StopSignal, cell_cm=CELL_CM):
        self.car = car
        self.stop_signal = stop_signal
        self.cell_cm = float(cell_cm)
        self.x_cm = 0.0
        self.y_cm = 0.0
        self.yaw_deg = START_YAW_DEG

    def set_start(self, x_cm: float, y_cm: float, yaw_deg: float = START_YAW_DEG):
        self.x_cm, self.y_cm, self.yaw_deg = float(x_cm), float(y_cm), float(yaw_deg)

    def _grid_to_world_cm(self, cell, origin=ORIGIN):
        tx_cm = (cell[0] - origin[0]) * self.cell_cm
        ty_cm = (cell[1] - origin[1]) * self.cell_cm
        return tx_cm, ty_cm

    def _rotate_to_heading_toward(self, target_cell, origin=ORIGIN):
        tx, ty = self._grid_to_world_cm(target_cell, origin)
        dx = tx - self.x_cm
        dy = ty - self.y_cm
        # heading measured from +Y axis (forward)
        desired_yaw = math.degrees(math.atan2(dx, dy))
        rot = (desired_yaw - self.yaw_deg + 180) % 360 - 180
        if abs(rot) > 2.0:
            stop(self.car)
            time.sleep(TURN_PAUSE_SEC)
            rotate_in_place_deg(self.car, rot)
            self.yaw_deg = (self.yaw_deg + rot) % 360
            stop(self.car)
            time.sleep(TURN_AFTER_PAUSE_SEC)

    def _drive_run_to(self, last_cell_in_run, origin=ORIGIN):
        """
        Drive forward to the last cell in the current straight run,
        but poll the perception signal every DRIVE_POLL_DT to pause 3s if needed.
        """
        tx, ty = self._grid_to_world_cm(last_cell_in_run, origin)
        dx = tx - self.x_cm
        dy = ty - self.y_cm
        remaining_cm = math.hypot(dx, dy)

        if remaining_cm <= 0.5:
            return

        try:
            while remaining_cm > 0.5:
                if self.stop_signal.consume_if_set():
                    print("[NAV] STOP signal received -> stopping 3s, then continue.")
                    stop(self.car)
                    time.sleep(STOP_HOLD_SEC)
                # advance one small slice
                forward_time_slice(self.car, DRIVE_POLL_DT)
                advanced = CM_PER_SEC * DRIVE_POLL_DT
                remaining_cm -= advanced
        finally:
            stop(self.car)

        self.x_cm, self.y_cm = tx, ty
        if POSE_SETTLE_SEC > 0:
            time.sleep(POSE_SETTLE_SEC)

    def follow_path(self, path, origin=ORIGIN):
        if not path or len(path) < 2:
            print("[NAV] Empty or short path.")
            return False

        for cell in path:
            print(f"[NAV] Path cell: {cell}")

        i = 1
        while i < len(path):
            prev = path[i - 1]
            cur = path[i]
            step = (cur[0] - prev[0], cur[1] - prev[1])

            # find end of straight run
            run_end = i
            while run_end + 1 < len(path):
                a = path[run_end]
                b = path[run_end + 1]
                nxt = (b[0] - a[0], b[1] - a[1])
                if nxt != step:
                    break
                run_end += 1

            last_cell = path[run_end]
            self._rotate_to_heading_toward(last_cell, origin=origin)
            self._drive_run_to(last_cell, origin=origin)
            i = run_end + 1

        stop(self.car)
        return True

# --------------------------- Main --------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", nargs=2, type=int, required=True,
                        help="Goal cell coordinates: row col")
    args = parser.parse_args()
    goal = (args.goal[0], args.goal[1])

    print("[INFO] Init motor ...")
    car = Ordinary_Car()

    # Example grid (10x10) with two obstacle rows
    grid = np.zeros((10, 10), dtype=int)
    grid[4, 2:7] = 1
    grid[6, 3:9] = 1

    start = (0, 0)
    print(f"[INFO] Planning A* path from {start} to {goal} ...")
    path = astar(grid, start, goal)
    print("[INFO] Path:", path)
    print_ascii_grid(grid, path=path, start=start, goal=goal)

    # Perception thread + shared signal
    stop_event = threading.Event()
    stop_signal = StopSignal()
    perception_thread = None
    if not args.no_detect:
        perception_thread = PerceptionWorker(
            stop_event=stop_event,
            stop_signal=stop_signal,
            angle_min=SERVO_MIN, angle_max=SERVO_MAX, step=SERVO_STEP, shots_dir="pic"
        )
        perception_thread.start()

    start_time = time.time()
    try:
        if not path:
            print("[WARN] No path found. Abort.")
            return

        nav = Navigator(car, stop_signal=stop_signal, cell_cm=CELL_CM)
        nav.set_start(0.0, 0.0, START_YAW_DEG)

        print("[INFO] Start driving ... (continuous on straights; stop only to turn; reacts to stop sign <20cm).")
        ok = nav.follow_path(path, origin=ORIGIN)
        print("[RESULT]", "Reached goal." if ok else "Failed.")

        if (time.time() - start_time) > MAX_RUNTIME_SEC:
            print("[INFO] Max runtime reached. Stopping.")

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt. Stopping ...")
    except Exception as ex:
        print(f"[ERROR] Unexpected exception: {ex}")
    finally:
        try: stop(car)
        except Exception: pass
        try: car.close()
        except Exception: pass

        try:
            stop_event.set()
            if perception_thread is not None:
                perception_thread.join(timeout=5.0)
        except Exception:
            pass

        print("[INFO] Cleanup done. Bye.")

if __name__ == "__main__":
    main()
