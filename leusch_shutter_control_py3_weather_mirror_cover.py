# shutter door - motor control gui


class gui():
    def on_exit(self):
        print ('you are now exiting')




# *******************************************************************************************
# start function definitions and click event functions **************************************

def click_button_open_door():
    if GPIO.input(GPIO_weather_event_input)==True and auto_door_close == True:
        return
    button_emergency_stop.configure(bg = "coral")
    button_emergency_stop.configure(text = "Emergency Stop") 
    global door_opened_flag
    global button_changed_flag
    global button_selection
    if door_opening_flag == False and door_closing_flag == False:
        if door_opened_flag == False:
 #           button_open_door.configure(background='#FFF59D')
            button_open_door.configure(background='gray85')
            button_close_door.configure(background='gray85')
            button_selection = 1
            button_changed_flag = True
        if door_opened_flag == True:
            print ("The shutter door is already open")

def click_button_close_door():
    button_emergency_stop.configure(bg = "coral")
    button_emergency_stop.configure(text = "Emergency Stop") 
    global door_closed_flag
    global button_changed_flag
    global button_selection
    global log_write_weather_event_flag
    global mirror_open_command_sent
    global mirror_open_after_id

    print("the value of log_write_weather_event_flag= ", log_write_weather_event_flag)
    if door_opening_flag == False and door_closing_flag == False:
        if door_closed_flag == False:
#            button_close_door.configure(background='#FFF59D')
            button_close_door.configure(background='gray85')
            button_open_door.configure(background='gray85')
            button_changed_flag = True
            button_selection = 2
            button_changed_flag = True
            listbox.insert(END,' ')
            listbox.insert(END,' ')
            listbox.insert(END,' Weather Event --- Close Doors')
                 # write to file
            with open("shutter_doors.log", "a") as file:
                file.write("  " )
                file.write("  " )
                file.write(" ----------------------------------------------------------------------------- \n" )
                file.write(time_string_complete + " -- Weather Event -- Shutter Doors Closing \n" )

            # close the mirror cover immediately on the close request itself
            # (not waiting for the doors to finish closing), exactly once per request
            mirror_cover_closed_led.configure(bg='lawn green')
            mirror_cover_opened_led.configure(bg='gray85')
            GPIO.output(GPIO_mirror_cover_output, False)
            _send_mirror_command(MIRROR_CLOSE_SCRIPT)
            mirror_open_command_sent = False  # re-arm so the next open cycle fires again
            # cancel a still-pending delayed open command so it can't fire
            # after this close request and reopen the mirror behind our back
            if mirror_open_after_id is not None:
                gui.after_cancel(mirror_open_after_id)
                mirror_open_after_id = None
        if door_closed_flag == True:
            print ("The shutter door is already closed")


def click_button_toggle_auto_close():
    global auto_door_close
    if auto_door_close == True:
        auto_door_close = False
        auto_close_doors_enabled_disabled_led.configure (text = "Auto Doors Close \n DISABLED")
        auto_close_doors_enabled_disabled_led.configure(bg='gray85')
        
    else:
        auto_door_close = True
        auto_close_doors_enabled_disabled_led.configure (text = "Auto Doors Close \n ENABLED")
        auto_close_doors_enabled_disabled_led.configure(bg="yellow") 

    print (" the value of auto_door_close ==", auto_door_close)
    
    



def click_button_emergency_stop():

    global door_opening_flag
    global door_closing_flag
    global door_opened_flag
    global door_closed_flag

    obj_PWM.ChangeDutyCycle(0)
        
    door_opening_flag = False
    door_opening_led.configure(background='gray85')
    door_closing_flag = False
    door_closing_led.configure(background='gray85')

    count = listbox.size()
    if count >= 25:
        listbox.delete(0, 5)

    listbox.insert(END,'--------------EMERGENCY STOPPED --------------')

            # write timestamp to listbox
    now = datetime.datetime.now()
    time_string = now.strftime("%d %B %Y, %H:%M:%S")
    time_string_complete = ("Timestamp ------ " +  time_string)
    listbox.insert(END, time_string_complete)
    
    # check the state of the limit switches and set the limit LED's accordingly
    if GPIO.input(GPIO_door_opened_input)==True: # read door open switch
        door_opened_flag = True
        door_opened_led.configure(background="lawn green")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Open')        
    else:
        door_opened_flag = False
        door_opened_led.configure(background="gray85")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Open')                        
    if GPIO.input(GPIO_door_closed_input) == True:
        door_closed_flag = True
        door_closed_led.configure(background="lawn green")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Closed' )              
    else:
        door_closed_flag = False
        door_closed_led.configure(background="gray85")
        listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Closed')
    
    button_emergency_stop.configure(bg = "red")
    button_emergency_stop.configure(text = "Emergency Stop Activated")

    # write to file

    with open("shutter_doors.log", "a") as file:
        file.write("  ----------------------------------------------------------------------------- \n" )
        file.write(time_string_complete + " -- Emergency Stop Activated -- \n" )  
        

                

