from sr.robot3 import *
import math

robot = Robot()

walls = [[0,1,2,3,4,5,6],[7,8,9,10,11,12,13],[14,15,16,17,18,19,20],[21,22,23,24,25,26,27]]
asteroids = range(150,200)
egg = [110]
spaceships = [[120,125],[121,126],[122,127],[123,128]]
home_zone = robot.zone
home_wall_markers = walls[home_zone]

captured_asteroids = []

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
          marker.position.horizontal_angle,type])
    return output

def get_nearest_asteroid():
    all_markers = get_seen_markers()
    asters = []
    ids = []
    for i in range(len(all_markers)):
        if all_markers[i][3] == 'asteroid' and all_markers[i][0] not in ids and all_markers[i][0] not in captured_asteroids:
            asters.append(all_markers[i])
            ids.append(all_markers[i][0])
    
    return sorted(asters,key=lambda x: (x[1]))[0] if len(asters) > 0 else [None,None,None,None]

   

def align(ID):
    sensitivity = 0.04
    camera_to_front_of_bot_distance = 400
    
    angle = 1
    while angle > sensitivity or angle < -sensitivity:
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
    return True 

def return_home():
    ID = None
    while ID is None:
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in [home_wall_markers[3]]:
                ID = i
                break
        if ID is None:
            rotate_right(1)
            robot.sleep(0.02)
            reverse(0.1)
            robot.sleep(0.01)
            stop_moving()
    approach(ID,600)
 
def deposit_into_spaceship():
    ID = None
    while ID is None:
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
    approach(ID)
    servo_board.servos[2].position = 1
    robot.sleep(1)
    while robot.arduino.pins[A4].analog_read() > 0.25 and robot.arduino.pins[A0].analog_read() > 0.05  and  robot.arduino.pins[A1].analog_read() > 0.05:
        forward(0.2)
        robot.sleep(0.1)
    stop_moving()
    servo_board.servos[0].position = -1
    servo_board.servos[1].position = -1
    robot.sleep(0.5)
    reverse(0.5)
    robot.sleep(1)
    stop_moving()
    grabber_normal_position()
    
 
def approach(ID,distance_of_approach=0):
    try:
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        dist = all_markers[seen_marker_ids.index(ID)][1]
        while dist > distance_of_approach:
            if not align(ID):
                break
            forward(0.5)
            all_markers = get_seen_markers()
            seen_marker_ids = [i[0] for i in all_markers]
            robot.sleep(0.1)
            dist = all_markers[seen_marker_ids.index(ID)][1]
        stop_moving()
        if ID in asteroids:
            captured_asteroids.append(ID)
            print(home_zone,': captured - ',captured_asteroids)
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
    while ID is None:
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in asteroids and i not in captured_asteroids:
                ID = i
                break
        if ID is None:
            rotate_left(1)
            robot.sleep(0.1)
            reverse(0.1)
            robot.sleep(0.01)
            stop_moving()


def clamp_spaceship():
    ID = None
    while ID is None:
        all_markers = get_seen_markers()
        seen_marker_ids = [i[0] for i in all_markers]
        for i in seen_marker_ids:
            if i in spaceships[home_zone]:
                ID = i
                break
        if ID is None:
            rotate_right(1)
            robot.sleep(0.02)
            reverse(0.1)
            robot.sleep(0.01)
            stop_moving()
    approach(ID,400)
    servo_board.servos[0].position = -1
    servo_board.servos[1].position = -1
    servo_board.servos[2].position = 0.5
    robot.sleep(1.5)
    while robot.arduino.pins[A4].analog_read() > 0.25 and robot.arduino.pins[A0].analog_read() > 0.05  and  robot.arduino.pins[A1].analog_read() > 0.05:
        forward(0.2)
        robot.sleep(0.1)
    stop_moving()
    servo_board.servos[2].position = -0.08
    robot.sleep(1)


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
                print(math.sqrt(nearest_aster[1]**2 + spaceship[1]**2 - (2*nearest_aster[1]*spaceship[1]*math.cos(abs(nearest_aster[2] - spaceship[2])))), abs(nearest_aster[2] - spaceship[2]))
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
    return_home()
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
            print(math.sqrt(nearest_aster[1]**2 + spaceship[1]**2 - (2*nearest_aster[1]*spaceship[1]*math.cos(abs(nearest_aster[2] - spaceship[2])))), abs(nearest_aster[2] - spaceship[2]))
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
        
    return_home()
    deposit_into_spaceship()

def scoop_asteroid_collection():
    for rep in range(3):
        continuing = True
        while continuing:    
            seek_asteroid()
            spaceships_seen = [i for i in get_seen_markers() if i[3][:9] == 'spaceship']
            nearest_aster = get_nearest_asteroid()
            continuing = False
            for spaceship in spaceships_seen:
                #THRESHOLD ANGLES AND DISTS FOR BEING DEEMED INSIDE A SHIP TO BE ADJUSTED
                print(math.sqrt(nearest_aster[1]**2 + spaceship[1]**2 - (2*nearest_aster[1]*spaceship[1]*math.cos(abs(nearest_aster[2] - spaceship[2])))), abs(nearest_aster[2] - spaceship[2]))
                if math.sqrt(nearest_aster[1]**2 + spaceship[1]**2 - (2*nearest_aster[1]*spaceship[1]*math.cos(abs(nearest_aster[2] - spaceship[2])))) > 600 or abs(nearest_aster[2] - spaceship[2]) > 0.3:
                    pass
                else:
                    captured_asteroids.append(nearest_aster[0])
                    print(nearest_aster[0],'captured by opponent')
                    continuing = True
            
        target_aster = get_nearest_asteroid()
        approach(target_aster[0])
        
        if rep < 2:
            forward(0.3)
            robot.sleep(0.5)
            stop_moving()
        else:
            forward(0.6)
            robot.sleep(0.9)
            stop_moving()
            
        if rep == 1:
            grab_asteroid()
            reverse(0.5)
            robot.sleep(0.2)
            rotate_right(0.3)
            robot.sleep(0.4)
            stop_moving()
  
    
    return_home()
    reverse(0.5)
    robot.sleep(0.6)
    rotate_left(0.3)
    robot.sleep(0.3)
    forward(0.5)
    robot.sleep(0.5)
    return_home()
    deposit_into_spaceship()

clamp_spaceship()

#TODO - make sure asteroid in grasp before moving on -NEEDS WORK MAYBE, currently only applies to standard collection
#Don't try to grab asteroids inside other spaceships -DONE
#Troubleshoot if stuck/don't go after other bots

#FINISHING
#MAKE SURE YOUR SPACESHIP IN YOUR ZONE
#KICK OUT EGG (maybe start by depositing egg in other ship)

