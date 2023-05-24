# Inspired by https://github.com/WiringPi/WiringPi/blob/master/wiringPi/wiringPi.c

import ctypes
import os
import mmap
import time
from typing import Iterable, Optional, Callable

class AutoRestoreRegisters:
    def __init__(self, registers: Iterable[ctypes.c_int], cb: Optional[Callable[[Iterable[int]], None]] = None):
        self.registers = registers
        self.original_values = []
        self.cb = cb

    def __enter__(self):
        self.original_values =  [reg.value for reg in self.registers]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for reg, original_value in zip(self.registers, self.original_values):
            reg.value = original_value
            # print(f"Restored 0x{original_value:08X}")
            
        if self.cb is not None:
            self.cb(self.original_values)

class PWMController:
    
    GPIO_PERI_BASE_2711 = 0xFE000000
    PAGE_SIZE = 4*1024
    BLOCK_SIZE = 4*1024
    PWM0_RANGE = 4
    PWM1_RANGE = 8
    PWM_CONTROL = 0
    PWM_STATUS = 1
    PWM0_RANGE = 4
    PWM1_RANGE = 8
    PWMCLK_CNTL = 40
    PWMCLK_DIV = 41
    BCM_PASSWORD = 0x5A000000
    TIMER_CONTROL = (0x408 >> 2)
    TIMER_PRE_DIV = (0x41C >> 2)

    PWM0_ENABLE = 0x0001
    PWM1_ENABLE = 0x0100
    PWM0_MS_MODE = 0x0080
    PWM1_MS_MODE = 0x8000

    def __init__(self):
        piGpioBase = self.GPIO_PERI_BASE_2711
        GPIO_PWM = piGpioBase + 0x0020C000
        GPIO_CLOCK_BASE = piGpioBase + 0x00101000

        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC | os.O_CLOEXEC)
        self._pwm = mmap.mmap(fd, self.BLOCK_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=GPIO_PWM)
        self._pwm_mv = memoryview(self._pwm)
        self._clk = mmap.mmap(fd, self.BLOCK_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=GPIO_CLOCK_BASE)
        self._clk_mv = memoryview(self._clk)

        PWMCLK_DIV = PWMController.PWMCLK_DIV
        PWMCLK_CNTL = PWMController.PWMCLK_CNTL
        PWM_CONTROL = PWMController.PWM_CONTROL

        self.pwm_clk_div = ctypes.c_int.from_buffer(self._clk_mv, PWMCLK_DIV*4)
        self.pwm_control = ctypes.c_int.from_buffer(self._pwm_mv, PWM_CONTROL*4)
        self.pwm_clk_cntl = ctypes.c_int.from_buffer(self._clk_mv, PWMCLK_CNTL*4)
        self.pwm0_range = ctypes.c_int.from_buffer(self._pwm_mv, PWMController.PWM0_RANGE*4)
        self.pwm1_range = ctypes.c_int.from_buffer(self._pwm_mv, PWMController.PWM1_RANGE*4)


    def configure_pwm0(self, range: int):
        self.pwm0_range.value = range
        # print(f"Set PWM0 range to: {range}")

    def configure_pwm1(self, range: int):
        self.pwm1_range.value = range
        # print(f"Set PWM1 range to: {range}")

    def set_mode(self, channel_mode: str):
        mode = PWMController.PWM0_ENABLE | PWMController.PWM1_ENABLE
        if channel_mode == "ms":
            mode = mode | PWMController.PWM0_MS_MODE | PWMController.PWM1_MS_MODE

        self.pwm_control.value = mode
        # print(f"Set PWM_CONTROL to: 0x{mode:08X}")

    def pwm_set_clock(self, divisor: int):
        divisor = int(540*divisor/192)
        divisor &= 4095

        pwm_clk_div = self.pwm_clk_div
        pwm_control = self.pwm_control
        
        # print(f"Setting to: {divisor}. Current: 0x{pwm_clk_div.value:08X}")

        with AutoRestoreRegisters([pwm_control]):
            # print(f"Current PWM_CONTROL: {prev_pwm_control}")

            # We need to stop PWM prior to stopping PWM clock in MS mode otherwise BUSY
            # stays high.
            pwm_control.value = 0 # Stop PWM

            # Stop PWM clock before changing divisor. The delay after this does need to
            # this big (95uS occasionally fails, 100uS OK), it's almost as though the BUSY
            # flag is not working properly in balanced mode. Without the delay when DIV is
            # adjusted the clock sometimes switches to very slow, once slow further DIV
            # adjustments do nothing and it's difficult to get out of this mode.

            pwm_clk_cntl = self.pwm_clk_cntl
            pwm_clk_cntl.value = PWMController.BCM_PASSWORD | 0x01 # Stop PWM Clock
            time.sleep(0.0001)                                  # prevents clock going sloooow

            while ((pwm_clk_cntl.value & 0x80) != 0): # Wait for clock to be !BUSY
                time.sleep(0.000001)

            pwm_clk_div.value = PWMController.BCM_PASSWORD | (divisor << 12)
            pwm_clk_cntl.value = PWMController.BCM_PASSWORD | 0x011 # Start PWM Clock

        # print(f"Set     to: {divisor}. Now    : 0x{pwm_clk_div.value:08X}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        del self.pwm0_range
        del self.pwm1_range
        del self.pwm_control
        del self._pwm_mv
        self._pwm.close()

        del self.pwm_clk_div
        del self.pwm_clk_cntl
        del self._clk_mv
        self._clk.close()