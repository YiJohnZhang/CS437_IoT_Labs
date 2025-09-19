'''
yjzhang2

polynomial_dstar_direction_decider.py
'''
import numpy as np

SPARSITY_THRESHOLD = 0.5	# if sparsity > SPARSITY_THRESHOLD then analyzed direction is occupied


def analyze_obstacle_map(obstacle_map:np) -> tuple:
	'''
	
	'''
	obstacle_map_x_size, obstacle_map_y_size = obstacle_map.shape
	quadrant_1_3_right_bound = int(obstacle_map_x_size / 2)
	quadrant_1_2_bottom_bound = int(obstacle_map_y_size / 2)

	# analyze quadrant 1
	quadrant_1_sum = obstacle_map[0:quadrant_1_2_bottom_bound, 0:quadrant_1_3_right_bound].sum()
	quadrant_1_sparsity = quadrant_1_sum / (quadrant_1_2_bottom_bound * quadrant_1_3_right_bound)
	# analyze quadrant 2
	quadrant_2_sum = obstacle_map[0:quadrant_1_2_bottom_bound, quadrant_1_3_right_bound:obstacle_map_y_size].sum()
	quadrant_2_sparsity = quadrant_2_sum / (quadrant_1_2_bottom_bound * (obstacle_map_y_size - quadrant_1_3_right_bound))
	# analyze quadrant 3
	quadrant_3_sum = obstacle_map[quadrant_1_2_bottom_bound:obstacle_map_x_size, 0:quadrant_1_3_right_bound].sum()
	quadrant_3_sparsity = quadrant_3_sum / ((obstacle_map_x_size - quadrant_1_2_bottom_bound) * quadrant_1_3_right_bound)
	# analyze quadrant 4
	quadrant_4_sum = obstacle_map[quadrant_1_2_bottom_bound:obstacle_map_x_size, quadrant_1_3_right_bound:obstacle_map_y_size].sum()
	quadrant_4_sparsity = quadrant_4_sum / ((obstacle_map_x_size - quadrant_1_2_bottom_bound) * (obstacle_map_y_size - quadrant_1_3_right_bound))

	return (quadrant_1_sparsity, quadrant_2_sparsity, quadrant_3_sparsity, quadrant_4_sparsity)

def reduced_resolution_map(obstacle_map) -> np:
	'''
	Returns a low resolution obstacle map to help decide which direction to go. The car still needs to avoid obstacles using the 
	naive decider provided by Freenove (get left, forward, and right obstacle distances).

	Input a m x n map, reduce it to one of the following 2x2 maps:
	Quadrant Labels
		I		II
		III		IV

	Let 1 be an obstacle; F = forward, R = right, L = left

		0	0	|	1	0	|	0	1	
		0	0	|	0	0	|	0	0	
	Go:	F,R,L		F,R			F,R

		1	1	|	1	0	|	0	1
		0	0	|	1	0	|	0	1
	Go:	L or R		R			L
		
		1	1	|	1	1	
		1	0	|	0	1	
	Go: R			L
	
	'''
	reduced_numpy_map = np.zeros((2,2), dtype=int)
	quadrant_1_sparsity, quadrant_2_sparsity, quadrant_3_sparsity, quadrant_4_sparsity = analyze_obstacle_map(obstacle_map)

	return 