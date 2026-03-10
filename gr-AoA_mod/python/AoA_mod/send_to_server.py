#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 gr-AoA_mod author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class send_to_server(gr.sync_block):
    """
    docstring for block send_to_server
    """
    def __init__(self, host, port, station_id, send_every):
        gr.sync_block.__init__(self,
            name="send_to_server",
            in_sig=[np.float32, ],
            out_sig=None)


    def work(self, input_items, output_items):
        in0 = input_items[0]
        # <+signal processing here+>
        return len(input_items[0])
