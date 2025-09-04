Collaborators: Minqiang Liu (mliu110), Yi Zhang (yjzhang2)

# Deliverables and Locations
|Deliverable ##|Deliverable|Directory / File / Link|
|-|-|-|
|01a|Lab Report 01A Writeup|https://docs.google.com/document/d/1ofo3UBKZBPJ1nXjpC4MVrXOk0mxkwSKT93FRr8TGrU0|
|01b|PCB Images (Schematic; Gerber=F/B Cu,F/B Silkscreen,F/B Silkscreen;Cut,Drill) (no adhesive/paste); ||
|02|Lab Report 01A Video||
|03|||
|04|||

# Target Deadlines
|##|Task|Target Deadline|Completion Date|
|-|-|-|-|
|01|Setup Group/First Group Meeting||20250901|
|02|Lab 1A Part 2 Deliverable (PCB Sketch)|20250903|20250903|
|03|Finish Building rPi Car|||
|04|Finish Setting up rPi Car|||
|05|Finish Lab 1A Spec Codebase|||
|06|Finish Lab 1A Video Deliverable|||
|07|Finish Lab 1A Writeup|||

# notes dump
- lab01a.02
	- [x] include bom
	- [x] include gerber
	- [x] schematic img
	- [x] 3d img (w/ rPi)
	- [x] 3d img expanded (w/out rPi but w/ fan)

# writeup notes
- design assumptions:
	1. an appropriate battery holder
		- 2x 18650 Battery holder connected in series to supply  a nominal voltage of 7V4.
		- note Assignment specifications did not require to implement a voltage converter for 5V0 net (I would have chosen a buck converter for ~90%+ eff.).
	2. motors
		- Used a connector b/c assumed its connects to motor breakout boards that takes I2C control input, 7V4 (VBAT), and GND to  actuate the motor. (avoid dealing with motor control ICs and assoc. passives)
		- i implemented a 2WD because [ta said 2WD okay](https://campuswire.com/c/G39E9AC50/feed/40)
	3. Greyscale Module Conn = A connector connecting to FreeNove/Sunfounder 3-Ch Greyscale breakout board. this takes one input for e/ grayscale scale channel (photointerruptor) and 5V0+GND power.
	4. Photinterutpor = No specific photointerruptor mentioned in the assignment specification;
		- assumes the photointerruptor is  always on.
		- datasheet: https://www.lcsc.com/datasheet/C42422350.pdf
		- forward voltage: 1.2-1.6 @ 20mA
			- supply voltage = 5v => R>(5-1.2)/20E-3 = 190; use 220O (std resistor; 20 mA => (220*20E-3^2)=88 mW => 1/ 8W (125 mW) resistor => 0603 resistor?
			- use C22962 (100 mW 0603)
		- writeup design note: pulldown resistor for stable `LOW`
	5. bonus 5V0 rpi fan lol
- pcb todo:
	- [x] fix female header pin bottom mount polarity
	- [x] expand shield to accomodate battery; motor out
	- [x] modul-ize 30mm fan graphic
- deliverable 2 bom dump
	- [x] 18650 battery holder (extend the shield): C20606804
	- [x] fan fun male header pin (1x2,R): C706865
	- [x] female header pin (2x20): C25503128
		- **Need to fix bottom layer mirror**
	- [x] **grayscale module, (sense module see FreeNove pins: [23][15][14][5V0][GND])** (1x5), 1: C3008575 (has model)/C41361828
	- [x] **dummy motor output pins, pretend SDA/SCL/VCC/GND** (1x4), 4: C3008582 (has model) /C41361827
	- [x] photointerruptor: C7433015
		- datasheet: https://www.lcsc.com/datasheet/C7433015.pdf
		- forward voltage: 1.2-1.5 @ 20mA
			- supply voltage = 5v => R>(5-1.2)/20E-3 = 190; use 220O (std resistor; 20 mA => (220*20E-3^2)=88 mW => 1/ 8W (125 mW) resistor => 0603 resistor?
			- use C22962 (100 mW 0603)
		- writeup design note: pulldown resistor for stable `LOW`
