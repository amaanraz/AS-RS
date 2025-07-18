
import time
import RPi.GPIO as GPIO
import keyboard
from limit_switch_driver import LimitSwitch

# Arm 1test (PLAYGROUND)
PUL = 17
DIR = 27
ENA = 22 # Not in use

# Arm 2
PUL_2 = 23
DIR_2 = 24

# Lift
PUL_LIFT = 5
DIR_LIFT = 19

# Limit Switches
X_SWITCH = 12
Y_SWITCH = 16

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

delay = 0.00005
lift_delay = 0.01

# Debug variables
xcount = 0
ycount = 0
liftcount = 0

mm_to_inch = 0.0393701

# Configuration for step calculations (Side Gripper Configuration)
config = {
    'arm_center_offset': 57.15,         # mm from home to middle of the arm (2.25 inches)
    'first_box_center': 110,          # mm to center of first box (3.78 inches)
    'box_spacing': 114.3,               # mm between box centers (4.5 inches)
    'steps_per_mm_x': 39.96,            # steps per mm for X axis
    'steps_per_mm_y': 39.96,            # steps per mm for Y axis
    'box_height_from_initial': 50,      # mm to lift up to box height from initial position
    'hook_distance_mm': 30,             # mm to slide in sideways to hook the box
    'drop_off_height': 150,             # mm total height for safe drop-off clearance
    'steps_per_mm_lift': 8,             # not used in X calc
    'camera_position_x_mm': 457.2,      # 18 inches in mm (18 * 25.4)
    'drop_off_x_mm': 696,            # 4 feet in mm (4*304.8)
}


def calculate_steps(shelf_number, box_number, config):
    """
    Calculates step counts for moving to a given shelf and box using side gripper configuration.
    
    Side gripper sequence:
    1. Move X to box position (x_1)
    2. Move Y up to box height (y_1) 
    3. Move X sideways to hook the box (hook)
    4. Move Y up to clearance height (y_2_clearance) - half of drop-off height
    5. Move X to camera position (camera)
    6. Move Y up to full drop-off height (y_3_full)
    7. Move X to drop-off zone (drop_off)

    Args:
        shelf_number (int): The target shelf (1-indexed)
        box_number (int): The target box (1-indexed)
        config (dict): Contains all physical measurements and steps/mm

    Returns:
        tuple: (x_1, y_1, hook, y_2_clearance, camera, y_3_full, drop_off) - steps for each movement phase
    """

    # Phase 1: X movement to get beside the box
    box_center_mm = config['first_box_center'] + (box_number - 1) * config['box_spacing']
    x_1 = int(box_center_mm * config['steps_per_mm_x'])
    print(f"Phase 1 - X to box {box_number}: {box_center_mm:.2f}mm ({mm_to_inch*box_center_mm:.2f}inch) -> {x_1} steps")

    # Phase 2: Y movement up to box height from initial position
    y_1 = int(config['box_height_from_initial'] * config['steps_per_mm_y'])
    print(f"Phase 2 - Y to box height: {config['box_height_from_initial']:.2f}mm ({mm_to_inch*config['box_height_from_initial']:.2f}inch) -> {y_1} steps")

    # Phase 3: X movement sideways to hook the box
    hook = int(config['hook_distance_mm'] * config['steps_per_mm_x'])
    print(f"Phase 3 - X hook distance: {config['hook_distance_mm']:.2f}mm ({mm_to_inch*config['hook_distance_mm']:.2f}inch) -> {hook} steps")

    # Phase 4: Y movement up to clearance height (half of drop-off height from box height)
    clearance_height_mm = config['drop_off_height'] / 2
    clearance_lift_mm = clearance_height_mm - config['box_height_from_initial']
    y_2_clearance = int(clearance_lift_mm * config['steps_per_mm_y'])
    print(f"Phase 4 - Y to clearance height: additional {clearance_lift_mm:.2f}mm (total {clearance_height_mm:.2f}mm, {mm_to_inch*clearance_lift_mm:.2f}inch) -> {y_2_clearance} steps")

    # Phase 5: X movement from current position to camera position
    current_x_mm = box_center_mm + config['hook_distance_mm']  # Current X position after hooking
    camera_x_mm = config['camera_position_x_mm']
    camera = int((camera_x_mm - current_x_mm) * config['steps_per_mm_x'])
    print(f"Phase 5 - X to camera position: from {current_x_mm:.2f}mm to {camera_x_mm:.2f}mm ({mm_to_inch*(camera_x_mm - current_x_mm):.2f}inch) -> {camera} steps")

    # Phase 6: Y movement up to full drop-off height (from clearance to full height)
    full_lift_mm = config['drop_off_height'] - clearance_height_mm
    y_3_full = int(full_lift_mm * config['steps_per_mm_y'])
    print(f"Phase 6 - Y to full drop-off height: additional {full_lift_mm:.2f}mm (total {config['drop_off_height']:.2f}mm, {mm_to_inch*full_lift_mm:.2f}inch) -> {y_3_full} steps")

    # Phase 7: X movement from camera position to drop-off zone
    drop_off_x_mm = config['drop_off_x_mm']
    drop_off = int((drop_off_x_mm - camera_x_mm) * config['steps_per_mm_x'])
    print(f"Phase 7 - X to drop-off: from {camera_x_mm:.2f}mm to {drop_off_x_mm:.2f}mm ({mm_to_inch*(drop_off_x_mm - camera_x_mm):.2f}inch) -> {drop_off} steps")

    return x_1, y_1, -hook, y_2_clearance, camera, y_3_full, drop_off


