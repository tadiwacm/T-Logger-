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
from time import sleep

#global variables
global delay #used to store and  set the delay
global runtime #stores the program rutime


#setup mode
GPIO.setmode(GPIO.BCM)

#initialise the button pins and buzzer pin
buttonPin=17   #the button pin for turning logging on/off
buttonPin2=27  #the button pin for switching between time delays
buzzer=22

#Set the buttons as Pull-Up buttons
GPIO.setup(buttonPin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(buttonPin2,GPIO.IN,pull_up_down=GPIO.PUD_UP)


# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)



# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 1
chan = AnalogIn(mcp, MCP.P1)

#setup buzzer as output
GPIO.setup(buzzer,GPIO.OUT)

#setup global variables
global start
global startlog


#setup pins
def setup():
    
    #global values reset
    global delay #refer to the global value of delay
    global startlog #refer to the global value of startlog
    delay=5 #set delay to be 5
    startlog=0 #turn off logging
    #Initialise buzzrr to be off
    GPIO.output(buzzer,GPIO.HIGH)
    
    #Print headings before logging starts
    str = ('Time',"Sys Timer", "Temp")
    print("{0: <20} {1: <20} {2: <20}".format(*str))
   

def button_pressed():
    global memory #this stores the string that will be sent to the EEPROM
    #set delay to 5 seconds
    delay=5
    
    #refer to buzzer
    global buzzer
    
    #create threads
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
	  
      #setup the "output" string that willbe saved to the EEPROM.
      output=str(mtime+runtime+str(temp))
      
      #create variable which will be used to extract seconds from runtime so as to calculate time to trigger buzzer
      buzzertime=int(str(runtime)[5:7])
      
      if(buzzertime%20==0): #check if runtime has reached a multiple of 20 secons
          GPIO.output(buzzer,GPIO.LOW)#set GPIO to low to trigger buzzer
          sleep(0.5) # Delay in seconds
          GPIO.output(buzzer,GPIO.HIGH)#set GPIO to high to stop buzzer
    
      #this for loop saves the characters of the word "output" to the EEPROM which saves our logging data to EEPROM
      for i in range (17):
       EPROM.write_byte(i,ord(output[i]))#write logging information to EEprom
      
      
    
    
    
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
    
    if(startlog==0):#check whether to start/stop logging
        clear = lambda: os.system('clear')#clear shell
        print("Logging has been stopped!")#printout logging stopped message
    
    
    
#add an event listener to check whether the start/stop logging button has been pressed
GPIO.add_event_detect(buttonPin,GPIO.FALLING,callback=run_program,bouncetime=700)



if __name__ == "__main__":
    #setup the environment
    setup()
   

    while True:
        pass

