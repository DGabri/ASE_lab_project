import logging
from auctions_DAO import AuctionDAO
from flask import Flask, request, jsonify

app = Flask(__name__)
database_path = 'auction.db'
auction_dao = AuctionDAO(database=database_path)

class AuctionService:
    def __init__(self, auction_dao):
        self.auction_dao = auction_dao

    def create_auction(self, piece_id, start_price, end_time):
        """Creates a new auction with the given piece, start price, and end time."""
        try:
            self.auction_dao.create_auction(piece_id, start_price, end_time)
            return {"message": "Auction created successfully."}
        except Exception as e:
            logging.error("Error in create_auction: %s", e)
            return {"error": "Failed to create auction due to an internal error."}

    def place_bid(self, auction_id, user_id, bid_amount):
        """Places a bid on an auction, ensuring it is higher than the current highest bid."""
        try:
            highest_bid = self.auction_dao.get_highest_bid(auction_id)
            
            if highest_bid and bid_amount <= highest_bid[0]['bid_amount']:
                return {"error": "Bid must be higher than the current highest bid."}

            self.auction_dao.add_bid(auction_id, user_id, bid_amount)
            return {"message": "Bid placed successfully."}
        except ValueError as ve:
            logging.warning("Validation error placing bid for auction %s: %s", auction_id, ve)
            return {"error": str(ve)}
        except Exception as e:
            logging.error("Error placing bid for auction %s: %s", auction_id, e)
            return {"error": "Failed to place bid due to an internal error."}

    def close_auction(self, auction_id):
        """Closes an auction and awards the item to the highest bidder, if any."""
        try:
            highest_bid = self.auction_dao.get_highest_bid(auction_id)
            if highest_bid:
                winner_id = highest_bid[0]['user_id']
                piece_id = self.auction_dao.get_piece_id(auction_id)
                
                self.award_piece_to_winner(winner_id, piece_id)

            self.auction_dao.close_auction(auction_id)
            return {"message": "Auction closed and winner awarded."}
        except Exception as e:
            logging.error("Error closing auction %s: %s", auction_id, e)
            return {"error": "Failed to close auction due to an internal error."}

    def award_piece_to_winner(self, user_id, piece_id):
        """Awards the auction piece to the winning user (to be implemented based on system)."""
        try:
            # Placeholder for awarding logic
            logging.info("Awarding piece %s to user %s", piece_id, user_id)
            # Implement actual transfer logic here
        except Exception as e:
            logging.error("Error awarding piece %s to user %s: %s", piece_id, user_id, e)
            raise Exception("Failed to award piece to winner.")

# Correct initialization by passing the 'database' parameter
auction_dao = AuctionDAO(database=database_path)  # Provide the database path here
auction_service = AuctionService(auction_dao)


# Definire gli endpoint Flask
@app.route('/create_auction', methods=['POST'])
def create_auction():
    try:
        data = request.get_json()
        piece_id = data['piece_id']
        start_price = data['start_price']
        end_time = data['end_time']
        
        # Validazione dei dati ricevuti
        if not piece_id or not start_price or not end_time:
            return jsonify({"error": "Missing required fields"}), 400
        
        response = auction_service.create_auction(piece_id, start_price, end_time)
        return jsonify(response)
    except Exception as e:
        logging.error("Error in creating auction: %s", e)
        return jsonify({"error": "An error occurred while processing the request"}), 500


@app.route('/place_bid', methods=['POST'])
def place_bid():
    data = request.get_json()
    auction_id = data['auction_id']
    user_id = data['user_id']
    bid_amount = data['bid_amount']
    response = auction_service.place_bid(auction_id, user_id, bid_amount)
    return jsonify(response)

@app.route('/close_auction', methods=['POST'])
def close_auction():
    data = request.get_json()
    auction_id = data['auction_id']
    response = auction_service.close_auction(auction_id)
    return jsonify(response)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Server is up and running!"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
