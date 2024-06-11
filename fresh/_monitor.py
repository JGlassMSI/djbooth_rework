from __future__ import annotations

import sys
import time

from collections import deque
from _printer import Printer, DEBUG_FLAG
if sys.platform.startswith("linux"):
    import RPi.GPIO as GPIO
else:
    from unittest.mock import Mock
    sys.modules['serial'] = Mock()
    sys.modules['GPIO'] = Mock()
    import serial
    import GPIO

class HandleMonitor:
    def __init__(self, id_string: str, handle_pin: int, handle_callback = None, printer: Printer = None, max_samples: int = 4):
        self.id_string = id_string
        self.printer: Printer = printer
        self.handle_pin = handle_pin
        self.handle_callback = handle_callback

        self.last_heartbeat_time = time.time()
        self.times_between_beats = deque(maxlen=max_samples)  #Time between beats list for average
        
    def start(self):
        GPIO.add_event_detect(self.handle_pin,GPIO.RISING,callback=self.handle_callback,bouncetime=350)

    def stop(self):
        GPIO.remove_event_detect(self.handle_pin)

    def reset(self):
        self.times_between_beats.clear()

    def print(self, value):
        if self.printer: self.printer.print(DEBUG_FLAG.HANDLE, value)

    def maybe_generate_message(self, callback) -> str | None:
        self.print(f"last heartbeat time = {self.last_heartbeat_time}")
        self.print("HB Detected")

        now = time.time()
        t = now - self.last_heartbeat_time
        print(f"Time between beats: {t}")

        self.times_between_beats.append(t)

        if len(self.times_between_beats) >= self.times_between_beats.maxlen: # Wait until queue is full
            average_between_beats = sum(self.times_between_beats) / self.times_between_beats.maxlen
            self.print(f"{average_between_beats=}")

            heartrate:float = 60/average_between_beats
            self.print(f"{heartrate=}")
            self.last_heartbeat_time = now

            callback(f'{{"{self.id_string}","state": "present", "heartrate": {int(heartrate)}, "saturation": 0, "confidence": 0, "TBB": {t}}}')