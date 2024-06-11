from __future__ import annotations

from enum import Flag, auto
import tkinter as tk

class DEBUG_FLAG(Flag):
    NONE = 0
    MAIN = auto()
    SERIAL = auto()
    HANDLE = auto()
    ARDUINO = auto()

class Printer:
    def __init__(self, textbox = None, flags: DEBUG_FLAG = None):
        self.textbox = None
        if textbox: self.text_box = textbox
        
        self.flags: dict[str,DEBUG_FLAG] = flags

    def print(self, flag, value):
        if self.flags | flag:
            print(value)
            if self.textbox:
                self.text_box.insert(tk.END, value)
                self.text_box.see(tk.END) 
    
    def debug_status(self, flag: DEBUG_FLAG):
        return self.flags | flag
    
