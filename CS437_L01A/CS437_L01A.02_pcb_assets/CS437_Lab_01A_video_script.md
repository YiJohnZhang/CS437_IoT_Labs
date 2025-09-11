# video script
- based on `UIUC_CS437_Lab01A.py`
- clips
	- ref_clip: main driving clip
	- clip_2: car on cinderblock clip while "driving" on air (only needed for `scan_environment`), +/- 20 deg, 9 degree steps!
- scene 1:
	- ref_clip: 1 single clip of car driving stragiht, once it encounters a few obstacles it side tracks
- scene 2:
	- clip side-by-side with used code base to make decision
		1. (ref_clip): talk about how the car can **move by itself and navigates**
			- first, we implemented a pseudo-API to abstract the freenove movement model `motor_obj.set_motor_model()` with four PWM on tick parameters for each of the four wheels
			- these methods are: `stop` that stops the car indefinitely, `stop_hold` for a configurable amount of time, `forward_continuos` to move forward; `reverse_for` to gently reverse, `turn_left`; and `post_bypass_advance`, a short forward movement after turning
			- then in the code, we used a decision tree based on some **decision metric** to trigger a combination of these methods
		2. the **decision metric** (the car can see)
			- the decision metric is naively determined using `robust_window_stats()`, which calculates the value based on the last 3 values recorded in a `history` buffer recorded by `range_worker()`
			- `range_worker()` is a function that samples the ultrasonic distance and stores it in a `history` buffer shared with `robust_window_stats()`. it runs on a separate thread; a design feature we used to improve the car's responsivity. the sweeping is handled by another function, `servo_sweep_worker()` that runs on a separate thread: it sweeps between some preset `minimum` and `maximum angle` with a preset `angle sweep step size`.
		3. everything after `finally` is teardown code: set the `stop_event`; block the threads handling ultrasonic ranging and servo sweep; block motor, and release any gpio resources allocated
			- As for the remainder of the code, it is just teardown: blocking the threads handling the ultrasonic ranging and servomotor sweep; stopping the motors; and releasing any allocated GPIO resources.