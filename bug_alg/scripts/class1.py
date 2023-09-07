#! /usr/bin/env python

# import ros stuff
import rospy
import time
import datetime
# import ros message
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from tf import transformations
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import SetModelState
# import ros service
from std_srvs.srv import *

import math
#initializing parameters
srv_client_go_to_point_ = None
srv_client_wall_follower_ = None
yaw_ = 0
#get the innitial position coordinates
position_ = Point()
initial_position_ = Point()
initial_position_.x = rospy.get_param('initial_x')
initial_position_.y = rospy.get_param('initial_y')
initial_position_.z = 0
#get the destination coordinates
target_ = Point()
target_.x = rospy.get_param('des_pos_x')
target_.y = rospy.get_param('des_pos_y')
target_.z = 0
regions_ = None
#states of robot during algorithm
state_desc_ = ['forward', 'wall following', 'rotate to target', 'start', 'change local direction']
state_ = 0
count_state_time_ = 0 # seconds the robot is in a state
count_loop_ = 0
# 0 - forward
# 1 - wall following
# 2 - rotate to target
# 3 - start position
# 4 - change local direction
list_hp_ = []  
SWF = 1

# callbacks
#robot movement callbacks
def clbk_odom(msg):
    global position_, yaw_
    
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


#laser callback
def clbk_laser(msg):
    global regions_
    regions_ = {
        'left':  min(min(msg.ranges[54:89]), 10),
        'fleft': min(min(msg.ranges[18:53]), 10),
        'front':  min(min(min(msg.ranges[0:10]), min(msg.ranges[349:359])) , 10),
        'fright':  min(min(msg.ranges[306:341]), 10),
        'right':   min(min(msg.ranges[270:305]), 10),
        'left45': msg.ranges[45] 
    }

#state changer
def change_state(state,SWF=None):
    global state_, state_desc_
    global srv_client_wall_follower_, srv_client_go_to_point_
    global count_state_time_
    count_state_time_ = 0
    state_ = state
    #informing user that the state has changed
    log = "state changed: %s" % state_desc_[state]
    rospy.loginfo(log)
    #differnet states turn on and off different servers(other scripts)
    if state_ == 0:
        resp = srv_client_go_to_point_(True)
        resp = srv_client_wall_follower_(False)
    if state_ == 1:
        resp = srv_client_go_to_point_(False)
        if SWF is not None and SWF == 1:
            resp = srv_client_wall_follower_(True)
        else:
            resp = srv_client_wall_follower_(False)
    if state_ == 2:
        resp = srv_client_go_to_point_(False)
        resp = srv_client_wall_follower_(False)
    if state_ == 3:
        resp = srv_client_go_to_point_(False)
        resp = srv_client_wall_follower_(False)
    
#fucntion to calculate distance to line connecting start and finish
def distance_to_line(p0):
    # p0 is the current position
    # p1 and p2 points define the line
    global st_position_, target_
    p1 = st_position_
    p2 = target_
    up_eq = math.fabs((p2.y - p1.y) * p0.x - (p2.x - p1.x) * p0.y + (p2.x * p1.y) - (p2.y * p1.x))
    lo_eq = math.sqrt(pow(p2.y - p1.y, 2) + pow(p2.x - p1.x, 2))
    distance = up_eq / lo_eq
    
    return distance

#function to calculate distance betweeen two points
def calc_distarts(point1, point2):
    dist = math.sqrt((point1.y - point2.y)**2 + (point1.x - point2.x)**2)
    return dist    
    
def check_if_point_in_list(point, list_hp, i):
    for p in list_hp:
        if p[2] != i and p[0] is not None and calc_distarts(point, p[0]) < 0.1:
            
                return True
    return False

 			
def check_last_leave_point_is_set(list_hp_, i):
    for p in list_hp_:
        if p[2] == i and p[1] == 'leave':
            if p[0] is not None:
                return True
    return False
    
def get_last_hit_point(i, position_, list_hp_):
    for p in list_hp_:
        if p[2] == i and p[1] == 'hit':
            if calc_distarts(p[0], position_) < 0.1:
                return True
    return False

#funcdion to nprmalize angle
def normalize_angle(angle):
    if(math.fabs(angle) > math.pi):
        angle = angle - (2 * math.pi * angle) / (math.fabs(angle))
    return angle
    