def click_button_exit():
    global exit_flag
    exit_flag = True
    print (">")
    print (">") 
    print (">Stop All Tasks")
    gui.after(200, exit_now) # delay ending/distroying GUI for 200ms
    # to give enough time for all three tasks to stop.  If all three tasks
    # are not stopped before the GUI is distroyed, you will get console errors
    # "invalid command name" 



def exit_now():
    print(">GUI Stopped Gacefully")
    GPIO.cleanup()
    gui.destroy()
    
# end function definitions and click event functions ***********************************************
# **************************************************************************************************
# --
# --
# --
# ****************************************************************************************************
# start task *****************************************************************************************

def task():

    global button_selection
    global button_changed_flag
    global door_opening_flag
    global door_opened_flag
    global door_closing_flag
    global door_closed_flag
    global time_string
    global time_string_complete
    global mirror_open_command_sent
    global mirror_open_after_id



    global exit_flag


# open door or closed selection *********************************************************************************

    if button_changed_flag == True:
        
        if button_selection == 1: # select open door- offset from center increased 25% (50 + 10.625), was 50 + 8.5
            obj_PWM.ChangeDutyCycle(60.625)
            door_opening_led.configure(background='lawn green')
            door_closing_led.configure(background='gray85')
            
            count = listbox.size()
            if count >= 25:
                listbox.delete(0, 5)

                
            listbox.insert(END,'Shutter Doors Opening - In Process')
            listbox.insert(END,' ----')
            door_opening_flag = True         
        if button_selection == 2: # select close door- offset from center reduced another 25% (50 - 6.375), was 50 - 8.5
            obj_PWM.ChangeDutyCycle(43.625)
            door_opening_led.configure(background='gray85')
            door_closing_led.configure(background='lawn green')

            count = listbox.size()
            if count >= 25:
                listbox.delete(0, 5)
            
            listbox.insert(END,'Shutter Doors Closing - In Process')
            listbox.insert(END,' ----')
            door_closing_flag = True

# reset the door_opening_flag or door_closing_flag because the motor is no longer in motion,
# and set the motor to idle at 1.5ms pulse width   
    if door_opening_flag == True and door_opened_flag == True:
        obj_PWM.ChangeDutyCycle(0)
        door_opening_flag = False
        door_opening_led.configure(background='gray85')

        # write "doors open" to listbox
        listbox.insert(END,'Shutter Doors Are Open ------')        
        
        # write timestamp to listbox
        now = datetime.datetime.now()
        time_string = now.strftime("%d %B %Y, %H:%M:%S")
        time_string_complete = ("Timestamp ------ " +  time_string)
        listbox.insert(END, time_string_complete)


        # write to file
        with open("shutter_doors.log", "a") as file:
            file.write(" ----------------------------------------------------------------------------- \n" )
            file.write(time_string_complete + " -- Shutter Doors Are Open -- \n" )

        # open the mirror cover a couple seconds after the motor has actually
        # stopped (not synchronously here), so the blocking ssh round-trip
        # never delays the motor-stop response to the open limit switch
        if mirror_open_command_sent == False:
            mirror_cover_opened_led.configure(bg='lawn green')
            mirror_cover_closed_led.configure(bg='gray85')
            GPIO.output(GPIO_mirror_cover_output, True)
            mirror_open_after_id = gui.after(MIRROR_OPEN_DELAY_MS, _fire_pending_mirror_open)
            mirror_open_command_sent = True


    if door_closing_flag == True and door_closed_flag == True:
        obj_PWM.ChangeDutyCycle(0)
        door_closing_flag = False
        door_closing_led.configure(background='gray85')

        # write "doors close" to listbox        
        listbox.insert(END,"Shutter Doors Are Closed ---------------")
        
        # write timestamp to listbox
        now = datetime.datetime.now()
        time_string = now.strftime("%d %B %Y, %H:%M:%S")
        time_string_complete = ("Timestamp ------ " +  time_string)
        listbox.insert(END, time_string_complete)

        # write to file
        with open("shutter_doors.log", "a") as file:
            file.write("  ----------------------------------------------------------------------------- \n" )
            file.write(time_string_complete + " -- Shutter Doors Are Closed -- \n" )  

    button_changed_flag = False 


    if exit_flag == True:
