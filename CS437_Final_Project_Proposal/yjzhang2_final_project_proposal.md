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
- Additional 

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