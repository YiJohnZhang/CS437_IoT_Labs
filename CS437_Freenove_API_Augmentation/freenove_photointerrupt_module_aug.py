'''
Yi John Zhang
freenove_photointerrupt_module.py
20250907

A library that presents an additional abstraction layer so the API for interpreting 
the servomotor functions for the Freenove FNK0043 is easier.

Current dependency fetching calls for placing this at 
`.../Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server/`.

note to self: try out the infrared main fn.
'''
import time
from enum import Enum;
from typing import List;
from infrared import Infrared;

def init_photointerrupt_module() -> Infrared:
	FREENOVE_PHOTO_MODULE = Infrared();
	return FREENOVE_PHOTO_MODULE;

def interpret_infrared_readings_unicast(photointerrupt_module: Infrared, servomotor_channel: int, 
										 servomotor_type: Servomotor_Type) -> (List[int], str):
	'''
	Generic infrared reading method reset method. Currently it is coupled to the 
	freenove library. Returns 1x3 vec of ints (either `0` or `1`).
	Doesn't do it all at once, akin to "unicast" routing methodology
	Usage: interpret_infrared_readings(servomotor_channel, servomotor_type)

	left/middle/right

	20250907 note: not exactly sure what "read_all_infrared" does (to test, is this the broadcast equivalent or someth)
	https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/blob/master/Code/Server/infrared.py

	20250907 Todo Dump:
	 	- decouple from Freenove library
		- standalone read loop? uses code from Freenove [test.py](https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/blob/master/Code/Server/test.py)
	'''
	return_vector = [0, 0, 0];
	return_detected_position = "left"

	return_vector[0] = photointerrupt_module.read_one_infrared(1);
	return_vector[1] = photointerrupt_module.read_one_infrared(1);
	return_vector[2] = photointerrupt_module.read_one_infrared(1);

	return (return_vector, return_detected_position);

def free_infrared_module(photointerrupt_module: Infrared) -> None:
	photointerrupt_module.close();