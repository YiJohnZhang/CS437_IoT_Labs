'''
Minqiang Liu (mliu110), Yi Zhang (yjzhang2)

Large amount of code inherited from `UIUC_CS437_Lab01A.py`
Idea: just ignore obstacles until it is close enough
'''
import time
import threading

import numpy as np


ANGLE_MIN = 25			# left bound of the small sweep
ANGLE_MAX = 65			# right bound of the small sweep
SWEEP_STEP = 9			# degrees per step

VALID_MIN_CM = 2.0		# Discard physically implausible low readings
VALID_MAX_CM = 300.0	# Discard too-far spikes
SWEEP_DWELL_SEC = 0.20	# how long to dwell at each step (keeps sweep slow)
POSE_SETTLE_SEC = 0.08	# settle a bit after each movement

MAP_SIZE = 16			# https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/blob/master/Code/Server/ultrasonic.py is 3.0 m?

# ---------------------------- SERVO SWEEP AND RANGE ----------------------------
def servo_sweep_and_range_worker(ultrasonic: Ultrasonic, servo: Servo, vision_window, stop_event: threading.Event):
	print("[INFO] Servo sweep thread started ({}°..{}°).".format(ANGLE_MIN, ANGLE_MAX))
	
	angle = ANGLE_MIN
	sweep_direction = 1  # +1 moving toward ANGLE_MAX, -1 moving toward ANGLE_MIN
	previous_sweep_obstacle_polar_coordinates = (None, None)
		# (r, \theta); used for interpolation
	
	while not stop_event.is_set():
		servo.set_servo_pwm('0', int(angle))
		time.sleep(POSE_SETTLE_SEC)
		
		distance = ultrasonic.get_distance()
		current_sweep_obstacle_polar_coordinates = (distance, angle)
		# interpolate onto map and paint
		
		time.sleep(SWEEP_DWELL_SEC)

		angle += sweep_direction * SWEEP_STEP
		if angle >= ANGLE_MAX:
			angle = ANGLE_MAX
			sweep_direction = -1
		elif angle <= ANGLE_MIN:
			angle = ANGLE_MIN
			sweep_direction = 1
	print("[INFO] Servo sweep thread stopping...")

def scan_surroundings():
	'''
	
	w/ Minqiang: need to agree on standards to represent map values, e.g.:
		- empty space = 0; impassable_obstacle = 1
		- stop_sign ("proceed w/ caution space") = 2?
	'''
	pass;

def generate_a_star_map():
	'''
	
	'''
	pass;

def a_star_on_local_map(vector_to_destination, local_map):
	'''
	Assumes that the destination is recheable.

	Insert test cases. To test this, the current idea is to return an integer/enum to 
	indicate the direction the computer intends to go.
	'''
	delta_x, delta_y = vector_to_destination


	pass;

def self_driving(can_distinguish_obstalces = False, )


def main():
	stop_event = threading.Event()
    thread_sweep_and_range = threading.Thread(target=servo_sweep_and_range_worker, args=(ultrasonic, servomotor, vision_window, stop_event), daemon=True)
    

if __name__ == "__main__":
	import doctest
	doctest.testmod()