#! /usr/bin/env python

# import ros stuff
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf import transformations
from std_srvs.srv import *

import math

active_ = False
pub_ = None
# regions of laser
regions_ = {
        'right': 0,
        'fright': 0,
        'front': 0,
        'fleft': 0,
        'left': 0,
}
state_ = 0
state_dict_ = {
    0: 'find the wall',
    1: 'turn left',
    2: 'follow the wall',
    3: 'turn right'
}
# switch that can be monitored for results of this service
def wall_follower_left_switch(req):
    global active_
    active_ = req.data
    res = SetBoolResponse()
    res.success = True
    res.message = 'Done!'
    return res

def clbk_laser(msg):
    global regions_
    regions_ = {
        'left':  min(min(msg.ranges[54:89]), 10),
        'fleft': min(min(msg.ranges[23:53]), 10),
        'front':  min(min(min(msg.ranges[0:22]), min(msg.ranges[338:359])) , 10),
        'fright':  min(min(msg.ranges[306:337]), 10),
        'right':   min(min(msg.ranges[270:305]), 10),
        'left45': min(msg.ranges[45],10)
    }
    take_action()
#state changer notifier
def change_state(state):
    global state_, state_dict_
    if state is not state_:
        print ('Wall follower - [%s] - %s' % (state, state_dict_[state]))
        state_ = state

# main function which tells robot what he should do(chsnges states) depending on his surroundings
def take_action():
    global regions_
    regions = regions_
    msg = Twist()
    linear_x = 0
    angular_z = 0
    
    state_description = ''
    #NOT ADVISED TO CHANGE THIS SETTINGS
    laser_range = 0.3
    
    diag_range = 0.4
    
    if regions['front'] < laser_range and regions['fleft'] > laser_range and regions['fright'] > laser_range:
        state_description = 'case 1 - front'
        change_state(3)
    elif regions['front'] > laser_range and regions['fleft'] > laser_range and regions['fright'] < laser_range:
        state_description = 'case 2 - fright'
        change_state(2)
    elif regions['front'] > laser_range and regions['fleft'] > laser_range and regions['fright'] > laser_range and regions['left45'] > diag_range:
        state_description = 'case 3 - correct angle'
        change_state(1)
    elif regions['front'] > laser_range and regions['fleft'] < laser_range and regions['fright'] > laser_range:
        state_description = 'case 4 - fleft'
        change_state(2)
    elif regions['front'] < laser_range and regions['fleft'] > laser_range and regions['fright'] < laser_range:
        state_description = 'case 5 - front and fright'
        change_state(3)
    elif regions['front'] < laser_range and regions['fleft'] < laser_range and regions['fright'] > laser_range:
        state_description = 'case 6 - front and fleft'
        change_state(3)
    elif regions['front'] < laser_range and regions['fleft'] < laser_range and regions['fright'] < laser_range:
        state_description = 'case 7 - front and fleft and fright'
        change_state(3)
    elif regions['front'] > laser_range and regions['fleft'] < laser_range and regions['fright'] < laser_range:
        state_description = 'case 8 - fleft and fright'
        change_state(0)

    else:
        state_description = 'unknown case'
        rospy.loginfo(regions)
#states 1-4 functioanally
def find_wall():
    msg = Twist()
    msg.linear.x = 0.15
    return msg

def turn_left():
    msg = Twist()
    msg.angular.z = 0.3
    return msg
    
def turn_right():
    msg = Twist()
    msg.angular.z = -0.3
    return msg

def follow_the_wall():
    msg = Twist()
    msg.linear.x = 0.15
    return msg

#main state cicle
def main():
    global pub_, active_
    
    
    rospy.init_node('reading_laser')
    
    pub_ = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
    
    sub = rospy.Subscriber('/scan', LaserScan, clbk_laser)
    
    srv = rospy.Service('wall_follower_left_switch', SetBool, wall_follower_left_switch)
    
    rate = rospy.Rate(20)
    
                    
    while not rospy.is_shutdown():
        if not active_:
            rate.sleep()
            continue
        msg = Twist()
        if state_ == 0:
            msg = find_wall()
        elif state_ == 1:
            msg = turn_left()
        elif state_ == 2:
            msg = follow_the_wall()
        elif state_ == 3:
            msg = turn_right()
        else:
            rospy.logerr('Unknown state!')
        
        pub_.publish(msg)
        
        rate.sleep()

if __name__ == '__main__':
    main()
