#! /usr/bin/env python

# import ros stuff
import rospy
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
desired_position_ = Point()
desired_position_.x = rospy.get_param('des_pos_x')
desired_position_.y = rospy.get_param('des_pos_y')
desired_position_.z = 0
regions_ = None
#states of robot during algorithm
state_desc_ = ['Go to point', 'wall following', 'checking leave point', 'start', 'stop']
state_ = 0
count_state_time_ = 0 # seconds the robot is in a state
count_loop_ = 0
# 0 - go to point
# 1 - wall following
# 2 - checking leave point
# 3 - start position
# 4 - stop

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
        'bleft':  min(min(msg.ranges[103:135]), 10),
        'left':  min(min(msg.ranges[57:102]), 10),
        'fleft': min(min(msg.ranges[11:56]), 10),
        'front':  min(min(min(msg.ranges[0:10]), min(msg.ranges[349:359])) , 10),
        'fright':  min(min(msg.ranges[303:348]), 10),
        'right':   min(min(msg.ranges[257:302]), 10),
        'bright':  min(min(msg.ranges[225:256]), 10),
    }

#state changer
def change_state(state):
    global state_, state_desc_
    global srv_client_wall_follower_, srv_client_go_to_point_
    global count_state_time_
    global count_loop_

    if not((state_ == 1 and state == 2) or (state_ == 2 and state == 1)):
        count_state_time_ = 0
    count_loop_ = 0
    
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
        resp = srv_client_wall_follower_(True)
    if state_ == 2:
        resp = srv_client_go_to_point_(False)
        resp = srv_client_wall_follower_(False)
    if state_ == 3:
        resp = srv_client_go_to_point_(False)
        resp = srv_client_wall_follower_(False)
    # if state_ == 4:
    #     resp = srv_client_go_to_point_(False)
    #     resp = srv_client_wall_follower_(False)

#function to calculate distance betweeen two points
def calc_dist_points(point1, point2):
    dist = math.sqrt((point1.y - point2.y)**2 + (point1.x - point2.x)**2)
    return dist    

#funcdion to nprmalize angle
def normalize_angle(angle):
    if(math.fabs(angle) > math.pi):
        angle = angle - (2 * math.pi * angle) / (math.fabs(angle))
    return angle

list_hp = []
len_hp = 0
def check_last_hp(position):
    global list_hp, len_hp
    result = False
    for i in range(len_hp-2):
        if calc_dist_points(position, list_hp[i]) < 0.2:
            result = True
    return result