def main():
    # stating global parameters
    global regions_, position_, target_, state_, yaw_, st_position_
    global srv_client_go_to_point_, srv_client_wall_follower_
    global count_state_time_, count_loop_
    global start
    global list_hp_
    global SWF
    #global v
    #global w
    #global c_v
    #global c_w
    #v = c_v
    #w = 0
    list_hp_ = []
    list_lp_ = []
    SWF = 1
    i = 0
    need_to_return = 0
    timer_hp = None
    rospy.init_node('alg1')
    Li = None
    Hi = None
    Q = calc_distarts(position_, target_)
    log = "Calculated new Q %s" % Q
    rospy.loginfo(log)
    timer_hp = datetime.datetime.now()
    OBSTACLES_COUNT = 0
    POINTS = []
    
    #publisher to change velocities
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
    
    #initialize subscribers laser and odometery
    sub_laser = rospy.Subscriber('/scan', LaserScan, clbk_laser)
    sub_odom = rospy.Subscriber('/odom', Odometry, clbk_odom)
    
    #initialize servers for other scripts involved
    rospy.wait_for_service('/go_to_point_switch')
    rospy.wait_for_service('/wall_follower_switch')
    rospy.wait_for_service('/gazebo/set_model_state')
    
    srv_client_go_to_point_ = rospy.ServiceProxy('/go_to_point_switch', SetBool)
    srv_client_wall_follower_ = rospy.ServiceProxy('/wall_follower_switch', SetBool)
    srv_client_set_model_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
    
    # set robot position
    model_state = ModelState()
    model_state.model_name = 'turtlebot3_burger'
    
    change_state(3) #state -> start
    log = "Starting"
    rospy.loginfo(log)
    
    st_position_ = position_
       
    #calculate the yaw to the destination point
    desired_yaw = math.atan2(target_.y - position_.y, target_.x - position_.x)
    err_yaw = desired_yaw - yaw_
    
    #point the robot to the destination point
    while not math.fabs(err_yaw) <= math.pi / 90:
        twist_msg = Twist()
        desired_yaw = math.atan2(target_.y - position_.y, target_.x - position_.x)
        err_yaw = desired_yaw - yaw_
        twist_msg.angular.z = 0.7 if err_yaw > 0 else -0.7
        pub.publish(twist_msg)
        twist_msg.angular.z = 0
        pub.publish(twist_msg)
    
    
    change_state(0) #state -> forward
    log = "Moving forward"
    rospy.loginfo(log)
    
    rate = rospy.Rate(20)
    #circle to change robot states
    while not rospy.is_shutdown():
        if regions_ == None:
            continue
        #calculate distance to line (s-f)
        distance_position_to_line = distance_to_line(position_)
        
        
        
        #FORWARD
        if state_ == 0:
            if count_state_time_ > 20:
                POINTS.append(position_)
            Q = calc_distarts(position_, target_)
            log = "Calculated new Q %s" % Q
            rospy.loginfo(log)
            #target reached?
            log = "Check if target reached"
            rospy.loginfo(log)
            if math.sqrt((target_.y - position_.y)**2 + (target_.x - position_.x)**2) < 0.15 :
                twist_msg = Twist()
                twist_msg.angular.z = 0
                twist_msg.linear.x = 0
                pub.publish(twist_msg)
                log = "point reached"
                rospy.loginfo(log)
                RESULT_TIME = (datetime.datetime.now() - timer_hp)
                exit(0)
                
            #obstacle hit?
            log = "Check if obstacle hit"
            rospy.loginfo(log)
            if regions_['front'] > 0 and regions_['front'] < 0.25:
                start = position_
                i = i + 1
                list_hp_.append([position_, 'hit', i])
                list_hp_.append([[], 'leave', i])
                log = "list_hp: %s" % list_hp_
                rospy.loginfo(log)
                log = "Added hit point"
                rospy.loginfo(log)
                log = "hit is: %s" % Hi
                rospy.loginfo(log)
               
                SWF = 1
                
                OBSTACLES_COUNT += 1
                change_state(1) #state -> wall following
        
        #WALL FOLLOWING
        elif state_ == 1:
            if count_state_time_ > 20:
                POINTS.append(position_)
            Q = calc_distarts(position_, target_)
            log = "Calculated new Q %s" % Q
            rospy.loginfo(log)
            log = "Check if need to return"
            rospy.loginfo(log)
            if need_to_return == 1:
                log = "Need to return + check if last hit point reached"
                rospy.loginfo(log)
                if check_same_point(position_, list_hp_):
                    log = "Reached last hit point"
                    rospy.loginfo(log)
                    need_to_return = 0
            #target reached?
            #log = "Check if target reached from wall following"
            #rospy.loginfo(log)
            if math.sqrt((target_.y - position_.y)**2 + (target_.x - position_.x)**2) < 0.15 :
                twist_msg = Twist()
                twist_msg.angular.z = 0
                twist_msg.linear.x = 0
                pub.publish(twist_msg)
                log = "point reached"
                rospy.loginfo(log)
                RESULT_TIME = (datetime.datetime.now() - timer_hp)
                exit(0)
            
            log = "Check if encountered old points step %s" % i
            rospy.loginfo(log)
            if check_if_point_in_list(position_, list_hp_, i) and check_last_leave_point_is_set(list_hp_, i):
                need_to_return = 1
                log = "Reached old point"
                rospy.loginfo(log)

            #Robot is closer to T and way towards T is free
            log = "Check if reached leave point"
            rospy.loginfo(log)
            
            log = "calc_distarts(position_, target_) %s" % calc_distarts(position_, target_)
            rospy.loginfo(log)
            log = "Q %s" % Q
            rospy.loginfo(log)
            log = "calc_distarts(position_, target_)< Q) %s" % (calc_distarts(position_, target_)< Q)
            rospy.loginfo(log)

            
            if count_state_time_ > 20 and \
               calc_distarts(position_, target_)< Q:
                    
                    change_state(2) #state -> rotate to target
            #current position is in list_hp
            else:
                log = "Not leave point"
                rospy.loginfo(log)
            log = "Check if reached last hit point so that target is not reachable"
            rospy.loginfo(log)
            log = "last hit point %s" % get_last_hit_point(i, position_, list_hp_)
            rospy.loginfo(log)
            if count_state_time_ > 20 and get_last_hit_point(i, position_, list_hp_):
            
                twist_msg = Twist()
                twist_msg.angular.z = 0
                twist_msg.linear.x = 0
                pub.publish(twist_msg)
                log = "point cannot be reached"
                rospy.loginfo(log)
                RESULT_TIME = (datetime.datetime.now() - timer_hp)
                exit(0)
                
            #if check_if_point_in_list(position_, list_hp_) and (datetime.datetime.now() - timer_hp)> datetime.timedelta(seconds=1):
            #    change_state(4) #state -> change local direction
                
            
             
        #ROTATE TO TARGET   
        elif state_ == 2:
                #rotate to target
                log = "Rotating"
                rospy.loginfo(log)
                desired_yaw = math.atan2(target_.y - position_.y, target_.x - position_.x)
                err_yaw = desired_yaw - yaw_
                while not math.fabs(err_yaw) <= math.pi / 90:
                    twist_msg = Twist()
                    desired_yaw = math.atan2(target_.y - position_.y, target_.x - position_.x)
                    err_yaw = desired_yaw - yaw_
                    twist_msg.angular.z = 0.7 if err_yaw > 0 else -0.7
                    pub.publish(twist_msg)
                    twist_msg.angular.z = 0
                    pub.publish(twist_msg)
                
                #when we turned to finish and theres an obstacle we continue to circumnavigate obstacle
                if regions_['front'] > 0.1 and regions_['front'] < 0.25:
                    log = "not the leave point, continuing circumnavigating"
                    rospy.loginfo(log)
                    change_state(1) #state -> wall following
                else:
                 #if there is no obstacle right in front of the robot then we go towards the next obstacle
                   
                    log = "Setting leave point"
                    rospy.loginfo(log)
                    for p in list_hp_:
                        if p[2] == i and p[1] == 'leave':
                            p[0] = position_
                    rospy.loginfo(log)
                    
                    log = "list_hp: %s" % list_hp_
                    rospy.loginfo(log)
                    change_state(0) #state -> forward
                

        #CHANGE LOCAL DIRECTION
        elif state_ == 4:
                log = "Returning 180"
                rospy.loginfo(log)
                while regions_['left45'] > 0.4 :
                    twist_msg = Twist()
                    twist_msg.angular.z = 0.3
                    pub.publish(twist_msg)
                SWF = -1
                change_state(1,SWF) #state -> wall following
                
        count_loop_ = count_loop_ + 1
        if count_loop_ == 20:
            count_state_time_ = count_state_time_ + 1
            count_loop_ = 0
            
        rate.sleep()

if __name__ == "__main__":
    main()