import busio
import digitalio
import board
import threading
import datetime
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO
import time
import ES2EEPROMUtils
import os
EPROM= ES2EEPROMUtils.ES2EEPROM()
import blynklib
import requests
from threading import Thread
from time import sleep

#setup blynk 
BLYNK_AUTH = '<Rus-0nPoaOtM8Kk5T9PFup1PyfeEPEcy>' #insert your Auth Token here
# base lib init
blynk = blynklib.Blynk(BLYNK_AUTH)

#global variables
global delay #used to store and  set the delay
global runtime #stores the program rutime


#setup mode
GPIO.setmode(GPIO.BCM)

#initialise the button and buzzer pins
buttonPin=17   #the button pin for turning logging on/off
buttonPin2=27  #the button pin for switching between time delays
buzzer=22

#Disable warnings (optional)
#GPIO.setwarnings(False)

#Set the buttons as Pull-Up buttons
GPIO.setup(buttonPin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(buttonPin2,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#setup buzzer as output
GPIO.setup(buzzer,GPIO.OUT)

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)



# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 1
chan = AnalogIn(mcp, MCP.P1)

#define globals


global start
global startlog


#setup pins
def setup():
    
    #global values reset
    global delay #refer to the global value of delay
    global startlog #refer to the global value of startlog
    #global buzzer #refer to the buzzer pin
    delay=5
    startlog=0
    GPIO.output(buzzer,GPIO.HIGH)
    #Print headings before logging starts
    str = ('Time',"Sys Timer", "Temp")
    print("{0: <20} {1: <20} {2: <20}".format(*str))
    

# register handler for Virtual Pin V10,V11 and V12 reading by Blynk App.
# when a widget in Blynk App asks Virtual Pin data from server within given configurable interval (1,2,5,10 sec etc) 
# server automatically sends notification about read virtual pin event to hardware
# this notification captured by current handler 
@blynk.handle_event('read V10')
@blynk.handle_event('read V11')
@blynk.handle_event('read V12')
@blynk.handle_event('read V13')

def button_pressed():
    global memory #this stores the string that will be sent to the EEPROM
    #set delay
    global delay
    global buzzer
    
    #create threads
    blynk_thread=Thread(target=call_blynk_run)
    blynk_thread.start()
    thread = threading.Timer(delay, button_pressed)
    thread.daemon = True #thread.daemon = True # Daemon threads exit when the program does
    thread.start()

    if(startlog==1): #check whether to log or not
        
      #convert the reading to the temperature value in degrees
      temp = round((chan.voltage-0.5)/0.01)
	  
      #create and initialise variable for storing the CPU time to be printed out
      mtime=time.strftime('%H:%M:%S')
      
      #calculate runtime using the datetime library
      end=datetime.datetime.now()
      runtime=str((end-start))
      runtime=runtime.split(".")[0] #extract millisdeconds from the runtime reading
    
   
    
      #printout the time; system runtime and temperature to the console. 
      print("{0: <20} {1: <20} {2: <20} ".format(mtime,runtime,str(temp)+" C"))
      
      
      #create variable which will be used to extract seconds from runtime so as to calculate time to trigger buzzer
      buzzertime=int(str(runtime)[5:7])
      
      if(buzzertime%20==0): #check if runtime has reached a multiple of 20 secons
          GPIO.output(buzzer,GPIO.LOW)#set GPIO to low to trigger buzzer
          #print( "Buzzer!")
          sleep(0.5) # Delay in seconds
          GPIO.output(buzzer,GPIO.HIGH)#set GPIO to high to stop buzzer
      
      #setup the "output" string that willbe saved to the EEPROM.
      output=str(mtime+runtime+str(temp))
      

      # send values to Virtual Pins and store it in Blynk Cloud
      blynk.virtual_write(10, temp)#send temperature to blynk
      blynk.virtual_write(11,mtime)#send CPU time to blynk
      blynk.virtual_write(12, runtime)#send program runtime to blynk
      blynk.virtual_write(13, "System is logging")#send logging message to blynk
      
    
      #this for loop saves the characters of the word "output" to the EEPROM which saves our logging data to EEPROM
      for i in range (17):
       EPROM.write_byte(i,ord(output[i]))#write the logging data to the EEProm
      
      
    
	 
      
def call_blynk_run():
    while True:
        blynk.run()#call blynk.run to send write values to App
    
def run_program(channel):
    #variable to store the program start time
    global start
    
    #variable startlog to set and track logging
    global startlog
    
    #initialise program start-time
    start= datetime.datetime.now()
    
    #check to turn on/off logging
    if(startlog==1):
        startlog=0
    elif startlog==0:
        startlog=1
    
    #call the threads to run and start logging or stop logging
    button_pressed()
    
    if(startlog==0):
        clear = lambda: os.system('clear')#clear terminal
        print("Logging has been stopped!")##print logging stopped message
        blynk.virtual_write(13, "Logging has been Stopped")#send logging message to blynk
        
def change_delay(channel):
    #refer to the global variable of delay
    global delay
    
    #set or change the delay appropriately
    if(delay==5):
        delay=2
    elif(delay==2):
        delay=10
    elif(delay==10):
        delay=5
    
    #call the function to instruct the threads to start logging with the set delay 
    button_pressed()
    



 
 
#add an event listener to check whether the start/stop logging button has been pressed
GPIO.add_event_detect(buttonPin,GPIO.FALLING,callback=run_program,bouncetime=900)
GPIO.add_event_detect(buttonPin2,GPIO.FALLING,callback=change_delay,bouncetime=2000)



if __name__ == "__main__":
    
    #setup the environment
    setup()
    
    while True:
     pass