def main():
    # stating global parameters
    global regions_, position_, desired_position_, state_, yaw_, st_position_
    global srv_client_go_to_point_, srv_client_wall_follower_
    global count_state_time_, count_loop_
    global st_point
    global list_hp, len_hp
    
    rospy.init_node('distbug_step')
    
    #publisher to change velocities
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
    
    #initialize subscribers laser and odometery
    sub_laser = rospy.Subscriber('/scan', LaserScan, clbk_laser)
    sub_odom = rospy.Subscriber('/odom', Odometry, clbk_odom)
    
    #initialize servers for other scripts involved
    rospy.wait_for_service('/go_to_point_switch_step')
    rospy.wait_for_service('/wall_follower_switch')
    rospy.wait_for_service('/gazebo/set_model_state')
    
    srv_client_go_to_point_ = rospy.ServiceProxy('/go_to_point_switch_step', SetBool)
    srv_client_wall_follower_ = rospy.ServiceProxy('/wall_follower_switch', SetBool)
    srv_client_set_model_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
    
    # set robot position
    model_state = ModelState()
    model_state.model_name = 'turtlebot3_burger'
   # change state to start
    change_state(3)
    
    st_position_ = position_

    #st
    prev_step_pos = position_
    step = 0.3
    cur_step_dist = 0
    count_steps = 0
    counter = 0
    #end

    #calculate the yaw to the destination point
    desired_yaw = math.atan2(desired_position_.y - position_.y, desired_position_.x - position_.x)
    err_yaw = desired_yaw - yaw_
    if math.fabs(err_yaw) > math.pi:
        if err_yaw > 0:
            err_yaw = err_yaw - 2 * math.pi
        else: 
            err_yaw = err_yaw + 2 * math.pi
    degree = err_yaw * 180 / math.pi
    log = "st angle %.4f" % degree
    rospy.loginfo(log)

    # if (degree < 10 and degree >= 0) or (degree > -10 and degree <= 0):
    #     log = "dist front %.4f" % regions_['front']
    #     rospy.loginfo(log)
    # if degree <= 56 and degree > 10:
    #     log = "dist fleft %.4f" % regions_['fleft']
    #     rospy.loginfo(log)
    # if degree <= 102 and degree > 56:
    #     log = "dist left %.4f" % regions_['left']
    #     rospy.loginfo(log)
    # if degree <= 135 and degree > 102:
    #     log = "dist bleft %.4f" % regions_['bleft']
    #     rospy.loginfo(log)
    # if degree <= -10 and degree > -56:
    #     log = "dist fright %.4f" % regions_['fright']
    #     rospy.loginfo(log)
    # if degree <= -56 and degree > -102:
    #     log = "dist right %.4f" % regions_['right']
    #     rospy.loginfo(log)
    # if degree <= -102 and degree >= -135:
    #     log = "dist bleft %.4f" % regions_['bright']
    #     rospy.loginfo(log)
    
    #point the robot to the destination point
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
    
    # initialize going to the point
    change_state(0)
    
    rate = rospy.Rate(20)
    #circle to change robot states
    while not rospy.is_shutdown():
        if regions_ == None:
            continue
        #calculate distance to line (s-f)
        # distance_position_to_line = distance_to_line(position_)
        
        #check if robot arived at the dest point
        if math.sqrt((desired_position_.y - position_.y)**2 + (desired_position_.x - position_.x)**2) < 0.15 :
            twist_msg = Twist()
            twist_msg.angular.z = 0
            twist_msg.linear.x = 0
            pub.publish(twist_msg)
            log = "point reached"
            rospy.loginfo(log)
            exit(0)
        
         #go to point state
        elif state_ == 0:
            #check if there is an obstacle forward
            if regions_['front'] > 0 and regions_['front'] < 0.25:
                st_point = position_
                # log = "st_point [%.4f; %.4f] | %.4f" % (st_point.x, st_point.y, calc_dist_points(st_point, desired_position_))
                # rospy.loginfo(log)
                change_state(1)
        
        #circumnavigate until either line is crossed again or closed loop was made then point cannot be reached
        elif state_ == 1:
            # log = '%.4f' % (calc_dist_points(st_point, position_))
            # rospy.loginfo(log)
            
            cur_step_dist += calc_dist_points(position_, prev_step_pos)
            prev_step_pos = position_
            if cur_step_dist > step - 0.02:
                counter += 1
                twist_msg = Twist()
                twist_msg.linear.x = 0
                pub.publish(twist_msg)
                srv_client_wall_follower_(False)
                if counter == 25:
                    # log = "%d | %.4f" % (count_steps,cur_step_dist)
                    # rospy.loginfo(log)
                    counter = 0
                    count_steps += 1
                    cur_step_dist = 0

                    if len_hp < 25:
                        len_hp += 1
                    else:
                        list_hp.pop(0)
                    list_hp.append(position_)
                    for i in range(len_hp):
                        log = 'list_hp %d [%.4f;%.4f]' % (i,list_hp[i].x,list_hp[i].y)
                        rospy.loginfo(log)

                    change_state(2)
                    # srv_client_wall_follower_(True)

            if count_state_time_ > 20 and calc_dist_points(st_point, position_) < 0.2:
                log = "point cannot be reached"
                rospy.loginfo(log)
                exit(0)
            
            if count_state_time_ > 20 and check_last_hp(position_):
                log = "point cannot be reacheddddddd"
                rospy.loginfo(log)
                exit(0)
            # elif count_state_time_ > 20 and calc_dist_points(position_, desired_position_) < calc_dist_points(st_point, desired_position_):
            #     change_state(2)


        #checking if this point can be identified as leave point, looking in the direction of the finish basically        
        elif state_ == 2:
                
            # desired_yaw = math.atan2(desired_position_.y - position_.y, desired_position_.x - position_.x)
            # err_yaw = desired_yaw - yaw_
            # while not math.fabs(err_yaw) <= math.pi / 90:
            #     twist_msg = Twist()
            #     desired_yaw = math.atan2(desired_position_.y - position_.y, desired_position_.x - position_.x)
            #     err_yaw = desired_yaw - yaw_
            #     if math.fabs(err_yaw) > math.pi:
            #         if err_yaw > 0:
            #             err_yaw = err_yaw - 2 * math.pi
            #         else: 
            #             err_yaw = err_yaw + 2 * math.pi
            #     if err_yaw > 0:
            #         twist_msg.angular.z = 0.7
            #     else: 
            #         twist_msg.angular.z = -0.7
            #     pub.publish(twist_msg)
            #     twist_msg.angular.z = 0
            #     pub.publish(twist_msg)

            desired_yaw = math.atan2(desired_position_.y - position_.y, desired_position_.x - position_.x)
            err_yaw = desired_yaw - yaw_
            if math.fabs(err_yaw) > math.pi:
                if err_yaw > 0:
                    err_yaw = err_yaw - 2 * math.pi
                else: 
                    err_yaw = err_yaw + 2 * math.pi
            degree = err_yaw * 180 / math.pi
            
            
            if (degree < 10 and degree >= 0) or (degree > -10 and degree <= 0):
                reg = 'front'
            if degree <= 56 and degree > 10:
                reg = 'fleft'
            if degree <= 102 and degree > 56:
                reg = 'left'
            if degree <= 135 and degree > 102:
                reg = 'bleft'
            if degree <= -10 and degree > -56:
                reg = 'fright'
            if degree <= -56 and degree > -102:
                reg = 'right'
            if degree <= -102 and degree >= -135:
                reg = 'bright'

            log = "dist %s %.4f" % (reg, regions_[reg])
            rospy.loginfo(log)


            if regions_[reg] > 0.5:
                free_dist = 0.5
            else:
                free_dist = regions_[reg]

            if regions_[reg] > 0.23 and ((calc_dist_points(position_, desired_position_) - free_dist <= 0)\
                or (calc_dist_points(position_, desired_position_) - free_dist <= calc_dist_points(prev_step_pos, desired_position_) - step)):
                change_state(0)
            else:
                change_state(1)



            # #when we turned to finish and theres an obstacle we continue to circumnavigate obstacle
            # if regions_['front'] > 0.1 and regions_['front'] < 0.25:
            #     log = "not the leave point, continuing circumnavigating"
            #     rospy.loginfo(log)
            #     change_state(1)
            # else:
            #     #if there is no obstacle right in front of the robot then we go towards the next obstacle
            #     change_state(0)

        # stopping after step 
        # elif state_ == 4:
        #     twist_msg = Twist()
        #     twist_msg.linear.x = 0
        #     pub.publish(twist_msg)
        #     if count_loop_ == 19:
        #         prev_step_pos = position_
        #         cur_step_dist = 0
        #         change_state(0)
                
        
        # if state_ != 4:
        #     cur_step_dist += calc_dist_points(position_, prev_step_pos)
        #     prev_step_pos = position_
        #     if cur_step_dist > step:
        #         log = "%d | %.4f" % (count_steps,cur_step_dist)
        #         rospy.loginfo(log)
        #         change_state(4)
        
        # cur_step_dist += calc_dist_points(position_, prev_step_pos)
        # prev_step_pos = position_
        # if cur_step_dist > step - 0.02:
        #     counter += 1
        #     twist_msg = Twist()
        #     twist_msg.linear.x = 0
        #     pub.publish(twist_msg)
        #     srv_client_go_to_point_(False)
        #     srv_client_wall_follower_(False)
        #     if counter == 25:
        #         # log = "%d | %.4f" % (count_steps,cur_step_dist)
        #         # rospy.loginfo(log)
        #         counter = 0
        #         count_steps += 1
        #         cur_step_dist = 0
        #         change_state(state_)


        # if regions_['fleft'] > 0.1 and regions_['fleft'] < 1.0:
        #     counter += 1
        #     twist_msg = Twist()
        #     twist_msg.linear.x = 0
        #     pub.publish(twist_msg)
        #     srv_client_go_to_point_(False)
        #     srv_client_wall_follower_(False)
        #     log = "vision stop %.4f" % regions_['fleft']
        #     rospy.loginfo(log)
        #     exit(0)

        
        count_loop_ = count_loop_ + 1
        if count_loop_ == 20:
            count_state_time_ = count_state_time_ + 1
            count_loop_ = 0
            # log = "vision %.4f" % regions_['fleft']
            # rospy.loginfo(log)
        
        # if count_loop_ == 19:
        #     log = '%d' % count_state_time_
        #     rospy.loginfo(log)

        # rospy.loginfo(count_loop_)
        # if count_loop_ == 19:
        #     log = '[%.4f; %.4f] %.4f | state %s' % (position_.x, position_.y, calc_dist_points(position_, desired_position_), state_)
        #     rospy.loginfo(log)
            
        rate.sleep()

if __name__ == "__main__":
    main()
