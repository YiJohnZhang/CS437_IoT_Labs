const net = require('net');

// -------------------- Configuration --------------------
const server_addr = "192.168.0.42";   // Raspberry Pi IP Address
const server_port = 5000;             // TCP port

// -------------------- Global state --------------------
let client_socket1 = null;
let connect_Flag = false;
let sonicInterval = null;

let elBluetooth, elDir, elSpeed, elObstacle;

// -------------------- Distance Tracking --------------------
const FIXED_SPEED_CM_S = 20;
let isMoving = false;
let moveStartTime = null;
let totalDistance = 0;
let distanceTimer = null;

// -------------------- Connect to TCP Server --------------------
function socket1_connect(ip) {
    client_socket1 = new net.Socket();

    client_socket1.connect(server_port, ip, () => {
        connect_Flag = true;
        elBluetooth.innerHTML = "Connected to " + ip;
        startSonicAutoUpdate();
    });

    client_socket1.on('data', (data) => {
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

    client_socket1.on('error', (err) => {
        connect_Flag = false;
        elBluetooth.textContent = "Connection failed: " + err.message;
        stopSonicAutoUpdate();
    });

    client_socket1.on('close', () => {
        connect_Flag = false;
        elBluetooth.textContent = "Disconnected";
        stopSonicAutoUpdate();
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

// -------------------- Auto obstacle request --------------------
function startSonicAutoUpdate() {
    if (sonicInterval) clearInterval(sonicInterval);
    sonicInterval = setInterval(() => {
        if (connect_Flag) {

            sendData("CMD_SONIC");
        }
    }, 1000);
}

function stopSonicAutoUpdate() {
    if (sonicInterval) {
        clearInterval(sonicInterval);
        sonicInterval = null;
    }
}

// -------------------- Distance Tracking --------------------
function startMoving() {
    if (!isMoving) {
        isMoving = true;
        moveStartTime = Date.now();
        elSpeed.textContent = FIXED_SPEED_CM_S.toFixed(2);

        distanceTimer = setInterval(() => {
            const elapsedSec = (Date.now() - moveStartTime) / 1000;
            const newDistance = FIXED_SPEED_CM_S * elapsedSec;
        }, 500);
    }
}

function stopMoving() {
    if (isMoving) {
        const elapsedSec = (Date.now() - moveStartTime) / 1000;
        totalDistance += FIXED_SPEED_CM_S * elapsedSec;

        if (distanceTimer) clearInterval(distanceTimer);
        distanceTimer = null;
        moveStartTime = null;
        isMoving = false;
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
            startMoving();
            break;
        case 83: // S - Backward
            document.getElementById("downArrow").style.color = "green";
            command = "CMD_M_MOTOR#180#800#0#0";
            elDir.textContent = "Backward";
            startMoving();
            break;
        case 65: // A - Left
            document.getElementById("leftArrow").style.color = "green";
            command = "CMD_M_MOTOR#0#0#90#800";
            elDir.textContent = "Left";
            startMoving();
            break;
        case 68: // D - Right
            document.getElementById("rightArrow").style.color = "green";
            command = "CMD_M_MOTOR#0#0#-90#800";
            elDir.textContent = "Right";
            startMoving();
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
    elSpeed.textContent = "0.00";

    stopMoving();
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
        stopSonicAutoUpdate();
    } catch (e) {
        console.error("Error closing TCP client:", e);
    }
}

// -------------------- Lifecycle --------------------
window.onload = () => {
    elBluetooth = document.getElementById("bluetooth");
    elDir = document.getElementById("direction");
    elSpeed = document.getElementById("speed");
    elObstacle = document.getElementById("obstacle_distance");

    socket1_connect(server_addr);
    document.onkeydown = updateKey;
    document.onkeyup = resetKey;
};

window.onbeforeunload = () => {
    stopTcpClient();
};
