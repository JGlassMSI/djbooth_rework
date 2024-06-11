from __future__ import annotations

#Import for GUI
import tkinter as tk
import tkinter.scrolledtext as st
from sys import exit
import sys
import time

#Import for HR
if sys.platform.startswith("linux"):
    import serial
    import RPi.GPIO as GPIO
else:
    from unittest.mock import Mock
    sys.modules['serial'] = Mock()
    sys.modules['GPIO'] = Mock()
    import serial
    import GPIO
import socket
import threading

from _printer import Printer, DEBUG_FLAG
from _status import bool_to_color, bool_to_status, bool_to_on_off
from _monitor import HandleMonitor

class DJUI:
    UDP_IP = "192.168.10.6"#IP address to send to
    UDP_PORT = 16501 #Port to send to
    GPIO_PIN = 4
    def __init__(self, id: int, flags = None):
        self.id_string = f'"id":{id}'
        if flags is None: flags = DEBUG_FLAG.NONE
        #Open UDP socket
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socklocal = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

        # Serial Code
        #self.ser = serial.Serial('/dev/ttyACM0', 115200, 8, 'N', 1, timeout=1)
    
        # Gui Window creation    
        self.window = tk.Tk()
        self.window.title("Heartrate Capture V5")
        self.window.geometry("660x800")

        #Changes button colors to match debug settings at top
        self.SdebugColor = bool_to_color(flags & DEBUG_FLAG.SERIAL)
        self.FdebugColor = bool_to_color(flags & DEBUG_FLAG.ARDUINO)
        self.HdebugColor = bool_to_color(flags & DEBUG_FLAG.HANDLE)

        self.dSdebug = self.dFdebug = self.dHdebug = lambda: None

        self.handle_monitor = HandleMonitor(id_string=self.id_string, handle_pin=self.GPIO_PIN, handle_callback=self.send_message, printer=None)

        self.setup_gui()

        self.printer = Printer(
            textbox = self.text_box,
            flags = flags 
        )

        self.handle_monitor.printer = self.printer        

        self.dSdebug = self.make_debug_handler('serial_debug', "Serial Debug", self.bSdebug)
        self.dFdebug = self.make_debug_handler('arduino_debug', "Arduino Debug", self.bFdebug)
        self.dHdebug = self.make_debug_handler('handle_debug', "Handle Debug", self.bHdebug)

    def get_debug_status(self, keyword):
        if not hasattr(self, "printer") or not self.printer: return False
        return self.printer.debug_status(keyword)

    def set_debug_flag_to(self, flag: DEBUG_FLAG, val: bool):
        if val: self.set_debug_flag(flag)
        else: self.clear_debug_flag(flag)
    
    def set_debug_flag(self, flag):
        self.printer.flags |= flag

    def clear_debug_flag(self, flag):
        self.printer.flag &= ~flag

    def debug(self, flag, value):
        if hasattr(self, "printer") and self.printer: self.printer.print(flag, value)

    def setup_gui(self, heartrate=0):
        SdebugLabel = f"Serial Debug {bool_to_on_off(self.get_debug_status(DEBUG_FLAG.SERIAL))}" 
        FdebugLabel = f"Finger Debug {bool_to_on_off(self.get_debug_status(DEBUG_FLAG.ARDUINO))}" 
        HdebugLabel = f"Handle Debug {bool_to_on_off(self.get_debug_status(DEBUG_FLAG.HANDLE))}" 


        HRLabel = tk.Label( #HR Display
            text="Heart Rate= " + str(heartrate),
            fg="white",
            bg="black",
            width=16,
            height=1,
            font = ("Times New Roman",15)
        )
        self.bSdebug = tk.Button( #Serial Debug Button
            text=SdebugLabel,
            width=16,
            height=1,
            bg=self.SdebugColor,
            fg="yellow",
            font = ("Times New Roman",15),
            command=self.dSdebug
        )

        self.bFdebug = tk.Button( #Finger Debug Button
            text=FdebugLabel,
            width=16,
            height=1,
            bg=self.FdebugColor,
            fg="yellow",
            font = ("Times New Roman",15),
            command=self.dFdebug
        )

        self.bHdebug = tk.Button( #Handle Debug Button
            text=HdebugLabel,
            width=16,
            height=1,
            bg=self.HdebugColor,
            fg="yellow",
            font = ("Times New Roman",15),
            command=self.dHdebug
        )

        button_Clear = tk.Button(
            text="Clear",
            width=8,
            height=1,
            bg="blue",
            fg="yellow",
            font = ("Times New Roman",18),
            command=self.clear
        )
        button_Close = tk.Button(
            text="Close",
            width=8,
            height=1,
            bg="blue",
            fg="yellow",
            font = ("Times New Roman",18),
            command=self.close
        )
            
        #text_box = tk.Text(height = 38)
        self.text_box = st.ScrolledText(self.window,
                                    width = 63, 
                                    height = 29, 
                                    font = ("Times New Roman",
                                            15))
        
        #Place buttons in window
        self.bSdebug.place(x=10,y=10)
        self.bFdebug.place(x=230,y=10)
        self.bHdebug.place(x=450,y=10)
        button_Clear.place(x=10,y=60)
        button_Close.place(x=510,y=60)
        HRLabel.place(x=240,y=60)
        self.text_box.place(x=5,y=120)
        # text_box.insert(tk.END, "First Line.")
        # text_box.insert(tk.END, "\nPut me at the end!")

        timrHR  =threading.Timer(5.0,self.handle_monitor.reset)
        timrA = threading.Timer(5.0,self.handle_monitor.reset)
        self.debug(DEBUG_FLAG.MAIN, "Here we go! Press CTRL+C to exit")
        self.text_box.insert(tk.END, "Here we go! press Close to exit\n")
        self.text_box.see(tk.END)

    def make_debug_handler(self, status_flag:DEBUG_FLAG, status_label:str, button: tk.Button) -> None:
        def f():
            new_status = not self.get_debug_status(status_flag)
            self.set_debug_status(status_flag, new_status)

            self.debug(status_flag, f"{status_label} {bool_to_status(new_status)}")
            self.bSdebug.config(text=f"{status_label} {bool_to_on_off(new_status)}")
            self.bSdebug.config(bg=bool_to_color(new_status))
        return f

    def clear(self):
        self.text_box.delete(1.0,tk.END)
        self.text_box.see(tk.END)
        
    def close(self):
        self.running=False

    def send_message(self, msg):
        self.sock.sendto(msg.encode('utf-8'),(self.UDP_IP,self.UDP_PORT))

    def handle_serial(self):
        ...

    def run(self):
        self.running = True
        self.handle_monitor.start()

        while self.running:
            print(DEBUG_FLAG.MAIN, "handle_serial")
            self.handle_serial()
            #GuiPrint()
            #HRGui()
            self.window.update_idletasks()
            print(DEBUG_FLAG.MAIN, "Idle update")
            self.window.update()
            print(DEBUG_FLAG.MAIN, "Update")
            time.sleep(0.1)
        print("Program closed")
        self.window.destroy()
        exit()