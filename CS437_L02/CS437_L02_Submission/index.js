/*	Minqiang Liu (mliu110), Yi Zhang (yjzhang2)
 *	index.js
 *	20251014
 *	Significant refactoring from initial `index.js` so that the codebase is
 *	more friendly to toggle between two potential communication methods.
 */

const net = require('net');
const assert = require('assert');
const bt = require('bluetooth-serial-port');	// for bluetooth
const BLUETOOTH_MAC_ADDRESS = '';

// -------------------- Configuration --------------------
const server_addr = "192.168.0.42";   // Raspberry Pi IP Address
const server_port = 5000;
// TCP port
const CONNECTION_TYPE_ENUM = new Set([
    "ip",
    "bluetooth"
]);

const CONNECTION_TYPE = "ip";
// -------------------- Global state --------------------
let client_socket1 = null;
let connect_Flag = false;
let autoInterval = null;
let servoInterval = null;

let elBluetooth, elDir, elObstacle, elTemperature, elCpuLoad;

// -------------------- Servo Sweep State --------------------
let servoAngle = 45;
let servoIncreasing = true;

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
 *	@param {int} target_channel - Device channel; OPTIONAL
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
            client_obj.write(
                Buffer.from(() => {

                }, 'utf-8'), (err, bytes_written) => {
                    if (err) console.err(err);
                }
            );

            client_obj.on('data', (buffer) => {
                const msg = buffer.toString().trim();

                // NOTE: a cc of `socket_connect()` `on('data')` evt 
                try {
                    if (msg.startsWith("CMD_MODE_D")) {
                        const distance = parseFloat(msg.split("#")[2]);
                        if (!isNaN(distance)) {
                            elObstacle.textContent = distance.toFixed(2);
                        }
                    } else if (msg.startsWith("CMD_MODE_T")) {
                        const cpu_temperature = parseFloat(msg.split('#')[1]);
                        elTemperature.textContent = cpu_temperature.toFixed(2);
                    } else if (msg.startsWith("CMD_MODE_C")) {
                        const cpu_load = parseFloat(msg.split('#')[1]);
                        elCPULoad.textContent = cpu_load.toFixed(1);
                    }
                } catch (err) {
                    console.warn("⚠️ Failed to parse message:", msg);
                }
            });
        }, (err) => {
            teardown();
            elBluetooth.textContent = "Connection failed: " + err.message;
        });

        client_obj.close(() => {
            teardown();
            elBluetooth.textContent = "Disconnected";
        });
    });

    // client_obj.inquire();
}

// -------------------- Connect to TCP Server --------------------
function socket1_connect(ip) {
    client_socket1 = new net.Socket();

    client_socket1.connect(server_port, ip, () => {
        connect_Flag = true;
        elBluetooth.innerHTML = "Connected to " + ip;
        startAutoUpdate();
        startServoSweep();
    });

    client_socket1.on('data', (data) => {
        const msg = data.toString().trim();
        try {
            if (msg.startsWith("CMD_MODE")) {
                const distance = parseFloat(msg.split("#")[2]);
                if (!isNaN(distance)) elObstacle.textContent = distance.toFixed(2);
            } else if (msg.startsWith("CMD_TEMPERATURE")) {
                const temperature = parseFloat(msg.split("#")[1]);
                if (!isNaN(temperature)) elTemperature.textContent = temperature.toFixed(2);
            } else if (msg.startsWith("CMD_CPU_LOAD")) {
                const cpuLoad = parseFloat(msg.split("#")[1]);
                if (!isNaN(cpuLoad)) elCpuLoad.textContent = cpuLoad.toFixed(2);
            }
        } catch (err) {
            console.warn("⚠️ Failed to parse message:", msg);
        }
    });

    client_socket1.on('error', (err) => {
        connect_Flag = false;
        elBluetooth.textContent = "Connection failed: " + err.message;
        stopAutoUpdate();
        stopServoSweep();
    });

    client_socket1.on('close', () => {
        connect_Flag = false;
        elBluetooth.textContent = "Disconnected";
        stopAutoUpdate();
        stopServoSweep();
    });
}

