import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
import speech_recognition as sr
import pyttsx3
import re

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E760')

DEFAULT_HEIGHT = 0.3
BOX_LIMIT = 0.5

deck_attached_event = Event()

logging.basicConfig(level=logging.ERROR)

position_estimate = [0, 0]
numbers = ""

# Initialize the recognizer
r = sr.Recognizer()

# Function to convert text to
# speech
def SpeakText(command):
	
	# Initialize the engine
	engine = pyttsx3.init()
	engine.say(command)
	engine.runAndWait()


def poshold(cf, t, z):
    steps = t * 10

    for r in range(steps):
        cf.commander.send_hover_setpoint(0, 0, 0, z)
        time.sleep(0.1)


def log_pos_callback(timestamp, data, logconf):
    # print(data)
    global position_estimate
    position_estimate[0] = data['stateEstimate.x']
    position_estimate[1] = data['stateEstimate.y']

def run_sequence(scf, sequence, base_x, base_y, base_z, yaw):
    cf = scf.cf

    for position in sequence:
        print('Setting position {}'.format(position))

        x = position[0] + base_x
        y = position[1] + base_y
        z = position[2] + base_z

        for i in range(50):
            cf.commander.send_position_setpoint(x, y, z, yaw)
            time.sleep(0.1)

    cf.commander.send_stop_setpoint()
    # Make sure that the last packet leaves before the link is closed
    # since the message queue is not flushed before closing
    time.sleep(0.1)

def goingup(z):
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        # We take off when the commander is created
                         with MotionCommander(scf) as mc:
                            mc.up(z)
                            time.sleep(1)

def param_deck_flow(_, value_str):
    value = int(value_str)
    # print(value)
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

def speech2fly(mc, x, y, z):
    while(1):
            
            # Exception handling to handle
            # exceptions at the runtime
            try:
                
                # use the microphone as source for input.
                with sr.Microphone() as source2:
                    cf = mc._cf
                    print('in microphone')
                    # wait for a second to let the recognizer
                    # adjust the energy threshold based on
                    # the surrounding noise level
                    r.adjust_for_ambient_noise(source2, duration=0.1)
                    print('out of microphone')
                    #listens for the user's input
                    audio2 = r.listen(source2)

                    
                    # Using google to recognize audio
                    MyText = r.recognize_google(audio2)
                    MyText = MyText.lower()
                    text=""
                    numbers=""
                    organisedText=[]
                    for i in MyText:
                        if(i.isdigit()):
                            numbers+=i
                        else:
                            text+=i

                    organisedText.append(text)
                    organisedText.append(numbers)
                   
                    if numbers == '':
                        numbers = z

                    numbers = int(numbers)
                    print(text)
                    print(numbers)

                    if ('up' in text) or ('top' in text):
                        z = numbers/100
                        mc.up(z)
                        print("going up!")
                    elif 'down' in text:
                        z = numbers/100
                        mc.down(z)
                        print("going down!")
                    elif ('forward' in text) or ('for' in text) or ('fort' in text):
                        x = numbers/100
                        mc.forward(x)
                        print("going forward!")
                    elif 'back' in text:
                        x = numbers/100
                        mc.back(x)
                        print("going back!")
                    elif ('turn' in text) or ('tourn' in text):
                        if('-' in text):
                            mc.turn_left(numbers)
                        else:
                            mc.turn_right(numbers)
                        print('turning')
                    elif ("left" in text) or ("last" in text):
                        y = numbers/100
                        mc.left(y)
                        print("going left!")
                    elif ("right" in text) or ("write" in text):
                        y = numbers/100
                        mc.right(y)
                        print("going right!")
                    elif 'land' in text:
                        print("landing")
                        mc.land()
                        exit()
                    else:
                        print("Didn't read what was said properly")
                        poshold(cf, t, z)
                     
                                
    
                    
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
                poshold(cf, t, z)

            except sr.UnknownValueError:
                print("unknown error occurred")
                poshold(cf, t, z)
                # move_box_limit(scf)
                logconf.stop()

    return x, y, z

def move_linear_simple(scf, x, y, z):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        while(1):
            x,y,z = speech2fly(mc, x, y, z)
            time.sleep(1)
        
    


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf
        scf.cf.param.add_update_callback(group='deck', name='bcFlow2',
                                         cb=param_deck_flow)
        time.sleep(1)

        logconf = LogConfig(name='Position', period_in_ms=10)
        logconf.add_variable('stateEstimate.x', 'float')
        logconf.add_variable('stateEstimate.y', 'float')
        scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(log_pos_callback)

        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            sys.exit(1)

        logconf.start()
        x = 0.0
        y = 0.0
        z = 0.2
        initial_yaw = 90 
        
        t = 1
        move_linear_simple(scf, x, y, z)
        
        