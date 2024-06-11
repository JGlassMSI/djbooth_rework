#Import for GUI
import tkinter as tk
import tkinter.scrolledtext as st
from sys import exit
import time

#Import for HR
import serial
import RPi.GPIO as GPIO
import socket
import threading

#Station Number as string use single quotes ex. '"id": X'
STA='"id":2'
#Enable Debug messages
Debug=True #Generic Debug for console
Sdebug=False #Arduino/Serial Debug
aPrint=True #Disables printing of arduino values
hPrint= False #Disables printing of Handle values
DebugTemp=False #Used to hold value of Debug serial during setup
# UDP Parmaters
UDP_IP = "192.168.10.6"#IP address to send to
UDP_PORT = 16501 #Port to send to
MESSAGE = b"Message" #Message Var
# UDP_IPlocal = "192.168.10.32"#IP address to send to
# UDP_PORTlocal = 65500 #Port to send to
# MESSAGElocal = b"Message" #Message Var
#Set Up GPIO
GPIO.setmode(GPIO.BCM)
HRInput=4 # GPIO pin 4
GPIO.setup(HRInput, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#Vars for handles
lasttime=0.0
pHR=0 #Past HR value for limits
HRmin=0 #HR Min Value
HRmax=0 #HR max Value
aTBB=[] #Time between beats list for average
hdActive=False #Handle active flag
HR=0 # HR Value
sHR="" #String HR Value

#Vars for Pulse OX
output = ""
iHR=0 #Interger heart rate from Pulse-OX
suActive=False # setup active flag

lGui = [] #List to write to GUI

Running=True #Variable for running loop

#Gui Subroutines

def dSdebug():
    global Sdebug
    if Sdebug:
        Sdebug=False
        print("Serial Debug Disabled")
        text_box.insert(tk.END, "\nSerial Debug Disabled")
        text_box.see(tk.END)
        bSdebug.config(text="Serial Debug Off")
        bSdebug.config(bg="blue")
    else:
        Sdebug=True
        print("Serial Debug Enabled")
        text_box.insert(tk.END, "\nSerial Debug Enabled")
        text_box.see(tk.END)
        bSdebug.config(text="Serial Debug On")
        bSdebug.config(bg="red")
    
def dFdebug():
    global aPrint
    if aPrint:
        aPrint=False
        print("Finger Debug Disabled")
        text_box.insert(tk.END, "\nFinger Debug Disabled")
        text_box.see(tk.END)
        bFdebug.config(text="Finger Debug Off")
        bFdebug.config(bg="blue")
    else:
        aPrint=True
        print("Finger Debug Enabled")
        text_box.insert(tk.END, "\nFinger Debug Enabled")
        text_box.see(tk.END)
        bFdebug.config(text="Finger Debug On")
        bFdebug.config(bg="red")

def dHdebug():
    global hPrint
    if hPrint:
        hPrint=False
        print("Handle Debug Disabled")
        text_box.insert(tk.END, "\nHandle Debug Disabled")
        text_box.see(tk.END)
        bHdebug.config(text="Handle Debug Off")
        bHdebug.config(bg="blue")
    else:
        hPrint=True
        print("Handle Debug Enabled")
        text_box.insert(tk.END, "\nHandle Debug Enabled")
        text_box.see(tk.END)
        bHdebug.config(text="Handle Debug On")
        bHdebug.config(bg="red")
    
def Clear():
    text_box.delete(1.0,tk.END)
    text_box.see(tk.END)
    
def Close():
    global Running
    Running=False
#     window.destroy()
#     exit(0)
#     exit("Program Closed")

#Handles subroutines
def newtimer(sec):#Timer to reset handles after 4 beats or 4 seconds
    global hdActive
    global hPrint
    hdActive=True
#     msg="hdActive"
#     sock.sendto(msg.encode('utf-8'),(UDP_IP,UDP_PORT))
    sec=(sec*4)
    if sec > 4: sec=4
    if hPrint:print("Timer Sec: ",sec)
    if hPrint:GuiList("Timer Sec: "+str(sec))
    global timrHR
    if timrHR.is_alive():
        if hPrint:print("Running")
        if hPrint:GuiList("Running")
        timrHR.cancel()
        timrHR=threading.Timer(sec,reset)
        timrHR.start()
    else:
        if hPrint:print("Stopped")
        if hPrint:GuiList("Stopped")
        timrHR=threading.Timer(sec,reset)
        timrHR.start()

def reset():
    global HRmin
    global HRmax
    global hdActive
    global aTBB
    hdActive=False
#     msg="hdActive NOT"
#     sock.sendto(msg.encode('utf-8'),(UDP_IP,UDP_PORT))
    aTBB=[] #Resets TBB list
    HRmin=HRmax=0 #Resets MIN/MAX Values
    if hPrint:print("Time up")
    if hPrint:GuiList("Time up")

def HRlimits(HRLim):
    global pHR
    return True
    HRU=(pHR+10)
    HRL=(pHR-10)
    if hPrint:
        print ("HRU: ",HRU)
        print ("HRL: ",HRL)
        GuiList("HRU: "+str(HRU))
        GuiList("HRL: "+str(HRL))
    if HRLim>30 and HRLim<200 and HRLim>HRL and HRLim<HRU:
        pHR=HRLim
        a=True
        return (a)
    else:
        pHR=HRLim
        if hPrint:print("HR OOL! HR: ",HRLim,"\n")
        if hPrint:GuiList("HR OOL! HR: "+str(HRLim))
        a=False
        return (a)
    
def HRminmax(HRmm):#Removes out of limit readings
    global HRmin
    global HRmax
    if HRmin==0 and HRmax==0:HRmin=HRmax=HRmm
    if HR<HRmin: HRmin=HRmm
    if HR>HRmax: HRmax=HRmm
    if hPrint:print("HRmin= ",HRmin," HRmax= ",HRmax,"\n")
    if hPrint:GuiList("HRmin= "+str(HRmin)+" HRmax= "+str(HRmax)+"\n")
    
def rTrig(channel):
    global lasttime
    global pHR
    global aTBB
    global HR
    global sHR
    global iHR
    HR = 0
    print("iHR = "+str(iHR))
    print("lasttime= "+str(lasttime))
    if not iHR>0:
        if lasttime==0:
            lasttime=time.time()
        else:
            if hPrint:
                print("HB Dectected")
                GuiList("\nHB Dectected")
            now = time.time()
            TBB=now-lasttime
            if hPrint:print ("TBB: ",TBB)
            if hPrint:GuiList("TBB: "+str(TBB))
#             if TBB>2:
#                 lasttime=now
#                 return
            if len(aTBB)>3: aTBB.pop(0)#Remove first item if list of greater then 3
            aTBB.append(TBB) #Append current TBB to list
            if hPrint:print(aTBB)
            if hPrint:GuiList(str(aTBB)[1:-1])#converts list to string and adds to GUI print
            if len(aTBB)==4: #Wait till 4 beats are captured
                avTBB= ((aTBB[0]+aTBB[1]+aTBB[2]+aTBB[3])/4)#Take average TBB
                if hPrint:print ("AVG TBB: ",avTBB) #Print Average
                if hPrint:GuiList("AVG TBB: "+str(avTBB)) #GUI print average
                HR= int(round(((15/avTBB)*4))) #Rounded Average to BPM
                fHR= (15/avTBB)*4 #Floating average to BPM
                if hPrint:print ("fHR: ",fHR)#Print floating average
                if hPrint:GuiList("fHR: "+str(fHR)) #GUI Print average
            lasttime=now
            HR= int(HR)
            sHR= str(HR)
#             sHR= STA + sHR + "\n"
            newtimer(TBB)
            if HRlimits(HR):
                if hPrint:print("Heart Rate:",HR)
                if hPrint:GuiList("Heart Rate:"+str(HR))
                HRminmax(HR)
#                 print(sHR)
                sUDPmessage='{'+STA+',"state": "present","heartrate": '+sHR+',"saturation": 0,"confidence": 0,"TBB": '+str(TBB)+'}'
#                 print(sUDPmessage)
                sock.sendto(sUDPmessage.encode('utf-8'),(UDP_IP,UDP_PORT))
                #sock.sendto(sUDPmessage.encode('utf-8'),(UDP_IPLocal,UDP_PORTLocal))

#Serial subroutine
def sRead():
    global output
    global Sdebug
    global DebugTemp
    global aPrint
    global iHR
    global suActive
    global sHR
    global HR
    CF="0"
    O2="0"
#     global HR 
#     while output != "":
    output = ser.readline().decode("utf-8")
    if output != "":
        if "SETUP function" in output:
            DebugTemp=Sdebug
            Sdebug=True
            suActive=True
            if Debug:print("Setup Function triggered")
            GuiList("Setup Function triggered")
        elif "Setup Complete" in output:
            Sdebug=DebugTemp
            suActive=False
            print(output)#prints "Setup Complete" line from AD
            GuiList(output)
            if Debug:print("Setup Complete Triggered")
        if Sdebug:
            print(output)
            GuiList(output)
            if Debug:print("Standard print")
            
        if not hdActive and not suActive:
            if "Heartrate: " in output:
                start = (output.find(" "))+1
                end = len(output)
                if Debug:print("Start number-HR",start)
                if Debug:print("End Number-HR",end)
                sHR=(output[start:end])
                sHR=sHR.strip()
                if aPrint:print("HR=",sHR)
                if aPrint:GuiList("HR="+str(sHR))
                iHR=int(sHR)
                HR=iHR
                DebugTesting=iHR
                if iHR>0:
                    message="HR= "+sHR
                    print(message)
                    GuiList(message)
#                     sock.sendto(message.encode('utf-8'),(UDP_IP,UDP_PORT))
            elif "Confidence: " in output:
                start = (output.find(" "))+1
                end = len(output)
                if Debug:print("Start number-CO",start)
                if Debug:print("End Number-CO",end)
                CF=(output[start:end])
                CF=CF.strip()
                if aPrint:print("CF=",CF)
                if aPrint:GuiList("CF="+str(CF))
            elif "Oxygen: " in output:
                start = (output.find(" "))+1
                end = len(output)
                if Debug:print("Start number-O2",start)
                if Debug:print("End Number-O2",end)
                O2=(output[start:end])
                O2=O2.strip()
                if aPrint:print("O2=",O2)
                if aPrint:GuiList("O2="+str(O2))
            elif "Status: " in output:
                start = (output.find(" "))+1
                end = len(output)
                if Debug:print("Start number-ST",start)
                if Debug:print("End Number-ST",end)
                ST=(output[start:end])
                ST=ST.strip()
                if aPrint:print("ST=",ST)
                if aPrint:print("") #Spaces data in output window
                if aPrint:GuiList("ST="+str(ST)+"\n")
                #Create message to send
                state = '"absent"' if ST=="0" else '"present"'
                IBI= 60/iHR if iHR>0 else 0
                sUDPmessage='{'+STA+',"state": '+state+',"heartrate": '+str(iHR)+',"saturation": '+str(O2)+',"confidence": '+str(CF)+',"TBB": '+str(IBI)+'}'
                if Debug:print(sUDPmessage)
                sock.sendto(sUDPmessage.encode('utf-8'),(UDP_IP,UDP_PORT))
    if Debug:print("Output = Space")
    output = " "
    
# Function to write to list
def GuiList(Message):
    global lGui
    lGui.append(Message)
#     print(*lGui)
    
    

def GuiPrint(): #Function to write to GUI
    global lGui
    for x in range (len(lGui)):
        text_box.insert(tk.END,"\n"+lGui[x])
        text_box.see(tk.END)
    lGui=[]
    
def HRGui(): #Prints HR to GUI
    global HR
    HRLabel.config(text="Heart Rate= " + str(HR))
    

#Open UDP socket
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
socklocal = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# Serial Code
ser = serial.Serial('/dev/ttyACM0', 115200, 8, 'N', 1, timeout=1)
    
# Gui Window creation    
window = tk.Tk()
window.title("Heartrate Capture V5")
window.geometry("660x800")
ipadding = {'ipadx': 10, 'ipady': 10}

#Changes button colors to match debug settings at top
SdebugColor = "red" if Sdebug else "blue"
FdebugColor = "red" if aPrint else "blue"
HdebugColor = "red" if hPrint else "blue"

SdebugLabel = "Serial Debug On" if Sdebug else "Serial Debug Off"
FdebugLabel = "Finger Debug On" if aPrint else "Finger Debug Off"
HdebugLabel = "Handle Debug On" if hPrint else "Handle Debug Off"

HRLabel = tk.Label( #HR Display
    text="Heart Rate= " + str(HR),
    fg="white",
    bg="black",
    width=16,
    height=1,
    font = ("Times New Roman",15)
)
bSdebug = tk.Button( #Serial Debug Button
    text=SdebugLabel,
    width=16,
    height=1,
    bg=SdebugColor,
    fg="yellow",
    font = ("Times New Roman",15),
    command=dSdebug
)

bFdebug = tk.Button( #Finger Debug Button
    text=FdebugLabel,
    width=16,
    height=1,
    bg=FdebugColor,
    fg="yellow",
    font = ("Times New Roman",15),
    command=dFdebug
)

bHdebug = tk.Button( #Handle Debug Button
    text=HdebugLabel,
    width=16,
    height=1,
    bg=HdebugColor,
    fg="yellow",
    font = ("Times New Roman",15),
    command=dHdebug
)

button_Clear = tk.Button(
    text="Clear",
    width=8,
    height=1,
    bg="blue",
    fg="yellow",
    font = ("Times New Roman",18),
    command=Clear
)
button_Close = tk.Button(
    text="Close",
    width=8,
    height=1,
    bg="blue",
    fg="yellow",
    font = ("Times New Roman",18),
    command=Close
)
    
#text_box = tk.Text(height = 38)
text_box = st.ScrolledText(window,
                            width = 63, 
                            height = 29, 
                            font = ("Times New Roman",
                                    15))
        
#Place buttons in window
bSdebug.place(x=10,y=10)
bFdebug.place(x=230,y=10)
bHdebug.place(x=450,y=10)
button_Clear.place(x=10,y=60)
button_Close.place(x=510,y=60)
HRLabel.place(x=240,y=60)
text_box.place(x=5,y=120)
# text_box.insert(tk.END, "First Line.")
# text_box.insert(tk.END, "\nPut me at the end!")

timrHR  =threading.Timer(5.0,reset)
timrA=threading.Timer(5.0,reset)
if Debug:print("Here we go! Press CTRL+C to exit")
text_box.insert(tk.END, "Here we go! press Close to exit\n")
text_box.see(tk.END)

try:
    if Debug:print("Try")
    GPIO.add_event_detect(HRInput,GPIO.RISING,callback=rTrig,bouncetime=350)
    while Running:
        if Debug:print("sRead")
        sRead()
#         text_box.insert(tk.END, "\nsRead")
#         text_box.see(tk.END)
        GuiPrint()
        HRGui()
        window.update_idletasks()
        if Debug:print("Idle Update")
        window.update()
        if Debug:print("Update")
        time.sleep(0.01)
    print("Program closed")    
    window.destroy()
    exit()
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    text_box.insert(tk.END, "End")
