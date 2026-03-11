#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 gr-AoA_mod author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
import time

class phase_to_angle(gr.sync_block):
    """
    docstring for block phase_to_angle
    """
    def __init__(self, samp_rate, center_freq, tone_freq, d):
        gr.sync_block.__init__(self,
            name="phase_to_angle",
            in_sig=[np.float32, ],
            out_sig=[np.float32, ])
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.tone_freq = tone_freq
        self.d = d
        self.lambda_ = 3e8 / (self.center_freq + self.tone_freq)
        self.angle = 0.0
        self.last_angle = 0.0
        self.counter = 0
        self.phase_cal = 0.0
        self.curr_phi = 0.0
        self.curr_angle = 0.2

    def work(self, input_items, output_items):
        # phase calibration assuming the object starts directly in front of the antenna
        # if self.phase_cal == 0.0:
        #     self.phase_cal = np.average(input_items[0])
        #     print(f"Phase calibration set to {self.phase_cal:.2f} radians")
        phase_in0 = input_items[0]
        angle_out = output_items[0]
        
        # For now there is no phase cllibration
        phi = phase_in0 - self.phase_cal

        x = (self.lambda_ * phi) / (2 * np.pi * self.d)

        # Adjust for overflow
        # x = (np.mod(x + 1, 2) - 1) * np.sign(x)
        x = np.clip(x, -1, 1)
        
        # Find the angle of arrival
        angle_out[:] = np.degrees(np.arcsin(x))
        # self.counter += 1
        # # self.curr_phi = np.average(phi)/1000
        # # self.curr_angle = np.average(angle_out)/1000
        # if self.counter%1000 == 0:
        #     # print(f"phase: {self.curr_phi:.2f} Angle: {self.curr_angle:.2f} degrees")
        #     # self.curr_angle = 0.0
        #     # self.curr_phi = 0.0
        #     print(f"phase: {np.average(phi):.2f} Angle: {np.average(angle_out):.2f} degrees")
        return len(output_items[0])
