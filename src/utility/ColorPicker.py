import random
import copy
import numpy as np
import colorsys



def get_colors(num):
    """
    Description: This function generates N equidistant rgb colors and returns num of them.
    Basically it splits a cube of shape 256 x 256 x 256 in to N smaller cubes. Where, N = cube_length^3
    and cube_length is the smallest integer for which N >= num. 
    num : integer
    colors: list of rgb colors, where each element is a list of size 3 for each channel of rgb
    """
    cube_length = 1
    colors = []
    while cube_length**3 < num: # find cube_length bound of cubes to be made
        cube_length+=1
    block_length = 256/cube_length 
    for r in range(cube_length):
        r_mid_point = int(round(block_length * r +  block_length/2))
        for g in range(cube_length):
            g_mid_point = int(round(block_length * g +  block_length/2))
            for b in range(cube_length):
                b_mid_point = int(round(block_length * b +  block_length/2))
                colors.append([r_mid_point,g_mid_point,b_mid_point])
    return colors[:num]
    
    

