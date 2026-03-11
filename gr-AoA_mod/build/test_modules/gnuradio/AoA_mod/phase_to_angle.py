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

    def work(self, input_items, output_items):
        if self.phase_cal == 0.0:
            self.phase_cal = np.average(input_items[0])
            print(f"Phase calibration set to {self.phase_cal:.2f} radians")
        phase_in0 = input_items[0]
        angle_out = output_items[0]
        
        # For now there is no phase cllibration
        phi = phase_in0 - self.phase_cal

        x = np.average((self.lambda_ * phi) / (2 * np.pi * self.d))

        # Adjust for overflow
        # x = np.clip(x, -1, 1)
        
        # Find the angle of arrival
        angle_out[:] = np.degrees(np.arcsin(x))
        self.counter += 1

        if self.counter%100 == 0:
            print(x)
            print(f"phase: {phi[0]:.2f} Angle: {angle_out[0]:.2f} degrees")
        return len(output_items[0])
