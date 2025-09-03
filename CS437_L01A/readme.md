Collaborators: Minqiang Liu (mliu110), Yi Zhang (yjzhang2)

# Deliverables and Locations
|Deliverable ##|Deliverable|Directory / File / Link|
|-|-|-|
|01|Lab Report 01A Writeup|https://docs.google.com/document/d/1ofo3UBKZBPJ1nXjpC4MVrXOk0mxkwSKT93FRr8TGrU0|
|02|Lab Report 01A Video||
|03|||
|04|||

# Target Deadlines
|##|Task|Target Deadline|Completion Date|
|-|-|-|-|
|01|Setup Group/First Group Meeting||20250901|
|02|Lab 1A Part 2 Deliverable (PCB Sketch)|20250903||
|03|Finish Building rPi Car|||
|04|Finish Setting up rPi Car|||
|05|Finish Lab 1A Spec Codebase|||
|06|Finish Lab 1A Video Deliverable|||
|07|Finish Lab 1A Writeup|||

# notes
- fixed author settings test
- pcb todo:
	- [ ] fix female header pin bottom mount polarity
	- [ ] expand shield to accomodate battery; motor out
	- [ ] modul-ize 30mm fan graphic
- deliverable 2 bom dump
	- [x] 18650 battery holder (extend the shield): C20606804 Unecesary
	- [x] fan fun male header pin (1x2,R): C706865
	- [ ] female header pin (2x20): C25503128
		- **Need to fix bottom layer mirror**
	- [x] **grayscale module, (sense module see FreeNove pins: [23][15][14][5V0][GND])** (1x5), 1: C3008575 (has model)/C41361828
	- [x] **dummy motor output pins, pretend SDA/SCL/VCC/GND** (1x4), 4: C3008582 (has model) /C41361827
	- [x] photointerruptor: C7433015
		- datasheet: https://www.lcsc.com/datasheet/C7433015.pdf
		- forward voltage: 1.2-1.5 @ 20mA
			- supply voltage = 5v => R>(5-1.2)/20E-3 = 190; use 220O (std resistor; 20 mA => (220*20E-3^2)=88 mW => 1/ 8W (125 mW) resistor => 0603 resistor?
			- use C22962 (100 mW 0603)
		- writeup design note: pulldown resistor for stable `LOW`
