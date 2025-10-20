/*	Minqiang Liu (mliu110), Yi Zhang (yjzhang2)
 *	index.js
 *	20251014
 *	Significant refactoring from initial `index.js` so that the codebase is
 *	more friendly to toggle between two potential communication methods.
 */

const net = require('net');
const assert = require('assert');
// const bt = require('bluetooth-serial-port');	// for bluetooth

//	-------------------- GLOBAL STATE & CONFIG VARIABLES
//	==================== Connection Configuration
const CONNECTION_TYPE = "ip";
const SERVER_ADDR = "192.168.0.42";   // Raspberry Pi IP Address
const SERVER_PORT = 5000;
const BLUETOOTH_MAC_ADDRESS = '';
// TCP port
const CONNECTION_TYPE_ENUM = new Set([
	"ip",
	"bluetooth"
]);
// -------------------- Servo Sweep State & Config
let servoAngle = 45;
let servoIncreasing = true;

//	==================== Global State
let ip_client_socket = null;
let bt_client = null;
let is_connected = false;
let data_timer_obj = null;
let servo_timer_obj = null;

let HTML_SPAN_CONNECTION, HTML_SPAN_DIRECTION;
let HTML_SPAN_OBSTACLE, HTML_SPAN_CPU_TEMPERATURE, HTML_SPAN_CPU_LOAD;

//	-------------------- NETWORK LOGIC
/**	bluetooth_connect()
 *	Method that attempts to connect by bt.
 *	Follows `bluetooth-serial-port` pkg documentation (https://www.npmjs.com/package/bluetooth-serial-port)
 *	but assumes MAC address is already known to prevent stray connection.
 *
 *	TODO: Refactor into `socket_connect()` to build a general `connect()`
 *	method; IDEA: return `bt_client` that is returned by `bluetooth_connect()`/
 *	`socket_connect()` afterwards.
 *	TODO: figure out an `async` friendly library to prevent callback hell within
 *	`findSerialPortChannel()`, etc.
 *	ALT BT BY ELECTRONJS IDEA: https://www.electronjs.org/docs/latest/tutorial/devices
 *
 *	@param {String} target_mac_address - Device MAC address string
 *	@param {int} target_channel - Device channel; OPTIONAL
 *	@returns {null}
 */
function bluetooth_connect(target_mac_address, target_channel) {
	bt_client = new bt.BluetoothSerialPort();
	// https://www.npmjs.com/package/bluetooth-serial-port

	bt_client.findSerialPortChannel(target_mac_address, (channel) => {
		// directly connect, skip the `find` (.on found evt) sequence

		bt_client.connect(target_mac_address, channel, () => {
			is_connected = true;
			HTML_SPAN_CONNECTION.innerHTML = `Connected to ${target_mac_address}::${channel}`;

			bt_client.on('data', (buffer) => {
				const msg = buffer.toString().trim();

				// NOTE: a cc of `socket_connect()` `on('data')` evt 
				try {
					if (msg.startsWith("CMD_MODE_D")) {
						const distance = parseFloat(msg.split("#")[2]);
						if (!isNaN(distance)) {
							HTML_SPAN_OBSTACLE.textContent = distance.toFixed(2);
						}
					} else if (msg.startsWith("CMD_MODE_T")) {
						const cpu_temperature = parseFloat(msg.split('#')[1]);
						HTML_SPAN_CPU_TEMPERATURE.textContent = cpu_temperature.toFixed(2);
					} else if (msg.startsWith("CMD_MODE_C")) {
						const cpu_load = parseFloat(msg.split('#')[1]);
						HTML_SPAN_CPU_LOAD.textContent = cpu_load.toFixed(1);
					}
				} catch (err) {
					console.warn("⚠️ Failed to parse message:", msg);
				}
			});
		}, (err) => {
			teardown();
			HTML_SPAN_CONNECTION.textContent = "Connection failed: " + err.message;
		});

		bt_client.close(() => {
			teardown();
			HTML_SPAN_CONNECTION.textContent = "Disconnected";
		});
	});

	// bt_client.inquire();
}

/**	socket_connect()
 *	Method provided in starter code and expanded.
 *	Attempts to connect to the server at the given ip_address::port
 *	Handles `client_socket` lifecycle. 
 * 
 *	@param {String} target_ip_address - Server IP address string
 *	@param {int} target_port - Server Port ##
 *	@returns {null}
 */
function socket_connect(target_ip_address, target_port) {
	ip_client_socket = new net.Socket();

	ip_client_socket.connect(target_port, target_ip_address, () => {
		is_connected = true;
		HTML_SPAN_CONNECTION.innerHTML = "Connected to " + target_ip_address;
		startAutoUpdate();
		startServoSweep();
	});

	ip_client_socket.on('data', (data) => {
		const msg = data.toString().trim();
		try {
			if (msg.startsWith("CMD_MODE")) {
				const distance = parseFloat(msg.split("#")[2]);
				if (!isNaN(distance)) HTML_SPAN_OBSTACLE.textContent = distance.toFixed(2);
			} else if (msg.startsWith("CMD_TEMPERATURE")) {
				const temperature = parseFloat(msg.split("#")[1]);
				if (!isNaN(temperature)) HTML_SPAN_CPU_TEMPERATURE.textContent = temperature.toFixed(2);
			} else if (msg.startsWith("CMD_CPU_LOAD")) {
				const cpuLoad = parseFloat(msg.split("#")[1]);
				if (!isNaN(cpuLoad)) HTML_SPAN_CPU_LOAD.textContent = cpuLoad.toFixed(2);
			}
		} catch (err) {
			console.warn("⚠️ Failed to parse message:", msg);
		}
	});

	ip_client_socket.on('error', (err) => {
		is_connected = false;
		HTML_SPAN_CONNECTION.textContent = "Connection failed: " + err.message;
		teardown();
	});

	ip_client_socket.on('close', () => {
		is_connected = false;
		HTML_SPAN_CONNECTION.textContent = "Disconnected";
		teardown();
	});
}

