#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 gr-AoA_mod author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

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
        self.lambda_ = 3e8 / self.center_freq


    def work(self, input_items, output_items):
        phase_in0 = input_items[0]
        angle_out = output_items[0]
        
        # For now there is no phase cllibration
        phi = phase_in0

        x = (self.lambda_ * phi) / (2 * np.pi * self.d)

        # Adjust for overflow
        x = np.clip(x, -1, 1)
        
        angle_out[:] = np.arcsin(x).astype(np.float32)
        return len(output_items[0])
