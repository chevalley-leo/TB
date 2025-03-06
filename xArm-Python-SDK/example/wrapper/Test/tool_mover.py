#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2019, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

"""
Description: Move Tool Line
"""

import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from xarm.wrapper import XArmAPI





arm = XArmAPI('192.168.1.215', baud_checkset=False)
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(state=0)
arm.set_tcp_jerk(5000)
arm.set_joint_jerk(500)

#arm.move_gohome(wait=True)

#arm.set_tool_position(x=0, y=100, z=-20, roll=0, pitch=90, yaw=0, speed=100, wait=True)
#print(arm.get_position(), arm.get_position(is_radian=True))

print(arm.get_position(), arm.get_position(is_radian=True))



for i in range(100):  # Adjust the range for the number of back-and-forth movements
    
    print('set IO0 high level')
    code = arm.set_cgpio_digital(0, 1)

    arm.set_position(600, 200, 140, 0.0, 90.0, 0.0, speed=200, mvacc=10000, radius=0,wait=False)
    print('set IO0 low level')
    code = arm.set_cgpio_digital(0, 0)
    arm.set_position(600, 300, 140, 0.0, 90.0, 0.0, speed=200, mvacc=10000, radius=0,wait=False)

    #slowly add more analog to the output
    arm.set_cgpio_analog(0, (5/100)*i)








#arm.set_position(600, 200, 100, 0.0, 90.0, 0.0, speed=100, mvacc=1000, wait=True)


print(arm.get_position(), arm.get_position(is_radian=True))





#arm.move_gohome(wait=True)
arm.disconnect()