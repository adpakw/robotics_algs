#! /usr/bin/env python

# import ros stuff
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist, Point
from nav_msgs.msg import Odometry
from tf import transformations
from std_srvs.srv import *

import math

active_ = False

# robot state variables
position_ = Point()
yaw_ = 0
# machine state
state_ = 0
# goal
desired_position_ = Point()
desired_position_.x = rospy.get_param('des_pos_x')
desired_position_.y = rospy.get_param('des_pos_y')
desired_position_.z = 0
# parameters
yaw_precision_ = 2*math.pi / 90 # +/- 2 degree allowed
dist_precision_ = 0.1

# publishers
pub = None

# service callbacks
def go_to_point_switch_step(req):
    global active_
    active_ = req.data
    res = SetBoolResponse()
    res.success = True
    res.message = 'Done!'
    return res

# callbacks
#movement callbacks
def clbk_odom(msg):
    global position_
    global yaw_
    
    # position
    position_ = msg.pose.pose.position
    
    # yaw
    quaternion = (
        msg.pose.pose.orientation.x,
        msg.pose.pose.orientation.y,
        msg.pose.pose.orientation.z,
        msg.pose.pose.orientation.w)
    euler = transformations.euler_from_quaternion(quaternion)
    yaw_ = euler[2]

#state changer outputs state of the robot
def change_state(state):
    global state_
    state_ = state
    print ('State changed to [%s]' % state_)

def normalize_angle(angle):
    if(math.fabs(angle) > math.pi):
        angle = angle - (2 * math.pi * angle) / (math.fabs(angle))
    return angle

#turning in the right direction if for some reson the robot has been turned away
def fix_yaw(des_pos):
    global yaw_, pub, yaw_precision_, state_
    desired_yaw = math.atan2(des_pos.y - position_.y, des_pos.x - position_.x)
    err_yaw = normalize_angle(desired_yaw - yaw_)
    
    rospy.loginfo(err_yaw)
    
    twist_msg = Twist()
    
    #fixing yaw
    if math.fabs(err_yaw) > yaw_precision_:
        twist_msg.angular.z = 0.2 if err_yaw > 0 else -0.2
    
    pub.publish(twist_msg)
    
    # state change conditions/ if we a looking towards the desired point go forwards
    if math.fabs(err_yaw) <= yaw_precision_:
        print ('Yaw error: [%s]' % err_yaw)
        twist_msg.angular.z = 0
        pub.publish(twist_msg)
        change_state(1)

# function that checks constanly if the robot is on the right way and whether he reached the point to stop there
def go_straight_ahead(des_pos):
    global yaw_, pub, yaw_precision_, state_
    desired_yaw = math.atan2(des_pos.y - position_.y, des_pos.x - position_.x)
    err_yaw =  normalize_angle(desired_yaw - yaw_)
    err_pos = math.sqrt(pow(des_pos.y - position_.y, 2) + pow(des_pos.x - position_.x, 2))
    
    
    
    if err_pos > dist_precision_:
        twist_msg = Twist()
        twist_msg.linear.x = 0.2
        pub.publish(twist_msg)
    else:
        print ('Position error: [%s]' % err_pos)
        #stop at finish
        change_state(2)
    
    # state change conditions/ if robot is looking the wrong way we go to turning him back
    if math.fabs(err_yaw) > yaw_precision_:
        print ('Yaw error: [%s]' % err_yaw)
        change_state(0)

# "sleep" state of robot
def done():
    twist_msg = Twist()
    twist_msg.linear.x = 0
    twist_msg.angular.z = 0
    pub.publish(twist_msg)

def main():
    global pub, active_
    
    #initializing node, publishers and services
    rospy.init_node('go_to_point')
    
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
    
    sub_odom = rospy.Subscriber('/odom', Odometry, clbk_odom)
    
    srv = rospy.Service('go_to_point_switch_step', SetBool, go_to_point_switch_step)
    
    rate = rospy.Rate(40)
    
    #point the robot to the destination point
    desired_yaw = math.atan2(desired_position_.y - position_.y, desired_position_.x - position_.x)
    err_yaw = desired_yaw - yaw_
    

    while not math.fabs(err_yaw) <= math.pi / 90:
        twist_msg = Twist()
        desired_yaw = math.atan2(desired_position_.y - position_.y, desired_position_.x - position_.x)
        err_yaw = desired_yaw - yaw_
        if math.fabs(err_yaw) > math.pi:
            if err_yaw > 0:
                err_yaw = err_yaw - 2 * math.pi
            else: 
                err_yaw = err_yaw + 2 * math.pi
        if err_yaw > 0:
            twist_msg.angular.z = 0.7
        else: 
            twist_msg.angular.z = -0.7
        pub.publish(twist_msg)
        twist_msg.angular.z = 0
        pub.publish(twist_msg)
    
    #main cicle for robot states
    while not rospy.is_shutdown():
        if not active_:
            continue
        else:
            if state_ == 0:
                fix_yaw(desired_position_)
            elif state_ == 1:
                go_straight_ahead(desired_position_)
            elif state_ == 2:
                done()
            else:
                rospy.logerr('Unknown state!')
        
        rate.sleep()

if __name__ == '__main__':
    main()