#o ---only use the print statement for trouble shooting
# ----to ensure all the tasks are stopped and have not
# ----been reassigned, otherwise you will get "invalid command name" errors
#       print ("ending task")  
        return # the return statement revents the task from reassigning during shutdown
    gui.after(30, task)

# End task *************************************************************************************************
# ***********************************************************************************************************
# --
# --
# --
# ***********************************************************************************************************
#  start task2 ***********************************************************************************************

def task2():


    global door_opening_flag
    global door_closing_flag
    global first_boot_flag
    global door_opened_flag
    global door_closed_flag
    global button_selection
    global read_delay_index

    global exit_flag



# read the state of the limit switches one time after starting program,
# print to listbox and write to log file

    if first_boot_flag == False:
        door_opened_flag = False
        door_closed_flag = False
        print (">")
        print (">") 
        print (">Program Started")

        if GPIO.input(GPIO_door_opened_input)==True:        
            door_opened_flag = True
            door_opened_led.configure(background='lawn green')
        if GPIO.input(GPIO_door_closed_input) == True:
            door_closed_flag = True  
            door_closed_led.configure(background='lawn green')

        listbox.insert(END,' ----------------------------------------------------')
        listbox.insert(END,' First Boot Report:')
        now = datetime.datetime.now()
        time_string = now.strftime("%d %B %Y, %H:%M:%S")
        time_string_complete = ("Timestamp ------ " +  time_string)
        python_version_string_complete = ("Python Version - " + str(sys.version))
        python_version_parsed = python_version_string_complete [:23]
        listbox.insert(END, time_string_complete)
        listbox.insert(END,python_version_parsed)
        listbox.insert(END,' ')
        listbox.insert(END,'Shutter Door State *****')
                
        # write to file once on boot
        file_text_line_1 = ("Program First Boot " + "\n")
        file_text_line_2 = (time_string_complete + "\n")
        file_text_line_3 = (python_version_parsed + "\n")
                        
  
        with open("shutter_doors.log", "a") as file:
            file.write(" \n")
            file.write(" \n") 
            file.write("------------------------------------------------------------------------ \n")
            file.write("*********************************************************************** \n") 
            file.write(file_text_line_1)
            file.write(file_text_line_2)
            file.write(file_text_line_3)
            file.write(" \n")
            if door_opened_flag == True:
                file.write ("Shutter Door Status: Door is Open \n")
            if door_closed_flag == True:
                file.write ("Shutter Door Status: Door is Closed \n")
            file.write("************************************************************************ \n")    
            file.write("------------------------------------------------------------------------ \n")
            file.write(" \n")

        
        if door_opened_flag == True:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Open')
        else:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Open')


        if door_closed_flag == True:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Closed' )
        else:
            listbox.insert(END,' The Shutter Doors Sensor Reads --- Doors Not Closed')
        listbox.insert(END,' ------------------------------------------------------------')
        listbox.insert(END,'  ') 
            
                                      

        first_boot_flag = True            

# after initiating an opening or closing the shutter doors,
# continously read the limit switches and set flags when they are hit, then stop reading
# until another opening or closing is initiated

    if door_opening_flag == True:
        if GPIO.input(GPIO_door_closed_input) == False:
            door_closed_flag = False
            door_closed_led.configure(background="gray85")


        if GPIO.input(GPIO_door_opened_input)==True: # read door open switch
            door_opened_flag = True
            door_opened_led.configure(background='lawn green')
            # mirror-cover open command is fired from task() once the motor
            # has actually stopped, not from here -- see task()

    if door_closing_flag == True:
        if GPIO.input(GPIO_door_opened_input)== False:
            door_opened_flag = False
            door_opened_led.configure(background="gray85")
            
        if GPIO.input(GPIO_door_closed_input) == True:
            door_closed_flag = True   
            door_closed_led.configure(background='lawn green')