def retrieveItem(self, shelf, box, instructions):
    """
    Retrieves an item using the 7-phase side gripper sequence:
    1. Move X to box position
    2. Move Y up to box height 
    3. Move X sideways to hook the box
    4. Move Y up to clearance height (half drop-off height)
    5. Move X to camera position
    6. Move Y up to full drop-off height
    7. Move X to drop-off zone
    """
    print(f"Retrieving item from shelf {shelf}, box {box}")
    
    # instructions = (x_1, y_1, hook, y_2_clearance, camera, y_3_full, drop_off)
    
    # Move to appropriate shelf height first
    self.lift(-shelves[shelf])
    time.sleep(1)
    
    # Phase 1: Move X to box position
    self.moveArmX(instructions[0])  # x_1
    time.sleep(1)
    
    # Phase 2: Move Y up to box height
    self.moveArmY(instructions[1])  # y_1
    time.sleep(1)
    
    # Phase 3: Hook the box (slide sideways)
    self.moveArmX(instructions[2])  # hook
    time.sleep(1)
    
    # Phase 4: Lift to clearance height (safety)
    self.moveArmY(instructions[3])  # y_2_clearance
    time.sleep(1)
    
    # Phase 5: Move to camera position
    self.moveArmX(instructions[4])  # camera
    time.sleep(1)
    # Camera can take photo here
    # TODO: call camera from qrreader + send to webapp

    # Phase 6: Lift to full drop-off height
    self.moveArmY(instructions[5])  # y_3_full
    time.sleep(1)
    
    # Phase 7: Move to drop-off zone
    self.moveArmX(instructions[6])  # drop_off
    time.sleep(1)
    
    print("Item retrieved and ready for drop-off")


def storeItem(self, shelf, box):
    print(f"Storing item to shelf {shelf}, box {box}")
    steps_x = calculate_steps(shelf, box, config) #TODO:move out make a global call
    self.moveArmX(-steps_x)
    time.sleep(1)
    # Unhook and other Y movements can be added here as needed
    # self.moveArmY(...)
    # self.moveArmX(...)
    # self.moveArmY(...)
    # Store
    self.lift(shelves[shelf])

def hookArm(self,box):
    print("Hooking the arm to the box")
    #hook (start from y init pos, and bring up to clearance position)
    steps_y = calculate_steps(0, box, config)[1]  #TODO:move out make a global call
    self.moveArmY(steps_y)
    time.sleep(1)


def lift(steps):
    global liftcount

    print("Moving lift: ", steps)

    for _ in range(steps):
        GPIO.output(PUL_LIFT, GPIO.HIGH)
        time.sleep(lift_delay)
        GPIO.output(PUL_LIFT, GPIO.LOW)
        time.sleep(lift_delay)

        liftcount += 1

def moveArmX(steps):
    global xcount

    # print("Moving X: ", steps)

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
    
    # print("Moving Y: ", steps)

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

def come_home(y_limit_pin, x_limit_pin):
    """
    Moves the Y axis down until the Y limit switch is pressed, then moves the X axis left until the X limit switch is pressed.
    Uses the LimitSwitch class for detection.
    """
    global xcount, ycount

    y_switch = LimitSwitch(y_limit_pin, name="Y Limit")
    x_switch = LimitSwitch(x_limit_pin, name="X Limit")

    print("Homing X axis...")
    # Move X left (negative direction) until X limit switch is pressed
    x_steps = 0
    while not x_switch.is_pressed():
        moveArmX(-10)  
        x_steps += 10
        # time.sleep(0.01)
    print("X axis homed.")

    # print("Homing Y axis...")
    # # Move Y down (negative direction) until Y limit switch is pressed
    y_steps = 0
    while not y_switch.is_pressed():
        moveArmY(-10)  # Move in small increments for safety
        y_steps += 10
        # time.sleep(0.01)
    print("Y axis homed.")

    # Optionally clean up just the pins used for limit switches
    y_switch.cleanup()
    x_switch.cleanup()

    print(f"Total Y steps traveled during homing: {y_steps} / {y_steps / config['steps_per_mm_x'] *  mm_to_inch} inch")
    print(f"Total X steps traveled during homing: {x_steps} / {x_steps / config['steps_per_mm_x'] * mm_to_inch} inch ")


instructions = calculate_steps(0, 2, config)  # Example call to calculate steps for shelf 0, box 1
# Example usage of the functions
print(instructions)

come_home(Y_SWITCH, X_SWITCH)

GPIO.cleanup()
