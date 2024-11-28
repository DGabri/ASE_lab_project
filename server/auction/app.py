from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


import logging
import sqlite3
import time
from venv import logger
from flask_cors import CORS
from auction_service import AuctionService
from auctions_DAO import AuctionDAO

from flask import Flask, abort, json, request, jsonify
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

@app.route('/create_auction', methods=['POST'])
def create_auction():
    try:
        data = request.get_json()
        logging.debug(f"Received data: {data}")

        piece_id = data.get('piece_id')
        creator_id = data.get('creator_id')
        start_price = data.get('start_price')
        end_date = data.get('end_date')

        if not piece_id or not creator_id or not start_price or not end_date:
            logging.error("Missing required fields")
            return jsonify({"error": "Missing required fields"}), 400

        if start_price <= 0:
            logging.error("Invalid start price")
            return jsonify({"error": "Start price must be greater than zero"}), 400

        try:
            if 'T' in end_date:
                end_date = end_date.replace('T', ' ') 
            datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logging.error(f"Invalid end_date format: {e}")
            return jsonify({"error": "Invalid end_date format, expected 'YYYY-MM-DD HH:MM:SS'"}), 400

        logging.debug(f"Start price: {start_price}, End date: {end_date}")

        auction_id = auction_service.create_auction(piece_id, creator_id, start_price, end_date)
        logging.debug(f"Auction created with ID: {auction_id}")
        return jsonify({"id": auction_id, "message": "Auction created successfully."}), 201

    except Exception as e:
        logging.error(f"Error occurred: {e}")
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

@app.route('/bid/<int:auction_id>', methods=['POST'])
def place_bid(auction_id):
    try:
        data = request.get_json()

        if not data or 'user_id' not in data or 'bid_amount' not in data:
            return jsonify({"error": "Missing user_id or bid_amount"}), 400

        user_id = data['user_id']
        bid_amount = data['bid_amount']

        if bid_amount <= 0:
            return jsonify({"error": "Bid amount must be greater than zero"}), 400

        auction = auction_service.get_auction_by_id(auction_id)
        if auction is None:
            return jsonify({"error": "Auction not found"}), 404

        if auction.get('status') != 'active':
            return jsonify({"error": "Auction is not active"}), 400

        current_price = auction.get('current_price', 0)
        if bid_amount <= current_price:
            return jsonify({
                "error": f"Bid amount must be greater than the current price of {current_price}."
            }), 400

        updated_auction = auction_service.place_bid(auction_id, user_id, bid_amount)

        return jsonify({
            "message": "Bid placed successfully",
            "new_price": updated_auction['current_price']
        }), 200

    except ValueError as ve:
        return jsonify({"error": f"Invalid value: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/running/all', methods=['GET'])
def get_active_auctions():
    try:
        auctions = auction_service.get_active_auctions()
        return jsonify(auctions),200
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching active auctions"}), 500

@app.route('/history', methods=['GET'])
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

@app.route('/modify/<int:auction_id>', methods=['PUT'])
def modify_auction(auction_id):
    try:
        auction = auction_service.get_auction_by_id(auction_id)
        if auction is None:
            return jsonify({"error": "Auction not found"}), 404

        data = request.get_json()
        response = auction_service.modify_auction(auction_id, data)

        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
###############other routes##########
#
#@app.route('/close_auction', methods=['POST'])
#def close_auction():
#    data = request.get_json()
 #   data = request.get_json()
 #   auction_id = data['auction_id']
  #  response = auction_service.close_auction(auction_id)
  #  return jsonify(response)

#@app.route('/auction/test', methods=['GET'])
#def test():
  #  return jsonify({"message": "Server is up and running!"})

#@app.route('/close_expired_auctions', methods=['POST'])
#def close_expired_auctions():
  #  response = auction_service.close_expired_auctions()
  ##  return jsonify(response)


#@app.route('/auction/<int:auction_id>/bidding_history', methods=['GET'])
#def get_bidding_history(auction_id):
   # try:
    #    bidding_history = auction_service.get_market_history(auction_id)
        
     #   if bidding_history["status"] == "error":
     #       return jsonify(bidding_history), 404 
      #  return jsonify(bidding_history), 200 

   # except Exception as e:
       # logging.error(f"Error retrieving bidding history for auction {auction_id}: {e}")
       # return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500



if __name__ == '__main__':
    app.run()
