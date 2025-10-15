/*	Minqiang Liu (mliu110), Yi Zhang (yjzhang2)
 *	index.js
 *	20251014
 *	Significant refactoring from initial `index.js` so that the codebase is
 *	more friendly to toggle between two potential communication methods.
 */

const net = require('net');	// for TCP/IPC servers
const bt = require('bluetooth-serial-port');	// for bluetooth
	// npm i bluetooth-serial-port

const assert = require('assert');
const { FIXED_SPEED_CM_S, move_car, stop_moving } = require('./car_util.js');

//	-------------------- GLOBAL CONSTANTS & VARIABLES
//	==================== Connection Configuration
const BLUETOOTH_MAC_ADDRESS = '';
const BLUETOOTH_CHANNEL = 1;
const SERVER_ADDRESS = '192.168.0.42';	// rPi Address
const SERVER_PORT = 5000;	// default TCP Port
const CONNECTION_TYPE_ENUM = new Set([
	"ip",
	"bluetooth"
]);
const CONNECTION_TYPE = "ip";

const SENSOR_TIME_PERIOD = 1000;	// [ms]
const SENSOR_TYPE_ENUM = new Set(["ultrasonic", "temperature"]);
let SONIC_UPDATE_TIMER_OBJ = null;
let TEMPERATURE_UPDATE_TIMER_OBJ = null;
//	==================== Global State
let is_connected_flag = false;
let client_socket = null;
let elBluetooth, elDir, elSpeed, elObstacle, elTemperature;

//	-------------------- NETWORK LOGIC
/**	bt_connect()
 *	Method that attempts to connect by bt.
 *	Follows `bluetooth-serial-port` pkg documentation (https://www.npmjs.com/package/bluetooth-serial-port)
 *	but assumes MAC address is already known to prevent stray connection.
 *
 *	TODO: Refactor into `socket_connect()` to build a general `connect()`
 *	method; IDEA: return `client_obj` that is returned by `bt_connect()`/
 *	`socket_connect()` afterwards.
 *	TODO: figure out an `async` friendly library to prevent callback hell within
 *	`findSerialPortChannel()`, etc.
 *	ALT BT BY ELECTRONJS IDEA: https://www.electronjs.org/docs/latest/tutorial/devices
 *
 *	@param {String} target_mac_address - Device MAC address string
 *	@param {int} [target_channel] - Device channel; OPTIONAL
 *	@returns {null}
 */
function bt_connect(target_mac_address, target_channel) {
	client_obj = new bt.BluetoothSerialPort();
		// https://www.npmjs.com/package/bluetooth-serial-port

	client_obj.findSerialPortChannel(target_mac_address, (channel) => {
		// directly connect, skip the `find` (.on found evt) sequence

		client_obj.connect(target_mac_address, channel, () => {
			is_connected_flag = true;
			elBluetooth.innerHTML = `Connected to ${target_mac_address}::${channel}`;
			
			// send data to it by `.write()`

			client_obj.on('data', (buffer) => {
				const msg = buffer.toString().trim();
				//	...
			});


			
		}, () => {
			console.err(`Cannot connect to: ${target_mac_address}`);
		});
	});

	// client_obj.inquire();
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
	client_socket = new net.Socket();

	client_socket.connect(target_port, target_ip_address, () => {
		is_connected_flag = true;
		elBluetooth.innerHTML = `Connected to ${target_ip_address}::${target_port}`;
		SONIC_UPDATE_TIMER_OBJ = start_auto_update(SENSOR_TIME_PERIOD, "ultrasonic");
		TEMPERATURE_UPDATE_TIMER_OBJ = start_auto_update(SENSOR_TIME_PERIOD, "temperature");
	});

	client_socket.on('data', (data) => {
		const msg = data.toString().trim();
		try {
			if (msg.startsWith("CMD_MODE")) {
				const distance = parseFloat(msg.split("#")[2]);
				if (!isNaN(distance)) {
					elObstacle.textContent = distance.toFixed(2);
				}
			}
		} catch (err) {
			console.warn("⚠️ Failed to parse message:", msg);
		}
	});

	client_socket.on('error', (err) => {
		is_connected_flag = false;
		elBluetooth.textContent = "Connection failed: " + err.message;
		SONIC_UPDATE_TIMER_OBJ = stop_auto_update_timer(SONIC_UPDATE_TIMER_OBJ);
	});

	client_socket.on('close', () => {
		is_connected_flag = false;
		elBluetooth.textContent = "Disconnected";
		SONIC_UPDATE_TIMER_OBJ = stop_auto_update_timer(SONIC_UPDATE_TIMER_OBJ);
	});
}

