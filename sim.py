from sr.robot3 import *
import math
import threading
import sys
import random


class thread_with_trace(threading.Thread):
  def __init__(self, *args, **keywords):
    threading.Thread.__init__(self, *args, **keywords)
    self.killed = False
 
  def start(self):
    self.__run_backup = self.run
    self.run = self.__run     
    threading.Thread.start(self)
 
  def __run(self):
    sys.settrace(self.globaltrace)
    self.__run_backup()
    self.run = self.__run_backup

 #these two functions are added to thread.run so that a system exit is called in self.kill()
 #thread can therefore be terminated properly compared with the regular thread class
  def globaltrace(self, frame, event, arg):
    if event == 'call':
      return self.localtrace
    else:
      return None
 
  def localtrace(self, frame, event, arg):
    if self.killed:
      if event == 'line':
        raise SystemExit()
    return self.localtrace
 
  def kill(self):
    self.killed = True


robot = Robot()

walls = [[0,1,2,3,4,5,6],[7,8,9,10,11,12,13],[14,15,16,17,18,19,20],[21,22,23,24,25,26,27]]
asteroids = range(150,200)
egg = [110]
spaceships = [[120,125],[121,126],[122,127],[123,128]]
home_zone = robot.zone
home_wall_markers = walls[home_zone]

captured_asteroids = []
start_time = robot.time()

motor1 = robot.motor_board.motors[0]
motor2 = robot.motor_board.motors[1]
servo_board = robot.servo_board
robot.arduino.pins[A0].mode=INPUT
robot.arduino.pins[A1].mode=INPUT
robot.arduino.pins[A4].mode=INPUT

def forward(speed):
    motor1.power = speed
    motor2.power = speed

def reverse(speed):
    motor1.power = -speed
    motor2.power = -speed

def rotate_right(speed):
    motor1.power = speed
    motor2.power = -speed

def rotate_left(speed):
    motor1.power = -speed
    motor2.power = speed

def rotate_left_90_degrees():
    rotate_left(0.2)
    robot.sleep(0.7)
    stop_moving()

def rotate_right_90_degrees():
    rotate_right(0.2)
    robot.sleep(0.7)
    stop_moving()

def forward_spec_distance(distance):
    forward(0.3)
    robot.sleep(distance/352)
    stop_moving()
    
def reverse_spec_distance(distance):
    reverse(0.3)
    robot.sleep(distance/352)
    stop_moving()


def stop_moving():
    motor1.power = BRAKE
    motor2.power = BRAKE

def coast():
    motor1.power = COAST
    motor2.power = COAST

def get_seen_markers():
    markers = robot.camera.see()
    output = []
    for marker in markers:
        
        if marker.id in asteroids:
            type = 'asteroid'
        elif marker.id in egg:
            type = 'egg'
        else:
            for i in range(len(walls)):
                if marker.id in walls[i]:
                    type = 'wall'+str(i)
            for i in range(len(spaceships)):
                if marker.id in spaceships[i]:
                    type = 'spaceship'+str(i)
        
        output.append([marker.id, marker.position.distance,
          marker.position.horizontal_angle,type,marker.orientation.yaw])
    return output

def get_nearest_asteroid():
    all_markers = get_seen_markers()
    asters = []
    ids = []
    for i in range(len(all_markers)):
        if all_markers[i][3] == 'asteroid' and all_markers[i][0] not in ids and all_markers[i][0] not in captured_asteroids:
            asters.append(all_markers[i])
            ids.append(all_markers[i][0])
    
    return sorted(asters,key=lambda x: (x[1]))[0] if len(asters) > 0 else [None,None,None,None,None]

   

def align(ID):
    sensitivity = 0.04
    camera_to_front_of_bot_distance = 400
    
    angle = 1
    safety_counter = 0
    while angle > sensitivity or angle < -sensitivity and safety_counter < 500:
        safety_counter+=1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        seen_marker_dists = [i[1] for i in all_markers]
        seen_marker_angles = [i[2] for i in all_markers]
        if ID not in seen_marker_ids:
            print('cannot align to marker - cannot see it')
            return False
        elif seen_marker_dists[seen_marker_ids.index(ID)] < camera_to_front_of_bot_distance:
            print('too close to marker to align')
            return False
        else:
            
            angle = seen_marker_angles[seen_marker_ids.index(ID)]
            if angle > sensitivity:
                rotate_right(1)
                robot.sleep(0.01)
                stop_moving()
            elif angle < -sensitivity:
                rotate_left(1)
                robot.sleep(0.01)
                stop_moving()
    return True if safety_counter < 500 else False

