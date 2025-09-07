'''
Yi John Zhang
cs437_l01a_compliant_obstacle_car.py
20250907

CS437 Lab 01A Compliant Obstacle Car
- [x] Car Can Move by itself
- [x] Car Can "See" (Scans)
- [x] Car Can Navigate (attempts avoiding obstalces)


U night => video recording navigating video
W, meeting => have completed the edited and voiceover video; ready for submission; also talk about the AI thing
- Advanced Mapping
- Object Deteciton
'''

import time;
from typing import List;
from ultrasonic import Ultrasonic;
from motor import Ordinary_Car;
from servo import Servo;


Z_SERVO = '0';			# XY RHR (Freenove Docs)
X_SERVO = '1';			# YZ RHR (Freenove Docs)
NO_SSH_TIMEOUT = 5;		# I couldn't setup headless connection
LIMIT_CAR_RUN = 10;		# I couldn't setup headless connection
MANUEVER_DISTANCE_THRESHOLD = 50;

class Obstacle_Car:
	def __init__(self, drive_time: int = -1, 
		servo_scan_increment: int = 60, servo_scan_mode = 'abrupt') -> None:
		'''
		Constructor

		Args:
		drive_time -- [s] Either set a drive time or let it (theoretically) drive forever 
			(-1) until a `KeyboardInterrupt` is detected
		servo_scan_increment -- [degrees] how much to adjust the ultrasonic servo position
		servo_scan_mode -- [enum] WIP feature
		'''
		print(f'Obstacle_Car()::33: ssh-less timeout time: {NO_SSH_TIMEOUT}');
		
		self.CAR_MOTOR_MODULE = Ordinary_Car();
		self.CAR_ULTRASONIC_MODULE = Ultrasonic();
		self.CAR_SERVO_MODULE = Servo();
		
		self.ultrasonic_servo_angle = 90; # magic ##!! but there isn't a pos sensor?
		self.ultrasonic_servo_scan_mode = servo_scan_mode;
		self.ultrasonic_servo_scan_increment = servo_scan_increment;
		self.next_scan_direction = 0;
		
		self.setup();
		self.CAR_SERVO_MODULE.set_servo_pwm(Z_SERVO, 90 - self.ultrasonic_servo_scan_increment);
		self.drive_time = drive_time;
		self.end_time = time.time() + self.drive_time;
		print(f'Obstacle_Car()::48: {time.time()}; added {self.drive_time}s for end_time={self.end_time}');
		return;
	
	def setup(self) -> None:
		'''
		Setup: Reset motor positions and give me enough time to put it on the test track b/c
		I can't ssh to this rPi -____-
		'''
		self.reset_motor_positions();
		time.sleep(NO_SSH_TIMEOUT);
		print('Obstacle_Car()::setup()::54: called!');
		return;

	def reset_motor_positions(self) -> None:
		'''
		Reset the motor positions.
		'''
		self.CAR_SERVO_MODULE.set_servo_pwm(Z_SERVO, 90);
		self.CAR_SERVO_MODULE.set_servo_pwm(X_SERVO, 90);
		self.CAR_MOTOR_MODULE.set_motor_model(0, 0, 0, 0);
		return;
	
	def teardown(self) -> None:
		'''
		Reset the motor position and free GPIO resources.
		'''
		self.reset_motor_positions();
		self.CAR_MOTOR_MODULE.close();
		self.CAR_ULTRASONIC_MODULE.close();
		print('Obstacle_Car::teardown()::~80: called!');
		return;
	
	def adjust_scan_angle(self, scan_direction) -> None:
		'''
		Adjusts the ultrasonic scan angle (Z-Axis) servo by [scan_direction] degrees.

		Args:
		scan_direction -- [degrees]
		'''
		if scan_direction == 1:
			self.ultrasonic_servo_angle += self.ultrasonic_servo_scan_increment;
		else:
			self.ultrasonic_servo_angle -= self.ultrasonic_servo_scan_increment;
		
		self.CAR_SERVO_MODULE.set_servo_pwm(Z_SERVO, self.ultrasonic_servo_angle);
		time.sleep(0.1);
		return;
	
	def scan_environment(self) -> List[int]:
		'''
		Returns a complete vector of the scanned threshold. 
		Note: it may better to scan just one direciton so that the care can be more responsive.
		'''
		postion_measurement = [MANUEVER_DISTANCE_THRESHOLD, MANUEVER_DISTANCE_THRESHOLD, MANUEVER_DISTANCE_THRESHOLD];
		
		if self.next_scan_direction == 1:
			# x-d, x, x+d     
			postion_measurement[0] = self.CAR_ULTRASONIC_MODULE.get_distance();
			self.adjust_scan_angle(self.next_scan_direction);
			postion_measurement[1] = self.CAR_ULTRASONIC_MODULE.get_distance();
			self.adjust_scan_angle(self.next_scan_direction);
			postion_measurement[2] = self.CAR_ULTRASONIC_MODULE.get_distance();
			
			self.next_scan_direction = -1;
		else:
			# x+d, x, x-d
			postion_measurement[2] = self.CAR_ULTRASONIC_MODULE.get_distance();
			self.adjust_scan_angle(self.next_scan_direction);
			postion_measurement[1] = self.CAR_ULTRASONIC_MODULE.get_distance();
			self.adjust_scan_angle(self.next_scan_direction);
			postion_measurement[0] = self.CAR_ULTRASONIC_MODULE.get_distance();
			
			self.next_scan_direction = 1;

		# print(f'Obstacle_Car::scan_environment(): {postion_measurement}');
		return postion_measurement;

	def drive_car(self, distance) -> None:
		'''
		Drive the car, appropriately manuever given distance measurement.
		Values here are sourced from Freenove (Manufacturer) Test Code Documentation.
		Source: https://docs.freenove.com/projects/fnk0043/en/latest/fnk0043/codes/tutorial/5_Ultrasonic_Car.html

		Args:
		distance -- the left (distance[0]), middle (distance[1]), and right (distance[2]) scanned distances
		'''
		
		if (distance[0] < 30 and distance[1] < 30 and distance[2] <30) or distance[1] < 30:
			self.CAR_MOTOR_MODULE.set_motor_model(-1450,-1450,-1450,-1450) 			
			time.sleep(0.1);
			if (distance[0] < 10 and distance[1] < 10 and distance[2] <10):
				# stop
				self.CAR_MOTOR_MODULE.set_motor_model(0, 0, 0, 0);
				# blinkers
				
			elif distance[0] < distance[2]:
				self.CAR_MOTOR_MODULE.set_motor_model(1450,1450,-1450,-1450);
			else:
				self.CAR_MOTOR_MODULE.set_motor_model(-1450,-1450,1450,1450);
		elif distance[0] < 30 and distance[1] < 30:
			self.CAR_MOTOR_MODULE.set_motor_model(1500,1500,-1500,-1500);
		elif distance[2] < 30 and distance[1] < 30:
			self.CAR_MOTOR_MODULE.set_motor_model(-1500,-1500,1500,1500);
		elif distance[0] < 20:
			self.CAR_MOTOR_MODULE.set_motor_model(2000,2000,-500,-500);
			if distance[0] < 10:
				self.CAR_MOTOR_MODULE.set_motor_model(1500,1500,-1000,-1000);
		elif distance[2] < 20:
			self.CAR_MOTOR_MODULE.set_motor_model(-500,-500,2000,2000);
			if distance[2] < 10:
				self.CAR_MOTOR_MODULE.set_motor_model(-1500,-1500,1500,1500);
		else:
			# go forward
			self.CAR_MOTOR_MODULE.set_motor_model(600, 600, 600, 600);
		
		return;

	def scan_and_drive(self) -> bool:
		continue_running = True;
		if self.drive_time >= 0 and (time.time() >= self.end_time):
			continue_running = False;
		
		# technically self.drive_car(self.scan_environment());
		postion_measurement = self.scan_environment();
		self.drive_car(postion_measurement);

		return continue_running;

def run_test_obstacle_car() -> None:
	cs437_lab01a_compliant_car = Obstacle_Car(LIMIT_CAR_RUN);
	is_running = True;

	try:
		while is_running:
			is_running = cs437_lab01a_compliant_car.scan_and_drive();
	except KeyboardInterrupt:
		pass;
	
	cs437_lab01a_compliant_car.teardown();
	return;

if __name__ == '__main__':
	'''
	main()
	'''
	run_test_obstacle_car();