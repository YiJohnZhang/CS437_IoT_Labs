'''
Yi Zhang (yjzhang2), Minqiang Liu (mliu110)

Large amount of code inherited from `UIUC_CS437_Lab01A.py`
Idea: just ignore obstacles until it is close enough

Iterates on the previous implementation `.py` but significantly hardcodes it, is 
a lot more implicit and does 1-direction sweep to prevent ghosted values on the 
vision map.
'''

import math
import time
import threading
# from typing import List
import numpy as np

from ultrasonic import Ultrasonic;
from motor import Ordinary_Car;
from servo import Servo;

ANGLE_MIN = 25			# left bound of the small sweep (recommended: -30 deg from key)
ANGLE_MAX = 65			# right bound of the small sweep (recommended: +30 deg from key)
SWEEP_STEP = 5			# degrees per step (recommended: >5 deg)
KEY_ANGLE = int((ANGLE_MAX - ANGLE_MIN) / 2)
OFFSET_ANGLE = ANGLE_MAX - KEY_ANGLE

VALID_MIN_CM = 2.0			# Discard physically implausible low readings
VALID_MAX_CM = 300.0		# Discard too-far spikes
DETECTION_THRESHOLD = 100	# Discard obstalces detected at any distance further

SWEEP_DWELL_TIMEOUT_SECONDS = 0.20		# how long to dwell at each step (keeps sweep slow)
POSE_SETTLE_TIMEOUT_SECONDS = 0.08		# settle a bit after each movement

GRID_INCREMENT = 10			# grid increment
FEATHER_RADIUS = 1			# grid painting feather (to enlarge obstacles)

def generate_zeroes_grid(grid_shape: tuple):
	'''
	Generates a zeroes matrix of appropriate size.
	
	args:
	grid_shape [tuple(int,int)] - the shape of the grid

	returns: [np.array] - the vision window. a rank 2 tensor, mxn, where: m = floor(detection_threshold/grid_increment); n = floor(detection_threshold*sin(offset_angle)/grid_increment)
	'''
	np_matrix = np.zeros(grid_shape, dtype=int)
	return np_matrix

def floor_int(input_value):
	return_value = input_value
	if input_value < 0:
		return_value = int(math.ceil(input_value))
	else:
		return_value = int(math.floor(input_value))
	
	return return_value

def return_grid_position(polar_coordinates:int, grid_x_max:int, grid_increment:int = GRID_INCREMENT) -> tuple:
	'''
	Translates absolute measured position into the corresponding grid coordinates.

			CAR HERE (CENTER)
	<--left--	|		--right->
	(0,0)	---increasing x--->	 			
	0	1	1	0	0	0	0	0 	 |
	0	1	1	0	0	0	0	0	increasing y
	0	0	0	1	1	0	0	0	 |
	0	0	0	1	1	0	0	0	\|/

	polar_coordinates [tuple(int, int)] - the detected obstacle's position in polar coordinates; assumed neither value is None
	grid_increment [int] - the distance each cell represents (cm)
	grid_x_max [int] - 
	returns [tuple(int, int)] - corresponding grid x,y coordinates
	'''
	obstacle_distance, obstacle_offset_angle = polar_coordinates
	grid_x_center = int(grid_x_max / 2)

	calculated_grid_x_position = grid_x_center + floor_int(obstacle_distance * math.sin(math.radians(obstacle_offset_angle)) / grid_increment)
	calculated_grid_y_position = floor_int(obstacle_distance * math.cos(math.radians(obstacle_offset_angle)) / grid_increment)
	
	return (calculated_grid_x_position, calculated_grid_y_position)

def collect_obstacle_readings(ultrasonic_obj:Ultrasonic, servomotor_obj:Servo, grid_shape:tuple) -> list:
	obstacle_readings = []
		# list of tuples in polar coordinate (r, theta)

	for current_angle in range(ANGLE_MIN, ANGLE_MAX, SWEEP_STEP):
		servomotor_obj.set_servo_pwm('0', int(current_angle))
			# Freenove move servo API method
		
		offset_angle = current_angle - KEY_ANGLE
		measured_distance = ultrasonic_obj.get_distance()
			# Freenove ultrasonic sensor API method

		if (measured_distance > VALID_MIN_CM) and (measured_distance <= DETECTION_THRESHOLD):
			grid_position = return_grid_position((measured_distance, offset_angle), grid_shape[0], GRID_INCREMENT)
			obstacle_readings.append(grid_position)
			
		time.sleep(SWEEP_DWELL_TIMEOUT_SECONDS)
	return obstacle_readings

def paint_ones(obstacle_readings, grid_shape:tuple, feather_radius:int = FEATHER_RADIUS):
	'''
	
	'''
	vision_window = generate_zeroes_grid(grid_shape)
	print(f'[INFO] initial view: {vision_window}')
	painting_bounds = (0, grid_shape[0] - 1, 0, grid_shape[1] - 1)
	
	# calculate extra 1s to paint
	feathered_painting_list = []
	for obstacle_reading in obstacle_readings:
		center_x, center_y = obstacle_reading
		extra_x_coordinates = [x_coordinate for x_coordinate in range(center_x - feather_radius, center_x + feather_radius) if ((x_coordinate >= painting_bounds[2]) and (x_coordinate <= painting_bounds[3]) and (x_coordinate != center_x))]
		extra_y_coordinates = [y_coordinate for y_coordinate in range(center_y - feather_radius, center_y + feather_radius) if ((y_coordinate >= painting_bounds[0]) and (y_coordinate <= painting_bounds[1]) and (y_coordinate != center_y))]

		for x_coordinate in extra_x_coordinates:
			for y_coordinate in extra_y_coordinates:
				feathered_painting_list.append(x_coordinate, y_coordinate)
	
	# paint the reading 1s first
	for (coordinate_x, coordinate_y) in obstacle_readings:
		vision_window[coordinate_x, coordinate_y] = 1

	# paint the feathered 1s
	for (coordinate_x, coordinate_y) in feathered_painting_list:
		vision_window[coordinate_x, coordinate_y] = 1
	
	return vision_window

def teardown(ultrasonic_obj):
	ultrasonic_obj.close();

def main():
	ultrasonic_obj = Ultrasonic()
	servo_obj = Servo()

	# precalculated values:
	offset_angle_radians = math.radians(OFFSET_ANGLE)
	matrix_rows = int(DETECTION_THRESHOLD / GRID_INCREMENT)
	matrix_cols = int(DETECTION_THRESHOLD * math.sin(offset_angle_radians) / GRID_INCREMENT)
	grid_shape = (matrix_rows, matrix_cols)

	try:
		while True:
			collected_obstacle_readings = collect_obstacle_readings(ultrasonic_obj, servo_obj, grid_shape)
			vision_window = paint_ones(collected_obstacle_readings, grid_shape, DETECTION_THRESHOLD, FEATHER_RADIUS)
			print(vision_window)
	except KeyboardInterrupt:
		pass
	except Exception:
		pass
	finally:
		teardown()

if __name__ == "__main__":
    main()