def return_home_centre():
    ID = None
    safety_counter = 0
    while ID is None and safety_counter < 100:
        safety_counter += 1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in [home_wall_markers[3]]:
                ID = i
                break
        if ID is None:
            rotate_right(1)
            robot.sleep(0.02)
            forward(0.1)
            robot.sleep(0.01)
            stop_moving()
    if safety_counter < 100:
        approach(ID,600)
    else:
        reverse_spec_distance(500)
        return_home_centre()
 

def return_home():
    ID = None
    safety_counter = 0
    while ID is None and safety_counter < 100:
        safety_counter += 1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in home_wall_markers[1:6]:
                ID = i
                break
        if ID is None:
            rotate_right(1)
            robot.sleep(0.02)
            forward(0.1)
            robot.sleep(0.01)
            stop_moving()
    if safety_counter < 100:
        approach(ID,400)
    else:
        reverse_spec_distance(500)
        return_home()


def go_to_zone(zone,approach_len=600):
    ID = None
    safety_counter = 0
    while ID is None and safety_counter < 100:
        safety_counter += 1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in walls[zone]:
                ID = i
                break
        if ID is None:
            rotate_left(0.5)
            robot.sleep(0.04)
            reverse(0.2)
            robot.sleep(0.02)
            stop_moving()
    if safety_counter < 100:
        approach(ID,approach_len)
    else:
        reverse_spec_distance(500)
        go_to_zone(zone)


def deposit_into_spaceship():
    ID = None
    safety_counter = 0
    while ID is None and safety_counter < 100:
        safety_counter += 1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in spaceships[home_zone]:
                ID = i
                break
        if ID is None:
            rotate_left(1)
            robot.sleep(0.02)
            reverse(0.1)
            robot.sleep(0.01)
            stop_moving()
    
    if safety_counter < 100:
        approach(ID)
        servo_board.servos[2].position = 1
        robot.sleep(1)
        safety_counter = 0
        while robot.arduino.pins[A0].analog_read() > 0.1  and  robot.arduino.pins[A1].analog_read() > 0.1  and  robot.arduino.pins[A4].analog_read() > 0.15 and safety_counter < 25:
            forward(0.3)
            robot.sleep(0.1)
            safety_counter += 1
        stop_moving()
        servo_board.servos[0].position = -1
        servo_board.servos[1].position = -1
        robot.sleep(0.5)
        reverse(0.5)
        robot.sleep(1)
        stop_moving()
        grabber_normal_position()
    
    else:
        reverse_spec_distance(500)
        deposit_into_spaceship()
    
 
def approach(ID,distance_of_approach=0):
    try:
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        dist = all_markers[seen_marker_ids.index(ID)][1]
        prev_dist = None
        safety_counter = 0
        while dist > distance_of_approach and safety_counter < 50:
            if not align(ID) or (prev_dist is not None and dist>(prev_dist+5)):
                break
            forward(0.55)
            all_markers = get_seen_markers()
            seen_marker_ids = [i[0] for i in all_markers]
            robot.sleep(0.1)
            prev_dist = dist
            dist = all_markers[seen_marker_ids.index(ID)][1]
            safety_counter += 1
        stop_moving()
        if ID in asteroids and safety_counter<50:
            captured_asteroids.append(ID)
            print(home_zone,': captured - ',captured_asteroids)
        elif safety_counter>=50:
            reverse(1)
            robot.sleep(0.3)
            stop_moving()

    except:
        stop_moving()
        print(home_zone,': Could not see marker ' ,ID,' to approach')
        
    
def grab_asteroid():
    servo_board.servos[0].position = 1
    servo_board.servos[1].position = 1
    robot.sleep(1)
    servo_board.servos[2].position = 0.2
    robot.sleep(1)

def grabber_normal_position():
    servo_board.servos[0].position = -1
    servo_board.servos[1].position = -1
    servo_board.servos[2].position = -1
    robot.sleep(2)

def seek_asteroid():
    ID = None
    safety_counter = 0
    while ID is None and safety_counter < 100:
        safety_counter += 1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in asteroids and i not in captured_asteroids:
                ID = i
                break
        if ID is None:
            rotate_left(0.5)
            robot.sleep(0.1)
            reverse(0.2)
            robot.sleep(0.02)
            stop_moving()
    if safety_counter >= 100:
        return False
    else:
        return True


