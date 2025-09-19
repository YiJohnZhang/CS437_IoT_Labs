'''
Yi Zhang (yjzhang2), Minqiang Liu (mliu110)

Large amount of code inherited from `UIUC_CS437_Lab01A.py`
Idea: just ignore obstacles until it is close enough
'''

import math
import time
import threading

import numpy as np

ANGLE_MIN = 25			# left bound of the small sweep
ANGLE_MAX = 65			# right bound of the small sweep
SWEEP_STEP = 9			# degrees per step

VALID_MIN_CM = 2.0			# Discard physically implausible low readings
VALID_MAX_CM = 300.0		# Discard too-far spikes
DETECTION_THRESHOLD = 100	# Discard obstalces detected at any distance further
SWEEP_DWELL_SEC = 0.20		# how long to dwell at each step (keeps sweep slow)
POSE_SETTLE_SEC = 0.08		# settle a bit after each movement

GRID_INCREMENT = 10			# grid increment
FEATHER_RADIUS = 1		# grid painting feather (to enlarge obstacles)


def generate_zeroes_grid(grid_increment: int, detection_threshold: int, offset_angle:int):
	'''
	Generates a zeroes matrix of appropriate size.
	
	args:
	grid_increment [int] - the distance each cell represents (cm)
	detection_threshold [int] - the maximum distance, detection radius (cm)
	angle_offset [int] - maximum angle offset, floor(max_sweep_angle - min_sweep_angle)/2 (deg)

	returns: [np.array] - the vision window. a rank 2 tensor, mxn, where: m = floor(detection_threshold/grid_increment); n = floor(detection_threshold*sin(offset_angle)/grid_increment)
	'''
	matrix_rows = detection_threshold / grid_increment
	offset_angle_radians = math.radians(offset_angle)
	matrix_cols = detection_threshold * math.sin(offset_angle_radians) / grid_increment

	np_matrix = np.zeros((matrix_rows, matrix_cols), detype = int)
	return np_matrix

def return_grid_position(polar_coordinates:int, grid_increment:int):
	'''
	Translates absolute measured position into the corresponding grid coordiante.

	polar_coordinates [tuple(int, int)] - the detected obstacle's position in polar coordinates; assumed neither value is None
	grid_increment [int] - the distance each cell represents (cm)
	returns [tuple(int, int)] - corresponding grid x,y coordinates
	'''
	obstacle_distance, obstacle_offset_angle = polar_coordinates

	calculated_x_position = int(obstacle_distance * math.sin(math.radians(obstacle_offset_angle)) / grid_increment)
	calculated_y_position = int(obstacle_distance * math.cos(math.radians(obstacle_offset_angle)) / grid_increment)
	
	return (calculated_x_position, calculated_y_position)
	
def return_painting_coordinates(center_coordinate, feather_radius, painting_bounds):
	'''
	Returns an array of coordinates to be painted: of spread `feather_radius` centered about `center_coordinate`, (x_center, y_center).

	Note to mliu110: feather_radius works like this
	if 0: just paint the exact point, e.g.
	0	0	0	0	0	0
	0	0	0	1	0	0
	0	0	0	0	0	0
	0	0	0	0	0	0

	if 1: expand on all sides, e.g.
	0	0	1	1	1	0
	0	0	1	1	1	0
	0	0	1	1	1	0
	0	0	0	0	0	0

	center_coordinate [tuple(int, int)] - 
	feather_radius [int] - feather radius offset
	painting_bounds [tuple(int, int, int, int)] - minimum x, maximum x, minimum y, and maximum y bounds
	returns [tuple(list[int], list[int])] - x coordinates to be painted and y coordinates to be painted
	'''
	center_x, center_y = center_coordinate
	return_x = [x_coordinate for x_coordinate in range(center_x - feather_radius, center_x + feather_radius) if ((x_coordinate >= painting_bounds[2]) and (x_coordinate <= painting_bounds[3]))]
	return_y = [y_coordinate for y_coordinate in range(center_y - feather_radius, center_y + feather_radius) if ((y_coordinate >= painting_bounds[0]) and (y_coordinate <= painting_bounds[1]))]
	return (return_x, return_y)

