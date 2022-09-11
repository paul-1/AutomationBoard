# SPDX-FileCopyrightText: 2022 Paul Hermann for Orbis Corporation
# SPDX-License-Identifier: MIT#
#
#  Orbis 24 point Automation Board
#
#  This program runs using Circuitpython.  https://circuitpython.org/board/raspberry_pi_pico/
#
import board
import busio
from digitalio import DigitalInOut, Direction
import displayio
import adafruit_displayio_ssd1306
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
import gc

class IO_Display:
    def __init__(self):
        try:
            displayio.release_displays()  # If doing warm resets, the display can hold the i2c line.
        except Exception as e:
            pass
        self.IO_MONITOR_FREQ = .5
        self.LAST_IO_MONITOR = -1
        try:
            self.i2c = busio.I2C(sda=board.GP26, scl=board.GP27, frequency=100000)
            if self.i2c.try_lock():
                i2c_addr = [hex(ii) for ii in self.i2c.scan()]  # get I2C address in hex format
                self.i2c.unlock()
                if i2c_addr == []:
                    print('No I2C Display Found during scan')
                    self.DISPLAY = False
                else:
                    self.DISPLAY = True
                    print("Display Configured on I2C1 dev:{}".format(i2c_addr[0]))
            else:
                self.i2c.unlock()
                self.DISPLAY = False
                print("Error Checking i2c_addr")
        except Exception as e:
            print("Error Configuring Display:", e)
            self.DISPLAY = False

        if self.DISPLAY:  # Using an SSD1306 1.3" Display
            WIDTH = 128
            HEIGHT = 64
            self.COLOR = {'Blk': 0x000000, 'Wht': 0xFFFFFF}

            self.FONT = bitmap_font.load_font("DejaVuSans-12.pcf")
            self.FONT_X = 8  # 8x12 font
            self.FONT_Y = 12

            display_bus = displayio.I2CDisplay(self.i2c, device_address=int(i2c_addr[0]))
            self.display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

    def io_monitor(self, output):
        gc.collect()  # Cleanup old display memory
        disp_group = displayio.Group()
        title = Label(
            self.FONT,
            text="ORBIS Automation",
            x=1,
            y=8,
            color=self.COLOR['Wht'],
            background_color=self.COLOR['Blk']
        )
        disp_group.append(title)

        x = 3
        dx = self.FONT_X
        y = 22
        dy = self.FONT_Y

        disp_gpio = []
        disp_gpio.append(Label(self.FONT, text='   IN:', x=x, y=y, color=self.COLOR['Wht'], background_color=self.COLOR['Blk']))
        disp_group.append(disp_gpio[-1])
        x = 35
        y -= 1    # Move the numbers one pixel up
        for i in range(0, 20):  # Cycle through all possible inputs. This is actually 0-19
            t = "%02d" % i
            found = False
            for key in output:
                for j in output[key]['input_gpio']:
                    if i == j:  # If we find the input is used, then check the value of the input.  And set color appropriately.
                        found = True
                        indexofcntrl = output[key]['input_gpio'].index(j)
                        fgcolor = 'Blk' if output[key]['input_pin'][indexofcntrl].value else 'Wht'
                        bgcolor = 'Wht' if output[key]['input_pin'][indexofcntrl].value else 'Blk'
                        disp_gpio.append(Label(self.FONT, text=t[-1], x=x, y=y, color=self.COLOR[fgcolor], background_color=self.COLOR[bgcolor]))
            if not found:
                disp_gpio.append(Label(self.FONT, text='_', x=x, y=y, color=self.COLOR['Wht'], background_color=self.COLOR['Blk']))
            disp_group.append(disp_gpio[-1])
            x += dx
            if x > 110:  # Rolls over after 10 characters
                x = 35
                y += dy

        x = 3
        y = 54
        disp_gpio.append(Label(self.FONT, text='OUT:', x=x, y=y, color=self.COLOR['Wht'], background_color=self.COLOR['Blk']))
        disp_group.append(disp_gpio[-1])
        x = 35
        y -= 1
        for i in [20, 21 ,22 , 28]:  #THere are 4 possible outputs.
            t = "%02d" % i
            found = False
            for key in output:
                for j in output[key]['output_gpio']:
                    if i == j:  # If we find the input is used, then check the value of the input.  And set color appropriately.
                        found = True
                        indexofcntrl = output[key]['output_gpio'].index(j)
                        fgcolor = 'Blk' if output[key]['output_pin'][indexofcntrl].value else 'Wht'
                        bgcolor = 'Wht' if output[key]['output_pin'][indexofcntrl].value else 'Blk'
                        disp_gpio.append(Label(self.FONT, text=t[-1], x=x, y=y, color=self.COLOR[fgcolor], background_color=self.COLOR[bgcolor]))
            if not found:
                disp_gpio.append(Label(self.FONT, text='_', x=x, y=y, color=self.COLOR['Wht'], background_color=self.COLOR['Blk']))
            disp_group.append(disp_gpio[-1])
            x += dx

        self.display.show(disp_group)

    def update(self, now, output):
        if self.DISPLAY and now >= self.LAST_IO_MONITOR + self.IO_MONITOR_FREQ:
            self.io_monitor(output)
            self.LAST_IO_MONITOR = now

class Heartbeat:
    def __init__(self, pin):
        # Configure LED
        try:
            self.led = DigitalInOut(pin)
            self.led.direction = Direction.OUTPUT
        except Exception as e:
            print("Only one instance of Heartbeat supported")
        self.BLINK_ON_DURATION = 1
        self.BLINK_OFF_DURATION = 2
        self.LAST_BLINK_TIME = -1

    def stop(self):
        self.led.value = False

    def update(self, now):
        # Heartbeat blink on the pico onboard LED
        if not self.led.value:
            if now >= self.LAST_BLINK_TIME + self.BLINK_OFF_DURATION:
                self.led.value = True
                self.LAST_BLINK_TIME = now
        if self.led.value:
            if now >= self.LAST_BLINK_TIME + self.BLINK_ON_DURATION:
                self.led.value = False
                self.LAST_BLINK_TIME = now

class log:
    def __init__(self):
        self.PRINT_IO_FREQ = 3
        self.LAST_PRINT_IO = -1
        self.pr = False

    def print(self, data, end='\n'):
        if self.pr:
            print(data, end=end)

    def update(self, now):
        if now >= self.LAST_PRINT_IO + self.PRINT_IO_FREQ:
            self.LAST_PRINT_IO = now
            self.pr = True
        else:
            self.pr = False
