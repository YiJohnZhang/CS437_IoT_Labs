'''
Yi John Zhang
freenove_drive
20250907

A library that presents an additional abstraction layer so the API for controlling 
the drive functions for the Freenove FNK0043 is easier.
Current dependency fetching calls for placing this at 
`.../Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server/`.

motor doc notes: self.pwm = PCA9685; # PCA9685 operates on [0, 4095] ticks
self.pwm.set_motor_pwm(channel[, on_duty]) => (channel = motor sel; 
set_motor_model(self, front_left_wheel, rear_left_wheel, f_right_wheel, r_r_whel)
'''
import time;
from enum import Enum;
from motor import Ordinary_Car;

class Vehicle_Direction(Enum):
	STOP = "stopping"
	FORWARD = "moving forward"
	BACKWARD = "moving back"
	LEFT = "turning left"
	RIGHT = "turnight right"

def drive_car_intermittently(vehicle_direction: Vehicle_Direction, speed: int = 2000, 
			  motor_on_time: float = 1, does_resource_automatically_free: bool = True, 
			  is_debug_mode: bool = False, is_vehicle_reversed: bool = False) -> None:
	'''
	Generic car drive method. Currently it is coupled to the freenove library.
	Usage: drive_car(vehicle_direction[, speed = 2000, motor_on_time = 1])
	Advanced Usage: drive_car(vehicle_direction[, speed = 2000, motor_on_time = 1, 
		does_resource_automatically_free=True, is_debug_mode=False, 
		is_vehicle_reversed: bool = False])

	Args:
	vehicle_direction -- the direction to move the car
	speed -- the on duty ticks count that is proportional to the speed
	motor_on_time -- the amount of time the motor stays on [s]
	is_debug_mode -- whether or not to display debug text
	does_resource_automatically_free -- whether or not the motor automatically closes
	is_vehicle_reversed -- whether or not the motors of the vehicle is consistently 
		mounted in reverse

	20250907 Todo Dump:
	 	- further abstraction is to pass in a "car object" to decouple from Freenove library
		- 2000 magic number to decouple	from PCA9685; possibly even speed; (set to float \in [0, 1])
		- refactor out `FREENOVE_CAR_MOTOR.set_motor_model(0, 0, 0, 0);` to a stop method
	'''
	if not isinstance(vehicle_direction, Vehicle_Direction):
		raise TypeError(f'drive_car()::expected `vehicle_status` to be Vehicle_Direction Enum member. Found: {type(vehicle_direction)}');
		# run-time enforcment: https://stackoverflow.com/a/35409537

	FREENOVE_CAR_MOTOR = Ordinary_Car();
	if is_debug_mode:
		print('fCar is {Vehicle_Direction.vehicle_direction}');
		# py enums are weird, is this valid code?

	if is_vehicle_reversed:
		speed *= -1;

	match vehicle_direction:
		# note py switch does not have fall-through
		case Vehicle_Direction.STOP:
			FREENOVE_CAR_MOTOR.set_motor_model(0, 0, 0, 0);
		case Vehicle_Direction.FORWARD:
			FREENOVE_CAR_MOTOR.set_motor_model(speed, speed, speed, speed);
		case Vehicle_Direction.BACKWARD:
			FREENOVE_CAR_MOTOR.set_motor_model(-speed, -speed, -speed, -speed);
		case Vehicle_Direction.LEFT:
			FREENOVE_CAR_MOTOR.set_motor_model(-speed, -speed, speed, speed);
		case Vehicle_Direction.RIGHT:
			FREENOVE_CAR_MOTOR.set_motor_model(speed, speed, -speed, -speed);

	time.sleep(motor_on_time);
		# this may cause some bugs later but I will leave it in here for sake of getting it to work

	FREENOVE_CAR_MOTOR.set_motor_model(0, 0, 0, 0);
	if does_resource_automatically_free:
		FREENOVE_CAR_MOTOR.close();

'''
[Freenove Motor Test Script](https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/blob/master/Code/Server/motor.py)

def test_Motor(): 
    import time
    from motor import Ordinary_Car  
    PWM = Ordinary_Car()    
    try:
        PWM.set_motor_model(1000,1000,1000,1000)         #Forward
        print ("The car is moving forward")
        time.sleep(1)
        PWM.set_motor_model(-1000,-1000,-1000,-1000)     #Back
        print ("The car is going backwards")
        time.sleep(1)
        PWM.set_motor_model(-1500,-1500,2000,2000)       #Turn left
        print ("The car is turning left")
        time.sleep(1)
        PWM.set_motor_model(2000,2000,-1500,-1500)       #Turn right 
        print ("The car is turning right")  
        time.sleep(1)
        PWM.set_motor_model(0,0,0,0)                     #Stop
        print ("\nEnd of program")
    except KeyboardInterrupt:
        print ("\nEnd of program")
    finally:
        PWM.close() # Close the PWM instance
'''