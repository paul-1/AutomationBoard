# SPDX-FileCopyrightText: 2022 Paul Hermann for Orbis Corporation
# SPDX-License-Identifier: MIT#
#
#  Orbis 24 point Automation Board
#
#  This program runs using Circuitpython.  https://circuitpython.org/board/raspberry_pi_pico/
#

"""
To Configure, Change the variable "output" below.  Be sure to follow comments.

Then save as Orbis.py (or code.py) to the raspberry pico with Circuitpython already installed.
"""

import board
from digitalio import DigitalInOut, Direction, Pull
from Orbis_libs import IO_Display, log, Heartbeat
import time

# Create empty dictionary for I/O configuraion
output = {}

# This assigns gpio 0-19 to output gpio 20. Do not change or mixup brackets and braces.
output[1] = {'output_gpio': [20],     # There should only be a single number for the output,
             'input_gpio' : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]}

# This example creates 2 outputs using 8 gpio each
# output[1] = { 'output_gpio': [20],
#               'input_gpio':  [0, 1, 2, 3, 4, 5, 6]}
# output[2] = { 'output_gpio': [21],
#               'input_gpio':  [8, 9, 11, 10, 13, 14, 15]}
# output[3] = { 'output_gpio': [22],
#               'input_gpio':  [19]}

"""
----------------Changes should not be needed below this line--------------------------
"""
# The 24 point Automation board uses:
valid_outputs = [20, 21, 22, 28]
valid_inputs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

# Configure Display if found, needs to happen early, for print messages below to show on display.
iom = IO_Display()

def config_error(x):
    print(x)
    while True:
        time.sleep(10)

if len(output) > 4:
    config_error("\nToo many outputs\ndefined.\nCheck Program")

used_outputs = []
for key in output:
    if output[key]['output_gpio'][0] not in valid_outputs:
        config_error("\nInvalid output\ngpio used.\nCheck Program")
    if output[key]['output_gpio'][0] not in used_outputs:
        used_outputs.append(output[key]['output_gpio'][0])
    else:
        config_error("\nDuplicate output\ngpio used.\nCheck Program")
used_inputs = []
for key in output:
    for x in output[key]['input_gpio']:
        if x not in valid_inputs:
            config_error("\nInvalid input\ngpio used.\nCheck Program")
        if x not in used_inputs:
            used_inputs.append(x)
        else:
            config_error("\nDuplicate input\ngpio used.\nCheck Program")
del used_outputs  # Free unneeded variables
del used_inputs

# Setup output pins and make sure outputs are off.
for key in sorted(output):
    try:
        output[key]['output_pin'] = [DigitalInOut(getattr(board, 'GP%d' % output[key]['output_gpio'][0]))]
        output[key]['output_pin'][0].direction = Direction.OUTPUT
        output[key]['output_pin'][0].value = False
        print('Output %d configured on GPIO %s' % (key, output[key]['output_gpio'][0]))
    except Exception as e:
        print('Error setting up outputs:', e)

# Setup Configured Input pins
for key in sorted(output):
    print("Output %d: Configuring Inputs: " % key, end='')
    output[key]['input_pin'] = []
    for x in output[key]['input_gpio']:
        try:
            output[key]['input_pin'].append(DigitalInOut(getattr(board, 'GP%d' % x)))
            output[key]['input_pin'][-1].direction = Direction.INPUT  # -1 references the last in the list(just added above)
            output[key]['input_pin'][-1].pull = Pull.DOWN  # Board has external Pulls on input pins
            print("%s, " % x, end='')
        except Exception as e:
            print('Error setting up inputs:', e)
    print("", end='\n')


heart = Heartbeat()
mylog = log()

while True:  # Loop as fast as possible, using clock scheduler to perform events.
    now = time.monotonic()

    # Heartbeat LED
    heart.update(now)
    
    # io monitor
    iom.update(now, output)

    # Set print state to console.
    mylog.update(now)
    
    # Check GPIO every scan through.
    for key in sorted(output):
        output[key]['input_state'] = True
        mylog.print("Output %d: GPIO%02d: %s" % (key, output[key]['output_gpio'][0], ("ON" if output[key]['output_pin'][0].value else "OFF")))
        mylog.print("Inputs  : ", end='')

        for x in output[key]['input_gpio']:  # Cycle through GPIO assignment and print number
            mylog.print("%02d " % x, end='')
        mylog.print("\n          ", end='')

        for x in output[key]['input_pin']:  # Cycle through the pin input values and set the state.
            mylog.print(" %1d " % x.value, end='')
            if not x.value:
                output[key]['input_state'] = False
        mylog.print("\n", end='')

        if output[key]['input_state']: 
            output[key]['output_pin'][0].value = True
        else:
            output[key]['output_pin'][0].value = False
