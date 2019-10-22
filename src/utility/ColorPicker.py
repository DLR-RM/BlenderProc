import random
import copy
import numpy as np
import colorsys



def get_colors(num):
    """
    Description: This function generates N equidistant rgb colors and returns num of them.
    Basically it splits a cube of shape 256 x 256 x 256 in to N smaller cubes. Where, N = K^3
    and K is the smallest integer for which N >= num. 
    num : integer
    colors: list of rgb colors, where each element is a list of size 3 for each channel of rgb
    """
    K = 1
    colors = []
    while K**3 < num: # find K bound of cubes to be made
        K+=1
    block_length = 256/K 
    for r in range(K):
        r_mid_point = int(round(block_length * r +  block_length/2))
        for g in range(K):
            g_mid_point = int(round(block_length * g +  block_length/2))
            for b in range(K):
                b_mid_point = int(round(block_length * b +  block_length/2))
                colors.append([r_mid_point,g_mid_point,b_mid_point])
    return colors[:-num]
    
    

