#!/bin/bash

python app.py &

python auctions_worker.py