/**	send_data()
 *	Sends command to `client_socket` (BT?/TCP Server)
 * 
 *	@param {string} cmd 
 *	@returns {null}
 */
function send_data(cmd) {
	if (is_connected && ip_client_socket && !ip_client_socket.destroyed) {
		ip_client_socket.write(cmd + "\r\n", "utf-8");
	} else if (is_connected && bt_client) {
		bt_client.write(
			Buffer.from(() => {

			}, 'utf-8'), (err, bytes_written) => {
				if (err) console.err(err);
			}
		);
			// following `bluetooth-serial-port` documentation
	} else {
		HTML_SPAN_CONNECTION.textContent = "Not connected";
	}
}

/**	update_data()
 *	Manual message to rPi (provided).
 *
 *	@returns {null}
 */
 function update_data() {
	const msg = document.getElementById("message").value.trim();
	if (msg) send_data(msg);
}

// -------------------- Auto updates --------------------
function startAutoUpdate() {
	if (data_timer_obj) clearInterval(data_timer_obj);
	data_timer_obj = setInterval(() => {
		if (is_connected) {
			send_data("CMD_TEMPERATURE");
			send_data("CMD_CPU_LOAD");
		}
	}, 2000);
}

function startServoSweep() {
	if (servo_timer_obj) clearInterval(servo_timer_obj);
	servo_timer_obj = setInterval(() => {
		if (!is_connected) return;

		send_data(`CMD_SERVO#0#${servoAngle}`);
		send_data("CMD_SONIC");

		// Move servo angle up or down
		if (servoIncreasing) {
			servoAngle += 5;
			if (servoAngle >= 65) servoIncreasing = false;
		} else {
			servoAngle -= 5;
			if (servoAngle <= 45) servoIncreasing = true;
		}
	}, 1000);
}

function stopAutoUpdate() {
	if (data_timer_obj) {
		clearInterval(data_timer_obj);
		data_timer_obj = null;
	}
}

function stopServoSweep() {
	if (servo_timer_obj) {
		clearInterval(servo_timer_obj);
		servo_timer_obj = null;
	}
}

// -------------------- DOM INTERRUPT EVENTS
/**	updateKey(e)
 *	Event handler when a key is pressed.
 *
 *	@param {event} e - js event object
 *	@returns {null}
 */
function updateKey(e) {
	e = e || window.event;
	const key = e.keyCode;
	let command = "";

	switch (key) {
		case 87: // W - Forward
			document.getElementById("upArrow").style.color = "green";
			command = "CMD_M_MOTOR#0#800#0#0";
			HTML_SPAN_DIRECTION.textContent = "Forward";
			break;
		case 83: // S - Backward
			document.getElementById("downArrow").style.color = "green";
			command = "CMD_M_MOTOR#180#800#0#0";
			HTML_SPAN_DIRECTION.textContent = "Backward";
			break;
		case 65: // A - Left
			document.getElementById("leftArrow").style.color = "green";
			command = "CMD_M_MOTOR#0#0#90#800";
			HTML_SPAN_DIRECTION.textContent = "Left";
			break;
		case 68: // D - Right
			document.getElementById("rightArrow").style.color = "green";
			command = "CMD_M_MOTOR#0#0#-90#800";
			HTML_SPAN_DIRECTION.textContent = "Right";
			break;
	}

	if (command) send_data(command);
}

/**	reset_key()
 *	Resets DOM elements on key reset. Also contains logic
 *	to stop the car.
 *
 *	@returns {null}
 */
function resetKey() {
	["upArrow", "downArrow", "leftArrow", "rightArrow"].forEach(id => {
		document.getElementById(id).style.color = "grey";
	});

	HTML_SPAN_DIRECTION.textContent = "Stopped";
	send_data("CMD_M_MOTOR#0#0#0#0");
}

// -------------------- DOM LIFECYCLE EVENTS
/**	teardown()
 *	Teardown. Clears any timer objects and closes TCP client.
 *	
 *	@returns {null}
 */
 function teardown(){
	
	stopAutoUpdate();
	stopServoSweep();

	try {
		if (ip_client_socket) {
			ip_client_socket.destroy();
			ip_client_socket = null;
			is_connected = false;
			HTML_SPAN_CONNECTION.textContent = "Connection closed";
		}
	} catch (e) {
		console.error("Error closing TCP client:", e);
	}
}

window.onload = () => {
	HTML_SPAN_CONNECTION = document.getElementById("connection");
	HTML_SPAN_DIRECTION = document.getElementById("direction");
	HTML_SPAN_OBSTACLE = document.getElementById("obstacle_distance");
	HTML_SPAN_CPU_TEMPERATURE = document.getElementById("cpu_temperature");
	HTML_SPAN_CPU_LOAD = document.getElementById("cpu_load");

	assert.ok(CONNECTION_TYPE_ENUM.has(CONNECTION_TYPE), `window.onload()::\"${CONNECTION_TYPE}\" is an invalid connection type`);
	(CONNECTION_TYPE == "ip") ? socket_connect(SERVER_ADDR, SERVER_PORT) : bluetooth_connect(BLUETOOTH_MAC_ADDRESS);

	document.onkeydown = updateKey;
	document.onkeyup = resetKey;
};

window.onbeforeunload = () => {
	teardown();
};
