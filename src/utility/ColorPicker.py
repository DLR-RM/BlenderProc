import random
import copy
import numpy as np
import colorsys

def hex_to_rgb(hex):
    _hex = hex.lstrip('#')
    hlen = len(_hex)
    return tuple(int(_hex[i:i+hlen//3], 16) for i in range(0, hlen, hlen//3))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % tuple(rgb)

def get_colors(num):
    upper = 1
    colors = []
    while upper**3 < num: # find upper bound of cubes to be made
        upper+=1
    block_length = 256/upper 
    for r in range(upper):
        r_mid_point = int(round(block_length * r +  block_length/2))
        for g in range(upper):
            g_mid_point = int(round(block_length * g +  block_length/2))
            for b in range(upper):
                b_mid_point = int(round(block_length * b +  block_length/2))
                colors.append([r_mid_point,g_mid_point,b_mid_point])
    return colors[:num]
    
    