def clamp_spaceship(zone):
    ID = None
    safety_counter = 0
    while ID is None and safety_counter < 100:
        safety_counter += 1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in spaceships[zone]:
                ID = i
                break
        if ID is None:
            rotate_right(1)
            robot.sleep(0.02)
            reverse(0.1)
            robot.sleep(0.01)
            stop_moving()
    if safety_counter < 100:
        approach(ID,400)
        align(ID)
        servo_board.servos[0].position = -1
        servo_board.servos[1].position = -1
        servo_board.servos[2].position = 0.3
        robot.sleep(1.5)
        safety_counter = 0
        while robot.arduino.pins[A4].analog_read() > 0.25 and robot.arduino.pins[A0].analog_read() > 0.08  and  robot.arduino.pins[A1].analog_read() > 0.08 and safety_counter < 20:
            forward(0.3)
            robot.sleep(0.1)
        stop_moving()
        servo_board.servos[2].position = 0
        robot.sleep(1)
        reverse(0.2)
        robot.sleep(1)
        stop_moving()
    else:
        reverse_spec_distance(500)
        clamp_spaceship(zone)


def double_asteroid_collection():
    for rep in range(2):
        continuing = True
        while continuing:    
            seek_asteroid()
            spaceships_seen = [i for i in get_seen_markers() if i[3][:9] == 'spaceship']
            nearest_aster = get_nearest_asteroid()
            continuing = False
            for spaceship in spaceships_seen:
                #THRESHOLD ANGLES AND DISTS FOR BEING DEEMED INSIDE A SHIP TO BE ADJUSTED
                if math.sqrt(nearest_aster[1]**2 + spaceship[1]**2 - (2*nearest_aster[1]*spaceship[1]*math.cos(abs(nearest_aster[2] - spaceship[2])))) > 600 or abs(nearest_aster[2] - spaceship[2]) > 0.3:
                    pass
                else:
                    captured_asteroids.append(nearest_aster[0])
                    print(nearest_aster[0],'captured by opponent')
                    continuing = True
            
        target_aster = get_nearest_asteroid()
        approach(target_aster[0])
        forward(0.2)
        robot.sleep(0.5)
        stop_moving()
        

    grab_asteroid()
    return_home_centre()
    deposit_into_spaceship()
 
def standard_asteroid_collection():
    continuing = True
    while continuing:    
        seek_asteroid()
        spaceships_seen = [i for i in get_seen_markers() if i[3][:9] == 'spaceship']
        nearest_aster = get_nearest_asteroid()
        continuing = False
        for spaceship in spaceships_seen:
            #THRESHOLD ANGLES AND DISTS FOR BEING DEEMED INSIDE A SHIP TO BE ADJUSTED
            if math.sqrt(nearest_aster[1]**2 + spaceship[1]**2 - (2*nearest_aster[1]*spaceship[1]*math.cos(abs(nearest_aster[2] - spaceship[2])))) > 600 or abs(nearest_aster[2] - spaceship[2]) > 0.3:
                pass
            else:
                captured_asteroids.append(nearest_aster[0])
                print(nearest_aster[0],'captured by opponent')
                continuing = True
        
    target_aster = get_nearest_asteroid()
        
    grabbing = True
    while grabbing:
        approach(target_aster[0])
        forward(0.2)
        robot.sleep(0.5)
        stop_moving()
        grab_asteroid()
        grabbing = False
            
            
        reverse(0.3)
        robot.sleep(1)
        stop_moving()
        if get_nearest_asteroid()[0] == target_aster[0]:
            grabbing = True
            print('retrying grab')
        
    return_home_centre()
    deposit_into_spaceship()

