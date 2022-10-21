# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import abc
import subprocess
import RPi.GPIO as GPIO

from sj201_interface.revisions import SJ201


class MycroftFan:
    """ abstract base class for a Mycroft Fan
     all fan classes must provide at least
     these basic methods """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def set_fan_speed(self, new_speed):
        """takes in value between 0 - 100
           converts to internal format"""
        return

    @abc.abstractmethod
    def get_fan_speed(self):
        """returns value between 0-100"""

    @abc.abstractmethod
    def get_cpu_temp(self):
        """returns temp in celsius"""
        return

    @staticmethod
    def execute_cmd(cmd):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, )
        out, err = process.communicate()
        try:
            out = out.decode("utf8")
        except Exception:
            pass

        try:
            err = err.decode("utf8")
        except Exception:
            pass

        return out, err

    @staticmethod
    def cToF(temp):
        return (temp * 1.8) + 32


class R6FanControl(MycroftFan):
    # hardware speed range is appx 30-255
    # we convert from 0 to 100
    HDW_MIN = 0
    HDW_MAX = 255
    SFW_MIN = 0
    SFW_MAX = 100

    def __init__(self):
        self.fan_speed = 0
        self.set_fan_speed(self.fan_speed)

    def speed_to_hdw_val(self, speed):
        out_steps = self.HDW_MAX - self.HDW_MIN
        in_steps = self.SFW_MAX - self.SFW_MIN
        ratio = out_steps / in_steps
        # force compliance
        if speed > self.SFW_MAX:
            speed = self.SFW_MAX
        if speed < self.SFW_MIN:
            speed = self.SFW_MIN

        return int((speed * ratio) + self.HDW_MIN)

    def hdw_val_to_speed(self, hdw_val):
        out_steps = self.SFW_MAX - self.SFW_MIN
        in_steps = self.HDW_MAX - self.HDW_MIN
        ratio = out_steps / in_steps
        # force compliance
        if hdw_val > self.HDW_MAX:
            hdw_val = self.HDW_MAX
        if hdw_val < self.HDW_MIN:
            hdw_val = self.HDW_MIN

        return int(round(((hdw_val - self.HDW_MIN) * ratio) + self.SFW_MIN, 0))

    def hdw_set_speed(self, hdw_speed):
        # force compliance
        if hdw_speed > self.HDW_MAX:
            hdw_speed = self.HDW_MAX
        if hdw_speed < self.HDW_MIN:
            hdw_speed = self.HDW_MIN

        hdw_speed = str(hdw_speed)
        cmd = ["i2cset", "-y", "1", "0x04", "101", hdw_speed, "i"]
        out, err = self.execute_cmd(cmd)

    def set_fan_speed(self, speed):
        self.fan_speed = self.speed_to_hdw_val(speed)
        self.hdw_set_speed(self.fan_speed)

    def get_fan_speed(self):
        return self.hdw_val_to_speed(self.fan_speed)

    def get_cpu_temp(self):
        cmd = ["cat", "/sys/class/thermal/thermal_zone0/temp"]
        out, err = self.execute_cmd(cmd)
        return float(out.strip()) / 1000


class R10FanControl(MycroftFan):
    # hardware speed range is appx 30-255
    # we convert from 0 to 100
    HDW_MIN = 100
    HDW_MAX = 0
    SFW_MIN = 0
    SFW_MAX = 100

    def __init__(self):
        self.fan_speed = 0
        ledpin = 13  # PWM pin connected to LED
        GPIO.setwarnings(False)  # disable warnings
        GPIO.setmode(GPIO.BCM)  # set pin numbering system
        GPIO.setup(ledpin, GPIO.OUT)  # set direction
        self.pi_pwm = GPIO.PWM(ledpin, 1000)  # create PWM instance with frequency
        self.pi_pwm.start(0)  # start PWM of required Duty Cycle
        self.set_fan_speed(self.fan_speed)

    @staticmethod
    def speed_to_hdw_val(speed):
        return float(100.0 - (speed % 101))

    @staticmethod
    def hdw_val_to_speed(hdw_val):
        return abs(float(hdw_val - 100.0))

    def hdw_set_speed(self, hdw_speed):
        self.pi_pwm.ChangeDutyCycle(hdw_speed)  # provide duty cycle in the range 0-100

    def set_fan_speed(self, speed):
        self.fan_speed = self.speed_to_hdw_val(speed)
        self.hdw_set_speed(self.fan_speed)

    def get_fan_speed(self):
        return self.hdw_val_to_speed(self.fan_speed)

    def get_cpu_temp(self):
        cmd = ["cat", "/sys/class/thermal/thermal_zone0/temp"]
        out, err = self.execute_cmd(cmd)
        return float(out.strip()) / 1000


def get_fan(revision: SJ201) -> MycroftFan:
    if revision == SJ201.r10:
        return R10FanControl()
    elif revision == SJ201.r6:
        return R6FanControl()
    else:
        raise ValueError(f"Unsupported revision: {revision}")
