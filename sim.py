import time
import RPi.GPIO as GPIO
import keyboard

# Arm 1
PUL = 17
DIR = 27
ENA = 22 # Not in use

# Arm 2
PUL_2 = 23
DIR_2 = 24

# Lift
PUL_LIFT = 26
DIR_LIFT = 19

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(PUL_2, GPIO.OUT)
GPIO.setup(DIR_2, GPIO.OUT)
GPIO.setup(PUL_LIFT, GPIO.OUT)
GPIO.setup(DIR_LIFT, GPIO.OUT)

# Set Direction (LOW --> CCW, HIGH --> CW)
GPIO.output(DIR, GPIO.HIGH)
GPIO.output(DIR_2, GPIO.HIGH)

delay = 0.00025
lift_delay = 0.0005

# Debug variables
xcount = 0
ycount = 0
liftcount = 0

# Locations
# Boxes dictionary (box in shelf: [steps to get from home to box, steps to get from box to drop off])
boxes = {
    1: [200,600],
    2: [425,2480],
    3: [970,1820],
    4: [1550,1160],
    5: [600,200],
    6: [700,100]
}

# steps from init pos to shelf # (init pos - shelf 1 lined up)
shelves = {
    1: 0,
    2: 7515,
    3: 9940,
    4: 0 #unknown
}
def retrieveItem(shelf, box):
    # picking up the item
    print(f"Retrieving item from shelf {shelf}, box {box}")

    lift(-shelves[shelf])
    time.sleep(1)
    moveArmX(8*boxes[box][0])
    time.sleep(1)
    moveArmY(8*965) # constant val
    time.sleep(1)

    #hook
    hookArm()

    #drop off
    moveArmX(8*boxes[box][1])

def storeItem(shelf, box):
    print(f"Retrieving item from shelf {shelf}, box {box}")
    moveArmX(-8*boxes[box][1])
    time.sleep(1)

    #unhook
    moveArmY(8*985)
    time.sleep(1)
    moveArmX(-8*220)
    time.sleep(1)
    moveArmY(-8*965)
    time.sleep(1)
    
    #store
    moveArmX(-8*boxes[box][0])
    time.sleep(1)
    lift(shelves[shelf])

def hookArm():
    print("Hooking the arm to the box")
    #hook
    moveArmX(8*220)
    time.sleep(1)
    moveArmY(-8*965)
    time.sleep(1)


def lift(steps):
    global liftcount

    print("Moving lift: ", steps)

    if steps < 0:
        GPIO.output(DIR_LIFT, GPIO.LOW)
    else:
        GPIO.output(DIR_LIFT, GPIO.HIGH)

    steps = abs(steps)

    for _ in range(steps):
        GPIO.output(PUL_LIFT, GPIO.HIGH)
        time.sleep(lift_delay)
        GPIO.output(PUL_LIFT, GPIO.LOW)
        time.sleep(lift_delay)

        liftcount += 1

def moveArmX(steps):
    global xcount

    print("Moving X: ", steps)

    if steps < 0:
        GPIO.output(DIR, GPIO.LOW)
        GPIO.output(DIR_2, GPIO.LOW) 
    else:
        GPIO.output(DIR, GPIO.HIGH)
        GPIO.output(DIR_2, GPIO.HIGH)

    steps = abs(steps)

        for _ in range(steps):
        GPIO.output(PUL, GPIO.HIGH)
        GPIO.output(PUL_2, GPIO.HIGH)
        time.sleep(delay)  # Pulse width
        GPIO.output(PUL, GPIO.LOW)
        GPIO.output(PUL_2, GPIO.LOW)
        time.sleep(delay)  # Pulse interval

        xcount += 1

def moveArmY(steps):
    global ycount
    
    print("Moving Y: ", steps)

    if steps < 0:
        GPIO.output(DIR, GPIO.HIGH)
        GPIO.output(DIR_2, GPIO.LOW)
    else:
        GPIO.output(DIR, GPIO.LOW)
        GPIO.output(DIR_2, GPIO.HIGH)

    steps = abs(steps)

    for _ in range(steps):
        GPIO.output(PUL, GPIO.HIGH)
        GPIO.output(PUL_2, GPIO.HIGH)
        time.sleep(delay)  # Pulse width
        GPIO.output(PUL, GPIO.LOW)
        GPIO.output(PUL_2, GPIO.LOW)
        time.sleep(delay)  # Pulse interval

        ycount += 1


# Run the code
try:
    x = 425 #1550  #970
    drop_x = 2480 #1160 #1820
    lift_y = 9940
    
    retrieveItem(3,2)
    #lift(-lift_y)
    #time.sleep(1)
    #moveArmX(8*x)
    #time.sleep(1)
    #moveArmY(8*965)
    #time.sleep(1)
    #hook
    #moveArmX(8*220)
    #time.sleep(1)
    #moveArmY(-8*965)
    #time.sleep(1)

    #drop off
    #moveArmX(8*drop_x)
    #time.sleep(1)

    #Return
    #moveArmX(-8*drop_x)
    #time.sleep(1)
    #moveArmY(8*985)
    #time.sleep(1)
    #moveArmX(-8*220)
    #time.sleep(1)
    #moveArmY(-8*965)
    #time.sleep(1)
    #moveArmX(-8*x)
    #time.sleep(1)
    #lift(lift_y)
    
    time.sleep(10)
    storeItem(3,2)
    
#    moveArmY(-400) # Testing - remove after

#    while True:
#        key = input("Enter W/A/S/D: ").lower()
#        handle_input(key)

    print("Xsteps: ", xcount)
    print("Ysteps: ", ycount)
    print("Lift: ", liftcount)
    
except KeyboardInterrupt:
    print("Program interrupted by user")
    #moveArmY(-ycount)
    GPIO.cleanup()
    print("Xsteps: ", xcount)
    print("Ysteps: ", ycount)
    print("Lift: ", liftcount)

GPIO.cleanup()