// -------------------- Send command --------------------
function sendData(cmd) {
    if (connect_Flag && client_socket1 && !client_socket1.destroyed) {
        client_socket1.write(cmd + "\r\n", "utf-8");
    } else {
        elBluetooth.textContent = "Not connected";
    }
}

// -------------------- Auto updates --------------------
function startAutoUpdate() {
    if (autoInterval) clearInterval(autoInterval);
    autoInterval = setInterval(() => {
        if (connect_Flag) {
            sendData("CMD_TEMPERATURE");
            sendData("CMD_CPU_LOAD");
        }
    }, 2000);
}

function stopAutoUpdate() {
    if (autoInterval) {
        clearInterval(autoInterval);
        autoInterval = null;
    }
}

// -------------------- Servo sweeping --------------------
function startServoSweep() {
    if (servoInterval) clearInterval(servoInterval);
    servoInterval = setInterval(() => {
        if (!connect_Flag) return;

        sendData(`CMD_SERVO#0#${servoAngle}`);
        sendData("CMD_SONIC");

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

function stopServoSweep() {
    if (servoInterval) {
        clearInterval(servoInterval);
        servoInterval = null;
    }
}

// -------------------- Keyboard control (WASD) --------------------
function updateKey(e) {
    e = e || window.event;
    const key = e.keyCode;
    let command = "";

    switch (key) {
        case 87: // W - Forward
            document.getElementById("upArrow").style.color = "green";
            command = "CMD_M_MOTOR#0#800#0#0";
            elDir.textContent = "Forward";
            break;
        case 83: // S - Backward
            document.getElementById("downArrow").style.color = "green";
            command = "CMD_M_MOTOR#180#800#0#0";
            elDir.textContent = "Backward";
            break;
        case 65: // A - Left
            document.getElementById("leftArrow").style.color = "green";
            command = "CMD_M_MOTOR#0#0#90#800";
            elDir.textContent = "Left";
            break;
        case 68: // D - Right
            document.getElementById("rightArrow").style.color = "green";
            command = "CMD_M_MOTOR#0#0#-90#800";
            elDir.textContent = "Right";
            break;
    }

    if (command) sendData(command);
}

// -------------------- Stop movement --------------------
function resetKey() {
    ["upArrow", "downArrow", "leftArrow", "rightArrow"].forEach(id => {
        document.getElementById(id).style.color = "grey";
    });

    elDir.textContent = "Stopped";
    sendData("CMD_M_MOTOR#0#0#0#0");
}

// -------------------- Manual message --------------------
function update_data() {
    const msg = document.getElementById("message").value.trim();
    if (msg) sendData(msg);
}

// -------------------- Stop TCP client --------------------
function stopTcpClient() {
    try {
        if (client_socket1) {
            client_socket1.destroy();
            client_socket1 = null;
            connect_Flag = false;
            elBluetooth.textContent = "Connection closed";
        }
        stopAutoUpdate();
        stopServoSweep();
    } catch (e) {
        console.error("Error closing TCP client:", e);
    }
}

// -------------------- Lifecycle --------------------
window.onload = () => {
    elBluetooth = document.getElementById("bluetooth");
    elDir = document.getElementById("direction");
    elObstacle = document.getElementById("obstacle_distance");
    elTemperature = document.getElementById("temperature");
    elCpuLoad = document.getElementById("cpu_load");

    assert.ok(CONNECTION_TYPE_ENUM.has(CONNECTION_TYPE), `window.onload()::\"${CONNECTION_TYPE}\" is an invalid connection type`);
    (CONNECTION_TYPE == "ip") ? socket1_connect(server_addr) : bt_connect(BLUETOOTH_MAC_ADDRESS);

    document.onkeydown = updateKey;
    document.onkeyup = resetKey;
};

window.onbeforeunload = () => {
    stopTcpClient();
};