def paint_obstacle_on_map(vision_window, previous_polar_view, current_polar_view, painting_bounds,
						  minimum_sweep_angle: int = ANGLE_MIN, maximum_sweep_angle: int = ANGLE_MAX,
						  grid_increment: int = GRID_INCREMENT, detection_threshold: int = DETECTION_THRESHOLD, 
						  feather_radius: int = FEATHER_RADIUS):
	'''
	Paints the obstacle on the map. interpolates as necessary.

	SAMPLE vision_window
	c=0	------------------> c = vision_window.shape[1] - 1
	0	1	1	0	0	0	0
	0	1	1	0	0	0	0
	1	1	0	0	0	0	0
	1	1	0	0	0	0	0
	0	0	0	0	0	0	0
	0	0	0	0	0	0	0	r = vision_window.shape[0] - 1
			car is here

	args:
	vision_window [np.array] - current car's vision of the world
	previous_polar_view [tuple(int, int)] - obstalce detected in polar coordinates (r, theta)
	current_polar_view [tuple(int, int)] - obstalce detected in polar coordinates (r, theta)
	painting_bounds - [tuple(int, int, int, int)] - contains information about min and max shape sizes of window
	minimum_sweep_angle [int] - minimum servomotor angle position
	maximum_sweep_angle [int] - maximum servomotor angle position
	grid_increment [int] - the distance each cell represents (cm)
	detection_threshold [int] - the maximum distance, detection radius (cm)
	feather_radius [int] - feather radius offset
	returns: [np.array] - an updated vision window
	'''

	prev_obstacle_distance, prev_obstacle_offset_angle = previous_polar_view
	current_obstacle_distance, current_obstacle_offset_angle = current_polar_view

	sweep_direction = 1 if prev_obstacle_offset_angle < current_obstacle_offset_angle else -1

	if current_obstacle_distance <= detection_threshold:
		# first paint the obstacle if relevant
		current_obstacle_position = return_grid_position(current_polar_view, grid_increment)
		# anything beyond field of vision is reset to 0
		if (sweep_direction == 1) and (current_obstacle_offset_angle == maximum_sweep_angle):
			pass
		elif (sweep_direction == -1) and (current_obstacle_offset_angle == minimum_sweep_angle):
			# sweep_direction == -1
			pass

		# change appropriate 0s to 1s
		painted_x_coordinates, painted_y_coordinates = return_painting_coordinates(current_obstacle_position, feather_radius, painting_bounds)
		vision_window[painted_x_coordinates, painted_y_coordinates] = 1

		if (prev_obstacle_distance is not None) and (prev_obstacle_distance <= detection_threshold):
			prev_obstacle_position = return_grid_position(prev_obstacle_distance, prev_obstacle_offset_angle, grid_increment)
			# do some interpolation
			pass

	return vision_window

def servo_sweep_and_range_worker(ultrasonic_obj: Ultrasonic, servomotor_obj: Servo, stop_event: threading.Event, vision_window,
								 minimum_sweep_angle: int = ANGLE_MIN, maximum_sweep_angle: int = ANGLE_MAX,
								 grid_increment: int = GRID_INCREMENT, detection_threshold: int = DETECTION_THRESHOLD,
								 feather_radius: int = FEATHER_RADIUS):
	'''
	
	args:
	ultrasonic_obj [Ultrasonic] - ultrasonic object
	servomotor_obj [Ultrasonic] - servomotor object
	stop_event [threading.Event] - blocks this function from executing when `True`
	vision_window [np.array] - current car's vision of the world. SHARED BETWEEN THREADS
	minimum_sweep_angle [int] - minimum servomotor angle position
	maximum_sweep_angle [int] - maximum servomotor angle position
	grid_increment [int] - the distance each cell represents (cm)
	detection_threshold [int] - the maximum distance, detection radius (cm)
	feather_radius [int] - feather radius offset
	'''
	print("[INFO] servo sweep thread started ({}°..{}°).".format(minimum_sweep_angle, maximum_sweep_angle))
	
	sweep_angle_from_center = math.floor(maximum_sweep_angle - minimum_sweep_angle) / 2
	center_sweep_angle = maximum_sweep_angle - sweep_angle_from_center
	vision_window = generate_zeroes_grid(grid_increment, detection_threshold, sweep_angle_from_center)
	print(f'[INFO] initial view: {vision_window}')
	painting_bounds = (0, vision_window.shape[0] - 1, 0, vision_window.shape[1] - 1)
		# (min row=furthest from car, max row=closest to car, min col, max col)

	angle = minimum_sweep_angle
		# assumes initial sweep direction == 1
	previous_polar_view = (None, None)
		# (r, \theta); used for interpolation
	
	while not stop_event.is_set():
		servomotor_obj.set_servo_pwm('0', int(angle))
		time.sleep(POSE_SETTLE_SEC)
		
		distance = ultrasonic_obj.get_distance()
		current_polar_view = (distance, angle - center_sweep_angle)

		# interpolate onto map and paint
		vision_window = paint_obstacle_on_map(vision_window, previous_polar_view, current_polar_view, painting_bounds,
										minimum_sweep_angle, maximum_sweep_angle, grid_increment,
										detection_threshold, feather_radius)
		
		print(f'[INFO] current view: {vision_window}')
		previous_polar_view = current_polar_view

		angle += sweep_direction * SWEEP_STEP
		if angle >= ANGLE_MAX:
			angle = ANGLE_MAX
			sweep_direction = -1
		elif angle <= ANGLE_MIN:
			angle = ANGLE_MIN
			sweep_direction = 1

		time.sleep(SWEEP_DWELL_SEC)

	print("[INFO] Servo sweep thread stopping...")



'''
todo:
unpaint sweep back
unpain

install camera on rpi3b+
instal numpy on rpi3b+
test code works

'''