def scoop_asteroid_collection():
    for rep in range(3):
        continuing = True
        invalid = False
        while continuing:    
            if seek_asteroid():
                spaceships_seen = [i for i in get_seen_markers() if i[3][:9] == 'spaceship']
                nearest_aster = get_nearest_asteroid()
                if nearest_aster[0] is not None:
                    continuing = False
                    for spaceship in spaceships_seen:
                        #THRESHOLD ANGLES AND DISTS FOR BEING DEEMED INSIDE A SHIP TO BE ADJUSTED
                        if math.sqrt(nearest_aster[1]**2 + spaceship[1]**2 - (2*nearest_aster[1]*spaceship[1]*math.cos(abs(nearest_aster[2] - spaceship[2])))) > 600 or abs(nearest_aster[2] - spaceship[2]) > 0.3:
                            pass
                        else:
                            captured_asteroids.append(nearest_aster[0])
                            print(nearest_aster[0],'captured by opponent')
                            continuing = True
            else:
                invalid = True
                break
        if not invalid:
            target_aster = get_nearest_asteroid()
            approach(target_aster[0])
            
            if rep < 2:
                forward(0.3)
                robot.sleep(0.5)
                stop_moving()
            else:
                safety_counter = 0
                while robot.arduino.pins[A4].analog_read() > 0.05 and safety_counter < 25:
                    safety_counter+=1
                    forward(0.3)
                    robot.sleep(0.1)
                    stop_moving()
                
            if rep == 1:
                grab_asteroid()
                rotate_right(0.1)
                robot.sleep(2)
                stop_moving()
    
    return_home_centre()
    return_home_centre()
    reverse(0.55)
    robot.sleep(0.6)
    rotate_left(0.35)
    robot.sleep(0.3)
    forward(0.5)
    robot.sleep(0.5)
    return_home_centre()
    deposit_into_spaceship()




def deal_with_egg():
    ID = None
    safety_counter = 0
    while ID is None and safety_counter < 100:
        safety_counter += 1
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in egg:
                ID = i
                break
        if ID is None:
            rotate_left(0.5)
            robot.sleep(0.1)
            reverse(0.2)
            robot.sleep(0.02)
            stop_moving()
    if safety_counter < 100:
        approach(ID)
        forward_spec_distance(150)
        servo_board.servos[2].position = -0.2
        robot.sleep(0.4)
        grab_asteroid()
        robot.sleep(0.2)
        reverse_spec_distance(200)
        arr = [0,1,2,3]
        arr.remove(home_zone)
        zone_dict = {0:2,1:3,2:0,3:1}
        arr.remove(zone_dict[home_zone])
        target = arr[random.randint(0,1)]
        go_to_zone(target)
        go_to_zone(target)
        grabber_normal_position()
        robot.sleep(1)
        reverse_spec_distance(200)
    else:
        arr = [0,1,2,3]
        arr.remove(home_zone)
        target = arr[random.randint(0,2)]
        go_to_zone(target,1000)
        go_to_zone(target,1000)
        deal_with_egg()

def secure_spaceship():
    return_home_centre()
    return_home_centre()
    grabber_normal_position()
    reverse(0.55)
    robot.sleep(0.8)
    rotate_left(0.35)
    robot.sleep(0.3)
    forward(0.3)
    robot.sleep(0.5)
    return_home_centre()
    clamp_spaceship(home_zone)


    zone_dict = {0:2,1:3,2:0,3:1}
    go_to_zone(zone_dict[home_zone],3500)
    go_to_zone(zone_dict[home_zone],3500)
    return_home()
    forward_spec_distance(500)

    servo_board.servos[2].position = 1
    robot.sleep(1)
    reverse_spec_distance(300)
    grabber_normal_position()
    robot.sleep(0.5)

def endgame():
    print('endgame reached')
    stop_moving()
    robot.sleep(0.5)
    deal_with_egg()
    secure_spaceship()
    




collect_thread = thread_with_trace(target=scoop_asteroid_collection)
collect_thread.start()

last_time = start_time
collection_time = 60
while (robot.time() - start_time) < collection_time:
    safety_timer = (robot.time() - last_time)
    if not collect_thread.is_alive() and (robot.time() - start_time) < collection_time-5:
        collect_thread = thread_with_trace(target=scoop_asteroid_collection)
        last_time = robot.time()
        collect_thread.start()
    #safety feature sets maximum time before procedure abort at 40 secs
    elif safety_timer > 40 and collect_thread.is_alive():
        collect_thread.kill()
        grabber_normal_position()
        reverse(1)
        robot.sleep(1)
        stop_moving()
        
if collect_thread.is_alive():
    collect_thread.kill()
endgame()


#TODO
#Don't try to grab asteroids inside other spaceships -DONE
#Troubleshoot if stuck -DONE
#don't go after other bots - WIP

#FINISHING
#MAKE SURE YOUR SPACESHIP IN YOUR ZONE -DONE
#KICK OUT EGG -DONE

