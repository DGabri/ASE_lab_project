import logging
import sqlite3
import time
from venv import logger
from flask_cors import CORS
from auctions_DAO import AuctionDAO
from auction_service import AuctionService
from flask import Flask, json, request, jsonify
import os
from flask import request, jsonify
app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False
with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
CORS(app)
auction_dao = AuctionDAO(config['db']['name'], config['db']['scheme'])
auction_service = AuctionService(auction_dao)

## routes for the project

@app.route('/auction', methods=['POST'])
def create_auction():
    try:

        data = request.get_json()
        piece_id = data['piece_id']
        creator_id = data['creator_id']
        start_price = data['start_price']
        end_date = data['end_date']

        if not piece_id or not creator_id or not start_price or not end_date:
            return jsonify({"error": "Missing required fields"}), 400
        response = auction_service.create_auction(piece_id, creator_id, start_price, end_date)
        return jsonify(response), 201
    except Exception as e:
        return jsonify({"error": "An error occurred while processing the request"}), 500

@app.route('/auction/<int:auction_id>', methods=['GET'])
def get_auction_info(auction_id):
    try:
        auction_info = auction_service.get_auction_info(auction_id)
        if not auction_info:
            return jsonify({"error": "Auction not found"}), 404
        return jsonify(auction_info), 200

    except Exception as e:
        logging.error("Error fetching auction info for auction_id %s: %s", auction_id, e)
        return jsonify({"error": "An error occurred while processing the request"}), 500


@app.route('/auction/bid/<int:auction_id>', methods=['POST'])
def place_bid(auction_id):
    try:
        data = request.get_json()
        # these are given by json
        user_id = data['user_id']
        bid_amount = data['bid_amount']
        response = auction_service.place_bid(auction_id, user_id, bid_amount)
        return jsonify(response),200
    except Exception as e:
        return jsonify({"error": "An error occurred while bid an auction"}), 500

@app.route('/auction/running', methods=['GET'])
def get_active_auctions():
    try:
        auctions = auction_service.get_active_auctions()
        return jsonify(auctions),200
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching active auctions"}), 500

@app.route('/auction/history', methods=['GET'])
def get_past_auctions():
    try:
        auctions = auction_service.get_past_auctions()
        return jsonify(auctions),200
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching active auctions"}), 500

@app.route('/auction/running/<int:piece_id>', methods=['GET'])
def get_active_auctions_by_piece_id(piece_id):
    try:
        auctions = auction_service.get_active_auctions_by_piece_id(piece_id)
        return jsonify(auctions),200
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching active auctions"}), 500

###############other routes##########

@app.route('/close_auction', methods=['POST'])
def close_auction():
    data = request.get_json()
    auction_id = data['auction_id']
    response = auction_service.close_auction(auction_id)
    return jsonify(response)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Server is up and running!"})

@app.route('/close_expired_auctions', methods=['POST'])
def close_expired_auctions():
    response = auction_service.close_expired_auctions()
    return jsonify(response)


@app.route('/auction/<int:auction_id>/bidding_history', methods=['GET'])
def get_bidding_history(auction_id):
    try:
        bidding_history = auction_service.get_market_history(auction_id)
        
        if bidding_history["status"] == "error":
            return jsonify(bidding_history), 404 
        return jsonify(bidding_history), 200 

    except Exception as e:
        logging.error(f"Error retrieving bidding history for auction {auction_id}: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500



if __name__ == '__main__':
    app.run(port=5005)