/**	stop_TCP_client()
 *	Teardown.
 *	
 *	@returns {null}
 */
function stop_TCP_client() {
	try {
		if (client_socket) {
			client_socket.destroy();
			client_socket = null;
			is_connected_flag = false;
			elBluetooth.textContent = "Connection closed";
		}

		SONIC_UPDATE_TIMER_OBJ = stop_auto_update_timer(SONIC_UPDATE_TIMER_OBJ);
	} catch (e) {
		console.error("Error closing TCP client:", e);
	}
}

/**	send_data()
 *	Sends command to `client_socket` (BT?/TCP Server)
 * 
 *	@param {string} cmd 
 *	@returns {null}
 */
function send_data(cmd) {
	if (is_connected_flag && client_socket && !client_socket.destroyed) {
		client_socket.write(cmd + "\r\n", "utf-8");
	} else {
		elBluetooth.textContent = "Not connected";
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

// -------------------- Business Logic Events
/**	start_auto_update()
 *	Starts a timer to send a given `sensor_reading_type` request every
 *	set `ultrasonic_time_period_ms`.
 *
 *	@param {int} update_time_period_ms - the time period to send an update in [ms]
 *	@param {String} sensor_reading_type - the type of sensor reading requested
 *	@returns {null}
 */
 function start_auto_update(update_time_period_ms, sensor_reading_type) {
	assert.ok(SENSOR_TYPE_ENUM.has(sensor_reading_type), `start_auto_update()::${sensor_feedback_type} not a valid auto-update feedback datapoint`);
	
	timer_interval_obj = sensor_reading_type === 'ultrasonic' ? SONIC_UPDATE_TIMER_OBJ : TEMPERATURE_UPDATE_TIMER_OBJ;

	if (timer_interval_obj)
		clearInterval(timer_interval_obj);
	
		timer_interval_obj = setInterval(() => {
		if (is_connected_flag) {
			sensor_reading_type === 'ultrasonic' ? send_data("CMD_SONIC") : send_data("CMD_TEMPERATURE");				
		}
	}, update_time_period_ms);
}

/**	stop_auto_update_timer()
 *	Clears the selected global interval timer object.
 *
 *	@param {object} timer_obj - Sonic Timer Interval Object
 * 	@returns {null}
 */
 function stop_auto_update_timer(timer_obj) {
	if (timer_obj) {
		clearInterval(timer_obj);
		timer_obj = null;
	}

	return timer_obj;
}

// -------------------- KEYBOARD EVENTS
/**	on_key_event(evt)
 *	Event handler when a key is pressed.
 *
 *	@param {event} evt - js event object
 *	@returns {null}
 */
function on_key_event(evt) {
	evt = evt || window.event;
	const key = evt.keyCode;
	let command = "";

	if (key == 65 || key == 68 || key == 83 || key == 87){
		command = move_car(key);	
        elSpeed.textContent = FIXED_SPEED_CM_S.toFixed(2);
	}
	
	if (command)
		send_data(command);
}

/**	reset_key()
 *	Resets DOM elements on key reset. Also contains logic
 *	to stop the car.
 *
 *	@returns {null}
 */
function reset_key() {
	["upArrow", "downArrow", "leftArrow", "rightArrow"].forEach(id => {
		document.getElementById(id).style.color = "grey";
	});

	// stop the car
	elDir.textContent = "Stopped";
	elSpeed.textContent = "0.00";

	stop_moving();	// opportunity to collect distance traveled!
	send_data("CMD_M_MOTOR#0#0#0#0");
}

// -------------------- DOM LIFECYCLE
window.onload = () => {
	elBluetooth = document.getElementById("bluetooth");
	elDir = document.getElementById("direction");
	elSpeed = document.getElementById("speed");
	elObstacle = document.getElementById("obstacle_distance");
	assert.ok(CONNECTION_TYPE_ENUM.has(CONNECTION_TYPE), `window.onload()::\"${CONNECTION_TYPE}\" is an invalid connection type`);

	(CONNECTION_TYPE == "ip") ? socket_connect(SERVER_ADDRESS, SERVER_PORT) : bt_connect(BLUETOOTH_MAC_ADDRESS);
	document.onkeydown = on_key_event;
	document.onkeyup = reset_key;
};

window.onbeforeunload = () => {
	stop_TCP_client();
};
