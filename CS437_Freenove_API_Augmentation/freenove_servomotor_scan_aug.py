'''
Yi John Zhang
freenove_servomotor_scan
20250907

A library that presents an additional abstraction layer so the API for controlling 
the servomotor functions for the Freenove FNK0043 is easier.

Current dependency fetching calls for placing this at 
`.../Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server/`.
'''
import time
from enum import Enum;
from typing import Tuple;
from servo import Servo;
FREENOVE_SERVO = Servo();

class Servomotor_Type(Enum):
	HALF_PI_SWEEP = 90
	PI_SWEEP = 180
	FULL_SWEEP = 360

class Freenove_Servo_API:
	def generic_reset_servomotor_position(self, servomotor_channel: int, 
										servomotor_type: Servomotor_Type) -> None:
		'''
		Generic servo reset method. Currently it is coupled to the freenove library.
		Usage: reset_servomotor_position(servomotor_channel, servomotor_type)

		servomotor_type -- the type of servomotor (sweep angle): 90, 180, 360

		20250907 Todo Dump:
			- decouple from Freenove library
		'''
		if not isinstance(servomotor_type, Servomotor_Type):
			raise TypeError(f'drive_car()::expected `servomotor_type` to be Servomotor_Type Enum member. Found: {type(vehicle_direction)}');

		reset_angle = 0;

		match servomotor_type:
			case Servomotor_Type.HALF_PI_SWEEP:
				reset_angle = 0;
			case Servomotor_Type.PI_SWEEP:
				reset_angle = 90;
			case Servomotor_Type.FULL_SWEEP:
				reset_angle = 0;

		FREENOVE_SERVO.set_servo_pwm(servomotor_channel, reset_angle);

	def freenove_reset_servomotor_positions(self) -> None:
		'''
		Rests both servos for camera vision module.

		20250907 Todo Dump:
			- decouple from Freenove library
		'''
		RESET_ANGLE = 90;

		FREENOVE_SERVO.set_servo_pwm('0', RESET_ANGLE);
		FREENOVE_SERVO.set_servo_pwm('1', RESET_ANGLE);

	def freenove_continuous_servomotor_sweep(self, servo_channel, angle_range: Tuple[int, int]) -> None:
		'''
		Sweeps the servo_channel between the selected camera through the given angle range.
		'''
		start_angle, end_angle = angle_range;

		# properly bound angle between [0, \pi]
		if start_angle < 0:
			start_angle = 0;
		if start_angle > 180:
			start_angle = 180;
		if end_angle < 0:
			end_angle = 0;
		if end_angle > 180:
			end_angle = 180;

		# always start sweeping fro left to right (change it later on if time)
		for servo_angle in range(start_angle, end_angle + 1, 1):
			FREENOVE_SERVO.set_servo_pwm(servo_channel, servo_angle);
		for servo_angle in range(end_angle, start_angle - 1, -1):
			FREENOVE_SERVO.set_servo_pwm(servo_channel, servo_angle);