# periodically read the door_opoened and door_closed I/O inputs and set the door_opened and door_closed flags based on their state 
    if door_opening_flag == False and door_closing_flag == False:
        read_delay_index = read_delay_index + 1
        if read_delay_index > 10:  # creates a delay so the I/O devices are only read after the delay is met
          #  print("the read_delay_index = " + str(read_delay_index))  

            
            if GPIO.input(GPIO_door_opened_input)==True: # read door open switch
                door_opened_flag = True
                door_opened_led.configure(background="lawn green")

                

            else:
                door_opened_flag = False
                door_opened_led.configure(background="gray85")

                
                
            if GPIO.input(GPIO_door_closed_input) == True:
                door_closed_flag = True
                door_closed_led.configure(background="lawn green")
 
 
            else:
                door_closed_flag = False
                door_closed_led.configure(background="gray85")
                

   

                

            read_delay_index = 0  #reset index to start the delay over

    if exit_flag == True:
#o ---only use the print statement for trouble shooting
# ----to ensure all the tasks are stopped and have not
# ----been reassigned, otherwise you will get "invalid command name" errors
#       print ("ending tas2k")  
        return # the return statement revents the task from reassigning during shutdown
    gui.after(50, task2)    
    
# end task 2 **************************************************************
# ****************************************************************************************
# --
# --
# --
# ****************************************************************************************************************
# start task3 ****************************************************************************************************

def task3():

    global strobe
    global door_opening_flag
    global door_closing_flag
    global read_delay_index
    global read_delay_index_2 
    global weather_read_delay_index
    global exit_flag
    global log_write_weather_event_flag 

    
# start code to flash/blink the background lights as the moter is moving ************************
    if strobe == True:
        strobe = False
    else:
        strobe = True

    if door_opening_flag == True:
        if strobe == True:
            door_opening_led.configure(background='lawn green')
        else: door_opening_led.configure(background='yellow')

    if door_closing_flag == True:
        if strobe == True:
            door_closing_led.configure(background='lawn green')
        else: door_closing_led.configure(background='yellow')

    
        
# end code for flashing lights as the motor is moving ********************************************


# start code that reads weather event sensor every 10 times the task3 runs


    weather_read_delay_index += 1
    if weather_read_delay_index >5:
        weather_read_delay_index = 0
        if GPIO.input(GPIO_weather_event_input)==True:
            weather_event_indicator_led.configure(bg = "red")
            weather_event_indicator_led.configure(text = "Weather Event \n Triggered")
        else:
            weather_event_indicator_led.configure(bg = "gray85")
            weather_event_indicator_led.configure(text = "No Weather \n Event Detected")
            
        if GPIO.input(GPIO_weather_event_input)==True and auto_door_close == True: # read weather event
            if door_closed_flag == False:
                button_close_door.invoke()
          



# end code that reads weather event sensor every 10 times the task3 runs
        
#  test code of global vairiables, used for debugging only     *****
#    print ("task3")
#    print ("door_opening_flag = " +  str(door_opening_flag))
#    print ("door_closing_flag = " + str(door_closing_flag))
#    print ("door_opened_flag = " +  str(door_opened_flag))    
#    print ("door_closed_flag = " +  str(door_closed_flag))
#    print ("button_selection = " + str(button_selection))
#    print (" ")
# ******************************************************************

    if exit_flag == True:
#o ---only use the print statement for trouble shooting
# ----to ensure all the tasks are stopped and have not
# ----been reassigned, otherwise you will get "invalid command name errors"
#       print ("ending task3")  
        return # the return statement revents the task from reassigning during shutdown
    gui.after(150, task3)


# end task3 ******************************************************************************************
# *****************************************************************************************************
# --
# --
# --
# --
# *******************************************************************************************************
# start imports code ************************************************************************************

import sys
import time
from time import sleep
import datetime
import os
import RPi.GPIO as GPIO
from tkinter import *
import subprocess


# end imports code *************************************************************************************
# *****************************************************************************************************
# --
# --
# --
# --
# *********************************************************************************************************
# start declorations/assignments code for variables and constants **********************************************

global button_selection# indicates which button, open door or close, has been selected
global button_changed_flag# indicates an open or close door button has beed selected and to read that selection 
global door_opening_flag  # indicates a door opening process has been initiated and the motor is moving
global door_closing_flag  # indicates a door closing process has been initiated and the motor is moving
global door_opened_flag # indicates the door opened switch has activated and the doors are opened
global door_closed_flag # indicates the door closed switch has activated and the doors are closed
global first_boot_flag # for executing code only one time after starting the program
global strob # for flashing the door opening and door closing lights as the motor moves
global read_delay_index # allows to delay when reading the door opened and door\
global auto_door_close # this is set to True when a weather event triggers the door to close
global weather_read_delay_index # used as a index in task3 so the weather event GPIO is not read every time taks3 is invoked
global log_write_weather_event_flag # used so that a weather event flag is only logged to the text box and write file only once.
global mirror_open_command_sent # latches True once the mirror-open ssh command has been sent for the current open cycle, so it fires only once

