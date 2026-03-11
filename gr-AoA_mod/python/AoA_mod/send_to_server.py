#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 gr-AoA_mod author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import json
import urllib.request
import urllib.error
import time
import numpy as np
from gnuradio import gr

TIMEOUT = 3    # seconds before giving up on a request
SERVER_URL = "http://172.20.10.7:5005/data" 

class send_to_server(gr.sync_block):
    """
    docstring for block send_to_server
    """
    def __init__(self, host, port, station_id, send_every):
        gr.sync_block.__init__(self,
            name="send_to_server",
            in_sig=[np.float32, ],
            out_sig=None)
        self.host = host
        self.port = port
        self.station_id = station_id
        self.send_every = send_every
        self.counter = 0

    def send_aoa(self, rx_id, aoa_deg):
        data = {
            "rx_id": rx_id,
            "aoa_deg": float(aoa_deg),
            "station_id": self.station_id
        }
        payload = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            f"http://{self.host}:{self.port}/data",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                body = response.read().decode("utf-8")
                print(f"[client] Sent {rx_id} aoa={aoa_deg:.2f} deg -> {response.status}")
                print(f"[client] Server response: {body}")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            print(f"[client] HTTP error {e.code} for {rx_id}: {e.reason}")
            print(f"[client] Server said: {error_body}")

        except urllib.error.URLError as e:
            print(f"[client] Network error ({rx_id}): {e.reason}")

        except Exception as e:
            print(f"[client] Unexpected error ({rx_id}): {e}")


    def work(self, input_items, output_items):
        in0 = input_items[0]
        self.counter += 1
        if self.counter < self.send_every:
            self.counter = 0
            self.send_aoa(self.station_id, (np.average(in0[0])))
            self.send_aoa(self.station_id, (np.average(in0[0])))

        # print(f"[client] Sending {len(readings)} readings to {f"http://{self.host}:{self.port}/data"}")
        # print( "[client] Make sure server.py is running first.\n")
        # if self.counter < self.send_every:
        #     for i, (aoa1, aoa2) in enumerate(readings):
        #             print(f"-- Reading {i + 1} --")
        #             self.send_aoa("RX1", aoa1)
        #             self.send_aoa("RX2", aoa2)
        #             time.sleep(1.5)   # short interval so dashboard animates nicely   
        return len(input_items[0])
