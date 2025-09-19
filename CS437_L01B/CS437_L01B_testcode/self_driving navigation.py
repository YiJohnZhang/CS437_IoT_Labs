# Minqiang Liu(mliu110@illinois.edu), Yi Zhang(yjzhang2@illinois.edu)

#
# Purpose:
#   Drive the Freenove 4WD Smart Car Kit from a start cell to a goal cell
#   on a fixed occupancy grid using A* path planning.
#   Prints every coordinate along the path, prints the grid before driving,
#   and ONLY stops right before turns (continuous drive on straight runs).
#
# How to use:
#   python self_driving_navigation.py --goal 9 9
#
#   - Place the car on start cell (0,0) facing +Y.
#   - Obstacles are defined in the grid[] array.
#   - The car follows the A* path and pauses 0.5s before turning.

import time
import math
import argparse
import numpy as np
from heapq import heappush, heappop

from motor import Ordinary_Car  # Freenove motor driver

# --------------------------- Constants ---------------------------------------
SAFE_SPEED = 600
TURN_SPEED = 1000

CM_PER_SEC = 40
DEG_PER_SEC = 95.0

POSE_SETTLE_SEC = 0
TURN_PAUSE_SEC = 0.5
TURN_AFTER_PAUSE_SEC = 3.0  # NEW: post-turn stop duration
MAX_RUNTIME_SEC = 180.0

CELL_CM = 20.0
ORIGIN = (0, 0)
START_YAW_DEG = 0.0  # 0Â° means facing +Y (north). Positive rotation = left (CCW).

# --------------------------- Motor helpers -----------------------------------
def stop(car: Ordinary_Car):
    car.set_motor_model(0, 0, 0, 0)

def forward_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(SAFE_SPEED + 300, SAFE_SPEED, SAFE_SPEED, SAFE_SPEED) # +300 to make my car(car issue) kit run on a line 
    time.sleep(max(0.0, seconds))
    stop(car)

def backward_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(-SAFE_SPEED, -SAFE_SPEED, -SAFE_SPEED, -SAFE_SPEED)
    time.sleep(max(0.0, seconds))
    stop(car)

def spin_left_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(-TURN_SPEED - 300, -TURN_SPEED, TURN_SPEED, TURN_SPEED) # -300 to make my car(car issue) kit run on a line 
    time.sleep(max(0.0, seconds))
    stop(car)

def spin_right_time(car: Ordinary_Car, seconds: float):
    car.set_motor_model(TURN_SPEED, TURN_SPEED, -TURN_SPEED - 300, -TURN_SPEED) # -300 to make my car(car issue) kit run on a line 
    time.sleep(max(0.0, seconds))
    stop(car)

def drive_forward_cm(car: Ordinary_Car, cm: float):
    if abs(cm) < 1e-3:
        return
    secs = abs(cm) / max(1e-6, CM_PER_SEC)
    if cm > 0:
        forward_time(car, secs)
    else:
        backward_time(car, secs)

def rotate_in_place_deg(car: Ordinary_Car, deg: float):
    if abs(deg) < 1.0:
        return
    secs = abs(deg) / max(1e-6, DEG_PER_SEC)
    if deg > 0:
        spin_left_time(car, secs)
    else:
        spin_right_time(car, secs)

# --------------------------- A Star --------------------------------------
DIRS = [(-1,0), (1,0), (0,-1), (0,1)]  # N/S/W/E in grid (row, col) space

def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def astar(grid: np.ndarray, start, goal):
    """Compute A* path on occupancy grid (0=free,1=obstacle)."""
    h, w = grid.shape
    sx, sy = start; gx, gy = goal
    if not (0 <= sx < h and 0 <= sy < w and 0 <= gx < h and 0 <= gy < w):
        return None
    if grid[gx, gy] == 1:
        return None

    gscore = {start: 0}
    fscore = {start: heuristic(start, goal)}
    came = {}
    pq = []
    heappush(pq, (fscore[start], start))

    while pq:
        _, cur = heappop(pq)
        if cur == goal:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            return path[::-1]
        cx, cy = cur
        for dx, dy in DIRS:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < h and 0 <= ny < w):
                continue
            if grid[nx, ny] == 1:
                continue
            tentative = gscore[cur] + 1
            if tentative < gscore.get((nx, ny), 1e9):
                came[(nx, ny)] = cur
                gscore[(nx, ny)] = tentative
                fscore[(nx, ny)] = tentative + heuristic((nx, ny), goal)
                heappush(pq, (fscore[(nx,ny)], (nx,ny)))
    return None

# --------------------------- Utils -------------------------------------------
def print_ascii_grid(grid: np.ndarray, path=None, start=None, goal=None):
    """Pretty-print the grid (0=free '.', 1=obstacle '#'). Optionally overlay path."""
    h, w = grid.shape
    path_set = set(path) if path else set()
    rows = []
    for r in range(h):
        line = []
        for c in range(w):
            if start and (r, c) == start:
                ch = 'S'
            elif goal and (r, c) == goal:
                ch = 'G'
            elif (r, c) in path_set:
                ch = '.'
            else:
                ch = '#' if grid[r, c] == 1 else ' '
            line.append(ch)
        rows.append(''.join(line))
    print("[GRID]")
    for row in rows:
        print(row)

