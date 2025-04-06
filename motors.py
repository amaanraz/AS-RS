import time
import RPi.GPIO as GPIO

PUL = 17  
DIR = 27  
ENA = 22 # Not in use

PUL_2 = 23
DIR_2 = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(PUL_2, GPIO.OUT)
GPIO.setup(DIR_2, GPIO.OUT)

# Set Direction (LOW --> CCW, HIGH --> CW)
GPIO.setup(DIR, GPIO.HIGH)
GPIO.setup(DIR_2, GPIO.HIGH)

delay = 0.008

# Debug variables
xcount = 0
ycount = 0

# Locations
# Boxes dictionary (box in shelf: [steps to get from home to box, steps to get from box to drop off])
boxes = {
    1: [200,600],
    2: [300,500],
    3: [400,400],
    4: [500,300],
    5: [600,200],
    6: [700,100]
}

def retrieveItem(shelf, box):
    # Move arm to the box position
    moveArmX(boxes[box][0])
    time.sleep(0.5)  

    # Hook the arm to the box
    hookArm()

    # Simulate picking up the item
    print(f"Retrieving item from shelf {shelf}, box {box}")

    # Move arm to the drop off position
    moveArmX(-boxes[box][1])
    moveArmX(-boxes[box][0])
    # moveArmY(-100)
    time.sleep(0.5)  

    # Bring back to home position
    # want to see in action before continuing

def hookArm():
    # Simulate hooking the arm to the box
    print("Hooking the arm to the box")
    moveArmY(-100)  # Move arm down to hook the box
    moveArmX(100)  # Move arm forward to hook the box
    moveArmY(200)  # Move arm up to lift the box



def moveArmX(steps):

    if steps < 0:
        GPIO.output(DIR, GPIO.LOW)
    else:
        GPIO.output(DIR, GPIO.HIGH)

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

    if steps < 0:
        GPIO.output(DIR_2, GPIO.LOW)
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
    moveArmX(-800)

    
    print("Xsteps: ", xcount)
    print("Ysteps: ", ycount)
    GPIO.cleanup()

except KeyboardInterrupt:
    print("Program interrupted by user")
    GPIO.cleanup()
    print("Xsteps: ", xcount)
    print("Ysteps: ", ycount)