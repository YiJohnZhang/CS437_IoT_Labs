/*	Minqiang Liu (mliu110), Yi Zhang (yjzhang2)
 *	car_util.js	
 *	20251014	
 *	Car utility methods.
 */

 //	==================== Speed Settings Configuration
const MAXIMUM_SPEED = 800;
const STALL_SPEED = 0;

// ==================== Distance Tracking Constants
const FIXED_SPEED_CM_S = 20;
let is_moving = false;
let move_start_time = null;
let total_distance_traveled = 0;
let distance_timer_obj = null;

// -------------------- Movement
/**	move_car()
 *	Moves the car if `key_value` corresponds to either `W`, `A`, `S`, 
 *	or `D` and moves the car appropriately
 * 
 *	@param {int} key_value - ASCII key value
 *	@returns {string} - command string
 */
 function move_car(key_value) {
	let forward_direction_angle = 0;
	let forward_speed = 0;
	let turn_angle = 0;
	let turn_speed = 0;

	switch (key_value) {
		case 87: // W - Forward
			document.getElementById("upArrow").style.color = "green";
			forward_direction_angle = 0;
			forward_speed = MAXIMUM_SPEED;
			turn_angle = 0;
			turn_speed = STALL_SPEED;

			elDir.textContent = "Forward";
			break;
		case 83: // S - Backward
			document.getElementById("downArrow").style.color = "green";
			forward_direction_angle = 180;
			forward_speed = MAXIMUM_SPEED;
			turn_angle = 0;
			turn_speed = STALL_SPEED;

			elDir.textContent = "Backward";
			break;
		case 65: // A - Left
			document.getElementById("leftArrow").style.color = "green";
			forward_direction_angle = 0;
			forward_speed = STALL_SPEED;
			turn_angle = 90;
			turn_speed = MAXIMUM_SPEED;
			
			elDir.textContent = "Left";
			// start_moving();
			break;
		case 68: // D - Right
			document.getElementById("rightArrow").style.color = "green";
			forward_direction_angle = 0;
			forward_speed = STALL_SPEED;
			turn_angle = -90;
			turn_speed = MAXIMUM_SPEED;

			elDir.textContent = "Right";
			// start_moving();
			break;
	}

	const command = `CMD_M_MOTOR#${forward_direction_angle}#${forward_speed}#${turn_angle}#${turn_speed}`;
	start_moving();

	return command;
}

// -------------------- Distance Tracking
/**	start_moving()
 *	
 *
 *	@returns {null}
 */
function start_moving() {
	if (!is_moving) {
		is_moving = true;
		move_start_time = Date.now();
		elSpeed.textContent = FIXED_SPEED_CM_S.toFixed(2);

		distance_timer_obj = setInterval(() => {
			// const elapsedSec = (Date.now() - move_start_time) / 1000;
			// const newDistance = FIXED_SPEED_CM_S * elapsedSec;
		}, 500);
	}
}

/**	stop_moving
 *	Keeps track of the distance traveled
 *
 *	@returns {int} total distance traveled
 */
function stop_moving() {
	if (is_moving) {
		const elapsed_time_s = (Date.now() - move_start_time) / 1000;
		total_distance_traveled += FIXED_SPEED_CM_S * elapsed_time_s;

		if (distance_timer_obj) clearInterval(distance_timer_obj);
		distance_timer_obj = null;
		move_start_time = null;
		is_moving = false;
	}

	return total_distance_traveled;
}

module.exports = { FIXED_SPEED_CM_S, move_car, stop_moving }