global exit_flag # used for shutting down, to ensure all the tasks don't get
# reassigned once the program shutdown process has begun.  If this flag is set
# each one of the three tasks cannot be reassigned


# closed switches when do moving commands are present

# global declorations for constants
global PWM_output
global GPIO_door_opened_input
global GPIO_door_closed_input
global GPIO_PWM_output
global GPIO_weather_event_input
global GPIO_mirror_cover_output


# assign variables with initial values
door_opened_flag = False
door_closed_flag = False
button_selection = 0
button_changed_flag = False
door_opening_flag = False
door_closing_flag = False
door_opened_flag
door_closed_flag
first_boot_flag = False
strobe = False
read_delay_index = 0
exit_flag = False
auto_door_close = False
weather_read_delay_index = 0
log_write_weather_event_flag = False
mirror_open_command_sent = False



# assign constants with values
GPIO_door_opened_input = 16 # BCM GPIO number, constant
GPIO_door_closed_input = 20 # BCM GPIO number, constant
GPIO_weather_event_input = 21 # BCM GPIO number, constant
GPIO_PWM_output = 5 # BCM GPIO number, constant
GPIO_mirror_cover_output = 6 # BCD GPIO number, constant

# SSH key auth to the dome Pi -- replaces the old sshpass/plaintext-password
# path, which depended on sshpass being installed and is no longer used
DOME_SSH_KEY = os.path.expanduser('~/.ssh/id_ed25519_dome')
DOME_HOST = 'dome@192.168.1.6'
# the mirror cover mechanism itself needs its external 24V supply on to move --
# GPIO26 on the dome pi will toggle fine over ssh even with that supply off,
# with no error, it just won't physically move the cover
MIRROR_OPEN_SCRIPT = '/home/dome/device/launch_mirror_open.py'
MIRROR_CLOSE_SCRIPT = '/home/dome/device/launch_mirror_close.py'
MIRROR_OPEN_DELAY_MS = 2000 # wait this long after the motor stops before sending the open command
mirror_open_after_id = None # gui.after() id for the pending delayed open command, so it can be cancelled by a close request


def _fire_pending_mirror_open():
    global mirror_open_after_id
    mirror_open_after_id = None
    _send_mirror_command(MIRROR_OPEN_SCRIPT)


def _send_mirror_command(remote_script_path):
    try:
        subprocess.run(
            ['ssh', '-i', DOME_SSH_KEY, '-o', 'BatchMode=yes',
             '-o', 'StrictHostKeyChecking=accept-new', DOME_HOST,
             'python3', remote_script_path],
            timeout=10,
        )
    except Exception as e:
        print('Error running ssh command:', e)

# end decloations/assignments code for vairables and constants ****************************************
# *****************************************************************************************************
# --
# --
# --
# ******************************************************************************************************
#  start GPIO definitions/assignments ******************************************************************

# start setup GPIO outputs *********************************
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PWM_output, GPIO.OUT)
GPIO.setup(GPIO_mirror_cover_output, GPIO.OUT)
GPIO.output (GPIO_mirror_cover_output, False) # initialize with the mirror cover closed
  

# end setup GPIO outputs ************************************
# --
# --
# --
# start setup GPIO inputs ******************************************************
GPIO.setup(GPIO_door_opened_input, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) # door open
GPIO.setup(GPIO_door_closed_input, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) # door close
GPIO.setup(GPIO_weather_event_input, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) # weather event
# end setup GPIO inputs ******************************************************


# end GPIO definitions/assignments ***********************************************************************
# ********************************************************************************************************
# --
# --
# --
# ********************************************************************************************************
# start create PWM Object ******************************************************************************

obj_PWM = GPIO.PWM(5,350) #define GPIO output a GPIO 5, and an output frequency of 333Hz

obj_PWM.start(0) # starts the PWM output with a duty cycle of %0 duty cycle, This essentially ititializes
# the program applying no signal to the motor controller

# end create PWM object ************************************************************************************
# ***********************************************************************************************************
# --
# --
# --
# ************************************************************************************************************
# start create gui *******************************************************************************************