# --------------------------- Navigator ---------------------------------------
class Navigator:
    def __init__(self, car: Ordinary_Car, cell_cm=CELL_CM):
        self.car = car
        self.cell_cm = float(cell_cm)
        self.x_cm = 0.0
        self.y_cm = 0.0
        self.yaw_deg = START_YAW_DEG

    def set_start(self, x_cm: float, y_cm: float, yaw_deg: float = START_YAW_DEG):
        self.x_cm, self.y_cm, self.yaw_deg = float(x_cm), float(y_cm), float(yaw_deg)

    def _grid_to_world_cm(self, cell, origin=ORIGIN):
        # world-x grows with grid row, world-y grows with grid col
        tx_cm = (cell[0] - origin[0]) * self.cell_cm
        ty_cm = (cell[1] - origin[1]) * self.cell_cm
        return tx_cm, ty_cm

    def _rotate_to_heading_toward(self, target_cell, origin=ORIGIN):
        tx, ty = self._grid_to_world_cm(target_cell, origin)
        dx = tx - self.x_cm
        dy = ty - self.y_cm
        desired_yaw = math.degrees(math.atan2(dx, dy))  # yaw measured from +Y
        rot = (desired_yaw - self.yaw_deg + 180) % 360 - 180
        if abs(rot) > 2.0:
            stop(self.car)                  
            time.sleep(TURN_PAUSE_SEC)      
            rotate_in_place_deg(self.car, rot)
            self.yaw_deg = (self.yaw_deg + rot) % 360
            stop(self.car)                 
            time.sleep(TURN_AFTER_PAUSE_SEC)  


    def _drive_run_to(self, last_cell_in_run, origin=ORIGIN):
        """Drive forward in one continuous motion to the last cell in the straight run."""
        tx, ty = self._grid_to_world_cm(last_cell_in_run, origin)
        dx = tx - self.x_cm
        dy = ty - self.y_cm
        dist = math.hypot(dx, dy)
        if dist > 0.5:
            drive_forward_cm(self.car, dist)
            self.x_cm, self.y_cm = tx, ty
        if POSE_SETTLE_SEC > 0:
            time.sleep(POSE_SETTLE_SEC)

    def follow_path(self, path, origin=ORIGIN):
        if not path or len(path) < 2:
            print("[NAV] Empty or short path.")
            return False

        # Print every cell (for logging/visibility)
        for cell in path:
            print(f"[NAV] Path cell: {cell}")

        # Move along the path in STRAIGHT RUNS (no stop until a turn is needed)
        i = 1  # index of the next cell to reach
        while i < len(path):
            prev = path[i - 1]
            cur = path[i]
            step = (cur[0] - prev[0], cur[1] - prev[1])  # grid step direction

            # Extend the run while direction doesn't change
            run_end = i
            while run_end + 1 < len(path):
                a = path[run_end]
                b = path[run_end + 1]
                nxt = (b[0] - a[0], b[1] - a[1])
                if nxt != step:
                    break
                run_end += 1

            # Turn (if needed) to face the run direction, then drive the whole run in one go
            last_cell = path[run_end]
            self._rotate_to_heading_toward(last_cell, origin=origin)
            self._drive_run_to(last_cell, origin=origin)

            # If a turn is coming up (i.e., there is a next segment with different direction),
            # we'll pause/rotate at the START of the next loop iteration via _rotate_to_heading_toward.
            i = run_end + 1

        stop(self.car)
        return True

# --------------------------- Main --------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", nargs=2, type=int, required=True,
                        help="Goal cell coordinates: row col")
    args = parser.parse_args()
    goal = (args.goal[0], args.goal[1])

    print("[INFO] Init motor ...")
    car = Ordinary_Car()

    # Example grid
    grid = np.zeros((10, 10), dtype=int)
    grid[4, 2:7] = 1
    grid[6, 3:9] = 1

    start = (0, 0)

    print(f"[INFO] Planning A* path from {start} to {goal} ...")
    path = astar(grid, start, goal)
    print("[INFO] Path:", path)

    # Print grid BEFORE driving (with S/G and path overlay if available)
    print_ascii_grid(grid, path=path, start=start, goal=goal)

    start_time = time.time()
    try:
        if not path:
            print("[WARN] No path found. Abort.")
            return

        nav = Navigator(car, cell_cm=CELL_CM)
        nav.set_start(0.0, 0.0, START_YAW_DEG)

        print("[INFO] Start driving ... (continuous on straights; stop only to turn)")
        ok = nav.follow_path(path, origin=ORIGIN)
        print("[RESULT]", "Reached goal." if ok else "Failed.")

        if (time.time() - start_time) > MAX_RUNTIME_SEC:
            print("[INFO] Max runtime reached. Stopping.")

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt. Stopping ...")
    except Exception as ex:
        print(f"[ERROR] Unexpected exception: {ex}")
    finally:
        try:
            stop(car)
        except Exception:
            pass
        try:
            car.close()
        except Exception:
            pass
        print("[INFO] Cleanup done. Bye.")

if __name__ == "__main__":
    main()
