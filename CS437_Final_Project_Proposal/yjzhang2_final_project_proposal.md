# Overview
- 3 Parts:
	1. Official CS437 ARM Clone of Freenove/Sunfounder Car Kit (board design ~30-40)
		* Board (Freenove): is the chassis 
		* Board (Sunfounder): is a shield for rPi (make it compatible for BananaPi F3; assume input max is 15V0)
			* dpdt between 5V and 12V selection (parallelize/serialize battery conn & either 12V0 buck or 5V0 buck converter)?
		+ ideas: red_led + yellow_led + white_led for indicators
		+ breakout for unused pins
	2. Single Ultrasonic Transducer: ~25 hours (design, debugging, library coding)
		+ avoid that advanced mapping headache with swiveling head T_T
		+ realistic (3 front sensors)
		+ self-parking opportunity (3+3+2+2): (3 sensors for front/back; 2 sensors for fender sides)
		- a bit pricier: duplicate BOM for each ultrasonic transducer
	3. 3d-printed chassis prototype + misc mechanical supports: ~10-20 hours
		* deliverable: obj/stl file
	* Time thus far: ~65-85
	4. **BONUS**: Attempt at {"Park Assist", "Autopark", "Summon (reverse from parking spot)"} (constriction is about the size of the car): MAX 15-35 hours
		- maybe a lab instruction write up.
		- this is difficult: haven't done it before
		- camera tries to align with line.
		- dual camera (front and back line within margin)
			- need hacky freenove camera mount for reverse rPi 5 camera
	5. **BONUS**: Develop a robust library ()	
- Summary:
	- Compatibility with Raspberry Pi 5 (ARM), Orange Pi RV (RISC-V), MangoPi (RISC-V): Note their pin layouts are the same
	- 

# Notes & Dump
- Note: Each person in a group is expected to spend [50, 100] hours on this project
	- 1 person: 50 - 100 hours
	- 2 people: 100 - 200 hours
- Proposal Guidelines
- Typical Driver field of vision angle: [140, 170) degrees
- Sunfounder Pi-CarX
	- https://www.cnx-software.com/2024/01/11/sunfounder-picar-x-2-0-review-raspberry-pi-4-ai-robot-car-bloc
	- [figure out how to turn the car](https://www.cnx-software.com/wp-content/uploads/2024/01/SunFounder-PICAR-X-V2.0-Part-Kit.png)
- How Car Ultrasonic Sensors ignore a protective cover:
	- Ultrasonic Sensors have a minimum distance that is "ignored" (**Blanking Distance**)
	- **Signal Processing**: ignore extremely short distance readings
	- Material: should not be acoustically absorbent
- Integrated car dashcam (collision detection when the accelerometer detect a jolt & the car computer does not expect an acceleration)
- Minimum RAM Specs
	- [4 GB](https://campuswire.com/c/G39E9AC50/feed/19)
	- [4/8 GB](https://campuswire.com/c/G39E9AC50/feed/52)
	- Alternatives
		- [Orange Pi Zero 3](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-Zero-3.html)
			- [Orange Pi Zero 3 4GB @ 35.99](https://www.amazon.com/Orange-Pi-Allwinner-Quad-Core-Development/dp/B0CB19KD5S)
		- [Orange Pi Zero 2W (**ARM**)](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-Zero-2W.html)
			- [Orange Pi Zero 2W 4GB @ 33.99](https://www.amazon.com/Orange-Pi-Zero-2W-Development/dp/B0CHMHZKKR)
		- [Orange Pi 3B (ARM)](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-3B.html)
			- [Orange Pi 3B 4GB @ 46.99](https://www.amazon.com/Orange-Pi-Frequency-Bluetooth-OpenHarmony/dp/B0CDP6R2XR/)
			- [Orange Pi 3B 8GB @ 63.99](https://www.amazon.com/Orange-Pi-Frequency-Bluetooth-OpenHarmony/dp/B0CDP6R2XR/)
		- [Orange Pi 4A (ARM w/ RISC-V coprocessor)](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-4A.html)
			- [Orange Pi 4A 4GB @ 52.99](https://www.amazon.com/Orange-Pi-Allwinner-Co-Processor-Frequency/dp/B0DMZCDJ26)
		- [Orange Pi RV (**RISC-V**)](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-RV.html)
			- [Orange Pi RV 4GB @ 52.99](https://www.amazon.com/Orange-Pi-2GB-Processor-Development/dp/B0DK7F2M65/)
			- [Orange Pi RV 8GB @ 63.99](https://www.amazon.com/Orange-Pi-2GB-Processor-Development/dp/B0DK7F2M65/)
		- [Orange Pi AIPro (20T) (ARM)](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-AIpro(20t).html)
		- [Orange Pi RV2 (**RISC-V**)](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-RV2.html)
			- Pluses: 2 cameras & 8 GB is cheaper than rPi 8 GB
			- Issue: Odd topology
			- [Orange Pi RV2 8GB @ 63.99](https://www.amazon.com/Orange-Pi-RV2-Development-Ubuntu24-04/dp/B0DZ6VWRSZ/)

- [RPi 5 Price Points](https://www.tomshardware.com/raspberry-pi/raspberry-pi-5-16gb-review): 4 GB: 60; 8 GB: 80; 16 GB: 120
