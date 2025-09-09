# UIUC_CS437_Lab01A.py
# Minqiang Liu(mliu110@illinois.edu), Yi Zhang(yjzhang2@illinois.edu)
# NOTE: Design and code it ourself, and use ChatGPT to help with optimization.
# Purpose: Continuous slow drive with frequent ranging and a small, slow servo sweep.
# Preserved behaviors:
#   - Drive forward continuously until an obstacle is detected.
#   - If obstacle is within FRONT_STOP_CM:
#       * STOP & hold,
#       * REVERSE,
#       * LEFT turn to bypass,
#       * Move forward again and continue.
#   - If obstacle in a caution zone (<= FRONT_CAUTION_CM), preemptive LEFT bypass.

import time
import threading
from collections import deque

from ultrasonic import Ultrasonic
from servo import Servo
from motor import Ordinary_Car  # Motor driver

SAFE_SPEED = 600                 # Slow forward speed (max magnitude ~4095)
TURN_SPEED = 700                 # Slow tank turn speed
REVERSE_SPEED = -700             # Gentle reverse

FRONT_STOP_CM = 50.0             # Immediate stop threshold
FRONT_CAUTION_CM = 28.0          # Caution threshold to proactively bypass

STOP_HOLD_SEC = 1.0              # Stop & hold before reversing
REVERSE_SEC = 1.5                # Reverse duration
TURN_LEFT_SEC = 1.0              # Left turn duration to bypass
POST_BYPASS_ADVANCE_SEC = 0.40   # Short forward move after turning

MAX_RUNTIME_SEC = 180.0          # Hard cap: 3 minutes

RANGE_THREAD_PERIOD = 0.03       # ~33 Hz sampling loop (high-frequency)
HISTORY_SIZE = 15                # Keep last N samples for robust filtering
VALID_MIN_CM = 2.0               # Discard physically implausible low readings
VALID_MAX_CM = 400.0             # Discard too-far spikes
USE_MIN_FOR_SAFETY = True        # Conservative: consider min of window when deciding stops

ANGLE_MIN = 25                  # left bound of the small sweep
ANGLE_MAX = 65                  # right bound of the small sweep
SWEEP_STEP = 9                  # degrees per step
SWEEP_DWELL_SEC = 0.20          # how long to dwell at each step (keeps sweep slow)
POSE_SETTLE_SEC = 0.08          # settle a bit after each movement

def stop(motor: Ordinary_Car):
    print("[ACTION] STOP")
    motor.set_motor_model(0, 0, 0, 0)

def stop_hold(motor: Ordinary_Car, seconds: float):
    print(f"[ACTION] STOP & HOLD for {seconds:.2f}s")
    motor.set_motor_model(0, 0, 0, 0)
    time.sleep(max(0.0, seconds))

def forward_continuous(motor: Ordinary_Car):
    print("[ACTION] FORWARD (continuous, slow)")
    motor.set_motor_model(SAFE_SPEED, SAFE_SPEED, SAFE_SPEED, SAFE_SPEED)

def reverse_for(motor: Ordinary_Car, seconds: float):
    print(f"[ACTION] REVERSE for {seconds:.2f}s")
    motor.set_motor_model(REVERSE_SPEED, REVERSE_SPEED, REVERSE_SPEED, REVERSE_SPEED)
    time.sleep(max(0.0, seconds))
    stop(motor)

def turn_left(motor: Ordinary_Car, seconds: float):
    print(f"[ACTION] TURN LEFT for {seconds:.2f}s")
    motor.set_motor_model(-TURN_SPEED, -TURN_SPEED, TURN_SPEED, TURN_SPEED)
    time.sleep(max(0.0, seconds))
    stop(motor)

def post_bypass_advance(motor: Ordinary_Car, seconds: float):
    print(f"[ACTION] POST-BYPASS FORWARD for {seconds:.2f}s")
    motor.set_motor_model(SAFE_SPEED, SAFE_SPEED, SAFE_SPEED, SAFE_SPEED)
    time.sleep(max(0.0, seconds))
    stop(motor)