gui = Tk()
topFrame = Frame(gui)
topFrame.pack
gui.geometry('575x920+400+200')
gui.title('test app')
gui.configure(background='#626567')
gui.resizable(False, False)  # disables resizing both ways


# start code - console open and close doors boarder frames and weather event control boarder frames
canvas = Canvas(gui, width=575, height=900, bg="#626567", highlightthickness=0)
rect1 = canvas.create_rectangle(31, 40, 262, 125, outline="lightgreen", width=3, fill="")
rect2 = canvas.create_rectangle(275, 40, 507,125, outline="lightgreen", width=3, fill="")

rect3 = canvas.create_rectangle (66, 630, 457, 715, outline="lightgreen", width=3, fill="")

rect4 = canvas.create_rectangle(140, 730, 384, 819, outline="lightgreen", width=3, fill="")

canvas.pack()
# end code - console open and close doors boarder frames and weather event control boarder frames









# end create gui *********************************************************************************************
# *************************************************************************************************************
# --
# --
# --
# *************************************************************************************************************
# start create buttons ****************************************************************************************

button_open_door = Button(text ='Open Shutter \n Doors', width = '8', height ='4', command=click_button_open_door)
button_open_door.configure(bg = "white")
button_open_door.place(x=280,y=50)

button_close_door = Button(text ='Close Shutter \n Doors', width = '8', height ='4', command=click_button_close_door)
button_close_door.configure(bg = "white")
button_close_door.place(x=40,y=50)

button_exit = Button(text ='Exit', width = '12', height ='3', command=click_button_exit)
button_exit.configure(bg = "gray85")
button_exit.place(x=354,y=840)


button_emergency_stop = Button(text ='Emergency Stop', width = '23', height ='3',command=click_button_emergency_stop)
button_emergency_stop.configure(bg = "coral")
button_emergency_stop.place(x=40,y=840)

button_toggle_auto_close = Button(text ='TOGGLE \n Weather Event \n Auto Doors Close', width = '12', height ='4',command=click_button_toggle_auto_close)
button_toggle_auto_close.configure(bg = "gray85")
button_toggle_auto_close.place(x=74,y=638)




# end create buttons *******************************************************************************************
# **************************************************************************************************************
# --
# --
# --
# **************************************************************************************************************
# start create leds objects *************************************************************************************

door_opening_led = Button(text = "Opening Doors", width = '11', height = '1')
door_opening_led.place (x=380, y=55)
door_opening_led.configure(bg = "gray85")

door_closing_led = Button(text = "Closing Doors", width = '11', height = '1')
door_closing_led.place (x=138, y=55)
door_closing_led.configure(bg = "gray85")


door_opened_led = Button(text = "Doors Are Open", width = '11', height = '1')
door_opened_led.place (x=380, y=88)

door_closed_led = Button(text = "Doors Are Closed", width = '11', height = '1')
door_closed_led.place (x=138, y=88)

auto_close_doors_enabled_disabled_led = Button(text = "Auto Doors Close \n DISABLED", width = '12', height = '4')
auto_close_doors_enabled_disabled_led.place (x=208, y=638)

weather_event_indicator_led = Button(text = "No Weather \n Event Detected", width = '10', height = '4')
weather_event_indicator_led.place (x=341, y=638)
weather_event_indicator_led.configure(bg = "gray85")


mirror_cover_opened_led = Button(text = "Mirror Cover\n Opened", width = '10', height = '4')
mirror_cover_opened_led.place (x=268, y=740) 
mirror_cover_opened_led.configure(bg = "gray85")


mirror_cover_closed_led = Button(text = "Mirror Cover\n Closed", width = '10', height = '4')
mirror_cover_closed_led.place (x=148, y=740) 
mirror_cover_closed_led.configure(bg = "gray85")



# end create leds ***********************************************************************************************
# ****************************************************************************************************************
# --
# --
# --
# *****************************************************************************************************************
# start create listbox ************************************************************************************************

listbox = Listbox(gui, width = '60', height = '30')
listbox.place(x=33,y=150)
listbox.configure(background='#000000')
listbox.configure(fg='#66FF00')

 # end create listbox ************************************************************************************************
# ********************************************************************************************************************
# --
# --
# --
# *********************************************************************************************************************
# start code that calls all task functions ****************************************************************************



gui.after(30, task)
gui.after(50, task2)
gui.after(150, task3)
gui.protocol("WM_DELETE_WINDOW", exit_now)
gui.mainloop()

# end code that calls all task funcitons *********************************************************************************
# *************************************************************************************************************************
# --
# --
# --

