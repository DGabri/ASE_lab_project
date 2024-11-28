#!/bin/bash
flask run \
    --host=0.0.0.0 \
    --port=5000 \
    --reload \
    --cert=/run/secrets/auction_cert_secret \
    --key=/run/secrets/auction_key_secret &

python auctions_worker.py