# ---------------------------- Ranging helpers ----------------------------
def robust_window_stats(window: deque):
    if not window:
        return 999.0, 999.0
    vals = list(window)
    vals.sort()
    n = len(vals)
    median = vals[n // 2] if n % 2 == 1 else 0.5 * (vals[n // 2 - 1] + vals[n // 2])
    return float(median), float(vals[0])

def range_worker(sonic: Ultrasonic, history: deque, stop_event: threading.Event):
    print("[INFO] Ranging thread started (high frequency).")
    while not stop_event.is_set():
        d = sonic.get_distance()
        if d is not None and VALID_MIN_CM <= d <= VALID_MAX_CM:
            history.append(d)
            if len(history) > HISTORY_SIZE:
                history.popleft()
            print(f"[SENSE] FRONT={d:.1f} cm (raw)")
        else:
            print("[SENSE] FRONT invalid/None")
        time.sleep(RANGE_THREAD_PERIOD)
    print("[INFO] Ranging thread stopping...")

# ---------------------------- Servo sweep worker ----------------------------
def servo_sweep_worker(servo: Servo, stop_event: threading.Event):
    print("[INFO] Servo sweep thread started ({}°..{}°).".format(ANGLE_MIN, ANGLE_MAX))
    angle = ANGLE_MIN
    direction = 1  # +1 moving toward ANGLE_MAX, -1 moving toward ANGLE_MIN
    while not stop_event.is_set():
        servo.set_servo_pwm('0', int(angle))
        time.sleep(POSE_SETTLE_SEC)
        time.sleep(SWEEP_DWELL_SEC)

        angle += direction * SWEEP_STEP
        if angle >= ANGLE_MAX:
            angle = ANGLE_MAX
            direction = -1
        elif angle <= ANGLE_MIN:
            angle = ANGLE_MIN
            direction = 1
    print("[INFO] Servo sweep thread stopping...")

def main():
    print("[INFO] Initializing Ultrasonic, Servo, and Motor...")
    sonic = Ultrasonic()       # Default: trigger=27, echo=22
    servo = Servo()            # PCA9685 @50Hz; channel '0' used
    motor = Ordinary_Car()     # DC motor driver via PCA9685

    # Shared ranging buffer and threads
    front_history = deque(maxlen=HISTORY_SIZE)
    stop_event = threading.Event()
    t_range = threading.Thread(target=range_worker, args=(sonic, front_history, stop_event), daemon=True)
    t_servo = threading.Thread(target=servo_sweep_worker, args=(servo, stop_event), daemon=True)

    try:
        # Start ranging and servo sweep threads
        t_range.start()
        t_servo.start()

        # Begin continuous forward motion
        forward_continuous(motor)

        start_time = time.time()
        while True:
            # Stop after 3 minutes
            if (time.time() - start_time) >= MAX_RUNTIME_SEC:
                print("[INFO] Max runtime reached. Stopping.")
                break

            # Get robust estimates
            median_cm, min_cm = robust_window_stats(front_history)
            print(f"[SENSE] FRONT(median)={median_cm:.1f} cm, FRONT(min)={min_cm:.1f} cm")

            # Decision metric:
            decision_cm = min_cm if (USE_MIN_FOR_SAFETY and len(front_history) >= 3) else median_cm

            # Immediate stop + reverse + left bypass
            if decision_cm <= FRONT_STOP_CM:
                print(f"[DECIDE] <= {FRONT_STOP_CM:.0f} cm (decision {decision_cm:.1f}). Stop-Hold, Reverse, Left bypass.")
                stop_hold(motor, STOP_HOLD_SEC)
                reverse_for(motor, REVERSE_SEC)
                turn_left(motor, TURN_LEFT_SEC)
                post_bypass_advance(motor, POST_BYPASS_ADVANCE_SEC)
                forward_continuous(motor)

            # Preemptive bypass in caution range
            elif decision_cm <= FRONT_CAUTION_CM:
                print(f"[DECIDE] Caution zone ({decision_cm:.1f} cm). Preemptive LEFT bypass.")
                stop(motor)
                turn_left(motor, TURN_LEFT_SEC * 0.8)
                post_bypass_advance(motor, POST_BYPASS_ADVANCE_SEC * 0.8)
                forward_continuous(motor)

            # Else keep moving; ranging & sweep continue concurrently
            time.sleep(0.04)

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt received. Stopping...")

    except Exception as ex:
        print(f"[ERROR] Unexpected exception: {ex}")

    finally:
        # Cleanup
        try:
            stop_event.set()
        except Exception:
            pass
        try:
            if t_range.is_alive():
                t_range.join(timeout=1.0)
        except Exception:
            pass
        try:
            if t_servo.is_alive():
                t_servo.join(timeout=1.0)
        except Exception:
            pass
        try:
            stop(motor)
        except Exception:
            pass
        try:
            motor.close()
        except Exception:
            pass
        try:
            sonic.close()
        except Exception:
            pass
        print("[INFO] Cleanup done. Bye.")

if __name__ == "__main__":
    main()

