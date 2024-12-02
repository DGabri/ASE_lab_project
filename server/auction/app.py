from flask import Flask, json, request, jsonify
from auctions_DAO import AuctionsDAO
import requests
import logging
import signal
import time

app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = False

with open('config.json') as config_file:
    config = json.load(config_file)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging = logging.getLogger(__name__)

db_connector = AuctionsDAO(config['db']['name'])

########################
# Auctions check
def check_auctions(signum, frame):
    """Signal handler to check for ended auctions"""
    try:
        logging.info("[AUCTION CHECK] Checking for ended auctions...")
        ended_auctions = db_connector.get_ended_auctions()
        logging.info(f"[AUCTION CHECK] Found {len(ended_auctions) if ended_auctions else 0} ended auctions")
        logging.info(f"[ENDED AUCTIONS] {ended_auctions}")
        if ended_auctions:
            for auction in ended_auctions:
                try:
                    auction_id = auction['auction_id']
                    logging.info(f"[AUCTION CHECK] Processing auction: {auction_id}")
                    
                    auction_complete_data, error = db_connector.complete_auction(auction_id)
                    if error:
                        logging.error(f"[AUCTION CHECK] Failed to complete auction {auction_id}: {error}")
                        continue
                        
                    logging.info(f"[AUCTION CHECK] Auction {auction_id} completed with data: {auction_complete_data}")
                    
                    # update winner collection
                    if auction_complete_data and auction_complete_data.get('winner_id'):
                        try:
                            res = requests.post(
                                "https://user:5000/update_collection",
                                json=auction_complete_data,
                                timeout=10, 
                                verify=False
                            ) # nosec
                            
                            if not res.ok:
                                logging.error(f"[AUCTION CHECK] Failed to update collection: Status {res.status_code}, Response: {res.text}")
                                
                        except requests.exceptions.RequestException as e:
                            logging.error(f"[AUCTION CHECK] User service connection failed: {str(e)}")
                            continue
                except Exception as e:
                    logging.error(f"[AUCTION CHECK] Error processing auction {auction[0]}: {str(e)}", exc_info=True)
                    continue
        else:
            logging.info("[AUCTION CHECK] No ended auctions found")
            
    except Exception as e:
        logging.error(f"[AUCTION CHECK] Error in auction check: {str(e)}", exc_info=True)
    finally:
        # set next check after 60 seconds
        signal.alarm(60)

signal.signal(signal.SIGALRM, check_auctions)
# initial alarm
signal.alarm(10)

########################
@app.route('/create_auction', methods=['POST'])
def create_auction():
    try:
        data = request.get_json()
        required_fields = {'seller_id', 'piece_id', 'start_price', 'duration_hours'}
        
        if not all(field in data for field in required_fields):
            return jsonify({'err': 'Missing required fields'}), 400
        
        try:
            seller_id = int(data['seller_id'])
            piece_id = int(data['piece_id'])
            start_price = float(data['start_price'])
            duration_hours = float(data['duration_hours'])
        except:
            return jsonify({'err': 'seller_id, piece_id must be int. start_price and duration_hours float'}), 400
            
        if start_price <= 0:
            return jsonify({'err': 'Starting price must be non zero and positive'}), 400
        
        if duration_hours <= 0:
            return jsonify({'err': 'Duration in hours must be positive'}), 400
        
        # check if requesting user and seller_id are the same
        try:
            auth_response = requests.post(
                "https://auth:5000/introspect",
                json={'user_id': seller_id},
                headers={'Authorization': request.headers.get('Authorization')},
                timeout=10,
                verify=False
            ) # nosec
            
            if not auth_response.ok:
                return jsonify({'err': 'You cannot create an auction on behalf of another user'}), auth_response.status_code
                
        except requests.exceptions.RequestException as e:
            return jsonify({'err': f'Error verifying user authorization: {str(e)}'}), 500
        
        # check if user has piece
        try:
            response = requests.get(
                f"https://user:5000/user/has_piece/{seller_id}/{piece_id}",
                timeout=10,
                verify=False
            ) # nosec
            
            is_owner = response.json()
            
            if not is_owner.get('success') or not is_owner.get('has_piece'):
                return jsonify({'err': f'Seller: {seller_id} does not have: {piece_id} in the collection'}), 400
        except requests.exceptions.RequestException as e:
            return jsonify({'err': f'Error veryfing piece: {str(e)}'}), 500

        # register auction in db
        auction_id, error = db_connector.create_auction(
            seller_id, 
            piece_id,
            start_price, 
            duration_hours
        )
        
        if error:
            return jsonify({'err': error}), 400
        
        return jsonify({'auction_id': auction_id}), 201

    except Exception as e:
        return jsonify({'err': f'Internal server error: {e}'}), 500
    
# get info on a specific auction
@app.route('/auction/<int:auction_id>', methods=['GET'])
def get_auction_info(auction_id):
    try:
        auction = db_connector.get_auction(auction_id)
                
        if not auction:
            return jsonify({'err': 'Auction not found'}), 404
        
        return jsonify({
            'auction_id': auction[0],
            'seller_id': auction[1],
            'piece_id': auction[2],
            'start_price': auction[3],
            'current_price': auction[4],
            'end_time': auction[5],
            'status': auction[6],
            'winner_id': auction[7],
            'created_at': auction[8],
            'bid_count': auction[9]
        }), 200
        
    except Exception as e:
        return jsonify({'err': f'Internal server error: {e}'}), 500

# place a bid if you can
@app.route('/bid/<int:auction_id>', methods=['POST'])
def place_bid(auction_id):
    try:
        data = request.get_json()
        if not all(field in data for field in ['bidder_id', 'bid_amount']):
            return jsonify({'err': 'Missing required fields'}), 400

        # check bid seller
        auction = db_connector.get_auction(auction_id)

        if auction is None:
            return jsonify({'err': 'Auction not found'}), 404

        # prevent after end bidding
        # extract auction end time auction[5]
        current_time = int(time.time())
        
        if current_time >= auction[5]:
            return jsonify({'err': 'Auction has ended'}), 400

        # prevent bidding on own auction
        # extract auction bidder_id auction[5]
        bidder_id = data['bidder_id']
        if auction[1] == bidder_id:  
            return jsonify({'err': 'Bidding on own auction forbidden'}), 400
        
        # prevent consecutive bids
        last_bid = db_connector.get_last_bid(auction_id)        
        if last_bid and last_bid['bidder_id'] == bidder_id:
            return jsonify({'err': 'Last bidder id is the same'}), 400
        
        # Check user balance if he can bid
        try:
            response = requests.get(
                f"https://user:5000/user/balance/{bidder_id}",
                timeout=10,
                verify=False
            ) # nosec
            balance_data = response.json()
            if not balance_data.get('success') or balance_data.get('balance', 0) < float(data['bid_amount']):
                return jsonify({'err': 'Insufficient balance'}), 400
        except requests.exceptions.RequestException as e:
            return jsonify({'err': f'Failed to verify balance: {str(e)}'}), 500

        success, error = db_connector.place_bid(
            auction_id, bidder_id, float(data['bid_amount'])
        )
        
        if error:
            return jsonify({'err': error}), 400
        return jsonify({'message': 'Bid placed successfully'}), 200
    
    except Exception as e:
        logging.error(f"Error in place_bid: {str(e)}")
        return jsonify({'err': f'Internal server error: {e}'}), 500

# get all active auctions
@app.route('/running/all', methods=['GET'])
def get_active_auctions():
    try:
        auctions = db_connector.get_active_auctions()
        logging.info(f"[AUCTION] Active auctions: {auctions}")
        return jsonify({
            'auctions': [{
                'auction_id': auction[0],
                'seller_id': auction[1],
                'piece_id': auction[2],
                'current_price': auction[4],
                'end_time': auction[5],
                'bid_count': auction[9],
                'best_bidder_id': auction[10] if len(auction) > 10 else None
            } for auction in auctions]
        }), 200
    except Exception as e:
        logging.error(f"Error in get_active_auctions: {str(e)}")
        return jsonify({'err': f'Internal server error: {e}'}), 500
    
# get historical auctions
@app.route('/history', methods=['GET'])
def get_past_auctions():
    try:
        
        auctions = db_connector.get_completed_auctions()
        logging.info(f"[ENDED AUCTIONS] Auctions: {auctions}")
        
        return jsonify({'auctions': auctions}), 200
        
    except Exception as e:
        return jsonify({'err': f'Internal server error: {e}'}), 500

# get auctions about piece_id
@app.route('/running/<int:piece_id>', methods=['GET'])
def get_active_auctions_by_piece_id(piece_id):
    try:
        auctions = db_connector.get_active_auctions_by_piece_id(piece_id)
        return jsonify({
            'auctions': [{
                'auction_id': a[0],
                'seller_id': a[1],
                'piece_id': a[2],
                'current_price': a[4],
                'end_time': a[5],
                'bid_count': a[9],
                'best_bidder_id': a[10]
            } for a in auctions]
        }), 200
        
    except Exception as e:
        return jsonify({'err': f'Internal server error: {e}'}), 500

# modify end time of auction
@app.route('/modify/<int:auction_id>', methods=['PUT'])
def modify_auction(auction_id):
    try:
        data = request.get_json()
        if 'seller_id' not in data:
            return jsonify({'err': 'Missing seller_id'}), 400
        
        success, error = db_connector.modify_auction(auction_id, data['seller_id'], data)
        
        if error:
            return jsonify({'err': error}), 400
        return jsonify({'message': 'Auction modified successfully'}), 200
    
    except Exception as e:
        logging.error(f"Error in modify_auction: {str(e)}")
        return jsonify({'err': f'Internal server error: {e}'}), 500

if __name__ == '__main__':
    app.run()
    