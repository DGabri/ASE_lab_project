from wtforms.validators import Email, InputRequired, Length
from password_strength import PasswordPolicy
from flask import Flask, request, jsonify
from wtforms import StringField
from flask_wtf import FlaskForm
from users_DAO import UsersDAO
import requests
import logging
import json

app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

#################################################################
## UTILITY FUNCTIONS ##
password_requirements = PasswordPolicy.from_names(
    length=8, # at least 8 chars
    uppercase=1, # at least 1 uppercase
    numbers=2 # at least 2 numbers
)

class UserRegistrationForm(FlaskForm):
    username = StringField(validators=[InputRequired(message="Username required"), InputRequired(message="Username required"), Length(min=1, max=15, message="Username len must be between 1 and 15 chars long")])
    email = StringField(validators=[Email(message="Email is invalid"), InputRequired(message="Email required")])
    password = StringField('password', [InputRequired(message="Password is required")])
    user_type = StringField('user_type', [InputRequired(message="User type required")])

# load config
def load_config():
    config_path = "./config.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
        
    except FileNotFoundError:
        raise RuntimeError(f"[USER] Config not found")
    
    except json.JSONDecodeError:
        raise RuntimeError(f"[USER] Invalid JSON in config")

# db Setup
def init_db(config_json):
    try:
        db = UsersDAO(config_json["db"]["db_name"])
        
        # read db initialization scheme from sql file
        with open(config_json["db"]["init_scheme"], 'r') as f:
            init_scheme_sql = f.read()
            db.cursor.executescript(init_scheme_sql)
            logger.warning("DB init successful")
        return db
    
    except Exception as e:
        logger.error(f"[USER] DB init failed: {str(e)}")
        raise
    
# read config
config = load_config()

# get db connection DAO
db_connector = init_db(config)

#################################################################

## PLAYER ENDPOINTS  ##

# Crete account
@app.route('/create_user', methods=['POST'])
def create_player_account():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['username', 'email', 'user_id']):
            return jsonify({'err': 'Missing required fields'}), 400
        
        # validate user id as int
        try:
            data['user_id'] = int(data['user_id'])
        except (ValueError, TypeError):
            return jsonify({'err': 'user_id must be int'}), 400
            
        user_info = {
            'username': data['username'],
            'email': data['email'],
            'user_id': data['user_id']
        }
        
        logger.info(f"[USER] Received create user request with data: {data}")
        
        # Try to create user - let the database handle uniqueness constraints
        user_id, err_msg = db_connector.create_user_account(user_info)
            
        if err_msg:
            # Check if it's a duplicate - both username and id match
            existing_user = db_connector.get_user_by_id(data['user_id'])
            if existing_user and existing_user['username'] == data['username']:
                return jsonify({'rsp': 'User already exists', 'id': data['user_id']}), 200
                
            # Otherwise it's a conflict (either username or id taken)
            return jsonify({'err': err_msg}), 409
            
        logger.info(f"[USER] Successfully created user with ID: {user_id}")
        db_connector.log_action(user_id, "create_player", "created_user")
        return jsonify({'rsp': 'User created correctly', 'id': user_id}), 201

    except Exception as e:
        logger.error(f'Error creating user: {str(e)}')
        return jsonify({'err': 'Internal server error', 'message': str(e)}), 500
    
# Delete account
@app.route('/player/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):

    if player_id is None:
        db_connector.log_action(player_id, "ERR_delete_user", "User id to delete not provided")
        return jsonify({'err': 'Please provide a player id to delete'}), 400
        
    res, msg = db_connector.delete_user_account(player_id)
    
    if res:
        db_connector.log_action(player_id, "delete_user", f"Deleted user: {player_id}")
        return jsonify({'rsp': msg}), 200
    
    db_connector.log_action(player_id, "ERR_delete_user", "Error deleting user")
    return jsonify({'err': f'Error deleting player: {msg}'}), 400

# Modify account (only username)
@app.route('/player/<int:player_id>', methods=['PUT'])
def update_player(player_id):
    try:
        data = request.get_json()
        logger.info(f"[USER] Received update request for player {player_id}")
        logger.info(f"[USER] Request data: {data}")
        logger.info(f"[USER] Headers: {dict(request.headers)}")
        
        if not data:
            return jsonify({'err': 'No data provided'}), 400
        
        if not data.get('username'):
            return jsonify({'err': 'Username required'}), 400
        
        new_user_info = {
            'user_id': player_id,
            'username': data.get('username')
        }
        
        # update db
        res, msg = db_connector.modify_user_account(new_user_info)
        
        if res:
            db_connector.log_action(player_id, "modify_user", msg)
            
            # get auth token from original request
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                error_msg = "Missing Authorization header for auth service"

                db_connector.log_action(player_id, "ERR_modify_user", error_msg)
                return jsonify({'err': 'Authorization required'}), 401
            
            # update auth service
            try:
                auth_url = f"http://auth:5000/user/modify/{player_id}"
                auth_payload = {'username': data.get('username')}
                               
                auth_response = requests.put(
                    auth_url,
                    headers={'Authorization': auth_header},
                    json=auth_payload,
                    timeout=10
                )
                            
                if auth_response.status_code == 200:
                    return jsonify({'message': msg}), 200
                else:
                    error_msg = f"Auth service update failed: {auth_response.text}"
                    db_connector.log_action(player_id, "ERR_modify_user", error_msg)
                    return jsonify({'err': f'Failed to update authentication service. {error_msg}'}), 500
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Auth service connection error: {str(e)}"
                db_connector.log_action(player_id, "ERR_modify_user", error_msg)
                return jsonify({'err': 'Failed to connect to authentication service'}), 500
        
        db_connector.log_action(player_id, "ERR_modify_user", msg)
        return jsonify({'err': msg}), 400
        
    except Exception as e:
        logger.error(f"[USER] Unexpected error in update_player: {str(e)}")
        return jsonify({'err': str(e)}), 500
    
# See collection
@app.route('/player/collection/<int:player_id>', methods=['GET'])
def get_player_collection(player_id):

    res, collection, msg = db_connector.get_user_gacha_collection(player_id)
    
    if res:
        db_connector.log_action(player_id, "get_collection", "Retrieved collection for user")
        return jsonify({'rsp': msg, 'collection': collection}), 200
    
    db_connector.log_action(player_id, "ERR_get_collection", "Error retrieving collection for user")
    return jsonify({'err': msg}), 400

# Refill gold
@app.route('/player/gold/<int:player_id>', methods=['PUT'])
def update_player_gold(player_id):

    data = request.get_json()
    
    increment_amount = data.get('amount')
    is_refill = data.get('is_refill')

    # error
    if increment_amount is None:
        db_connector.log_action(player_id, "ERR_refill_gold", "Balance not provided")
        return jsonify({'rsp': 'Error updating balance, balance required'}), 400
    
    if is_refill is None:
        db_connector.log_action(player_id, "ERR_refill_gold", "Refill not specfied")
        return jsonify({'rsp': 'Error updating balance. Please specify if this is a refill: True or False'}), 400
    
    # check that increment amount is a number
    try:
        increment_amount = float(increment_amount)
        
        if (increment_amount == 0 and is_refill == False):
            db_connector.log_action(player_id, "ERR_refill_gold", "Negative refill value")
            return jsonify({'rsp': 'Error updating balance, balance must be a positive number > 0'}), 400
    except:
        db_connector.log_action(player_id, "ERR_refill_gold", "Amount is not a number")
        return jsonify({'rsp': 'Error updating balance, balance must be a number'}), 400
        
    
    # update balance
    new_balance, err = db_connector.update_token_balance(player_id, increment_amount, is_refill)

    if err:
        db_connector.log_action(player_id, "ERR_refill_gold", err)
        return jsonify({'rsp': f"Error: {err}"}), 200
        
    if new_balance is None:
        db_connector.log_action(player_id, "ERR_refill_gold", err)
        return jsonify({'err': 'Error updating balance'}), 400
                
    db_connector.log_action(player_id, "refill_gold", f"Updated balance: {new_balance}")
    return jsonify({'message': 'Successfully updated player gold', 'player_id': player_id, 'new_balance': new_balance}), 200

@app.route('/auction/complete', methods=['POST'])
def complete_auction():
    """Handle complete auction outcome including winner and losers"""
    try:
        data = request.get_json()
        required_fields = ['winner_id', 'gacha_id', 'winning_bid', 'losing_bids']
        
        if not all(field in data for field in required_fields):
            return jsonify({'err': 'Missing required fields'}), 400
            
        success, error = db_connector.process_auction_outcome(data)
        
        if success:
            db_connector.log_action(data['winner_id'],"auction_complete",f"Won auction gacha {data['gacha_id']}")
            return jsonify({'message': 'Auction completed successfully','winner_id': data['winner_id'], 'gacha_id': data['gacha_id']}), 200
        else:
            return jsonify({'err': error}), 400
            
    except Exception as e:
        return jsonify({'err': 'Internal server error'}), 500

        
#######################

##  ADMIN ENDPOINTS  ##

# Check syslog of last 5 minutes
@app.route('/admin/logs', methods=['GET'])
def get_logs():
    # get logs from db
    logs, err = db_connector.admin_get_latest_logs()
        
    if err:
        return jsonify({'err': err}), 500
        
    return jsonify({'rsp': logs}), 200

@app.route('/player/all', methods=['GET'])
def get_all_players():

    players, err = db_connector.admin_get_all_users()
    
    if not err:
        return jsonify({'players': players}), 200
    
    return jsonify({'err': err}), 400


@app.route('/player/<int:player_id>', methods=['GET'])
def get_player(player_id):
    user, err = db_connector.admin_get_user(player_id)
    
    if not err:
        return jsonify({'user_info': user}), 200
    
    return jsonify({'err': err}), 400

@app.route('/admin/user/modify/<int:user_id>', methods=['PUT'])
def admin_modify_user(user_id):
    try:
        update = request.get_json()
        
        # get username from request
        new_username = update.get('username')
        
        # username must be present
        if not new_username:
            return jsonify({'err': 'Username required'}), 400

        # update db
        res, msg = db_connector.admin_modify_user(user_id, new_username)
        
        if res:
            return jsonify({'message': 'User updated successfully'}), 200
        else:
            return jsonify({'err': msg}), 400
            
    except Exception as e:
        return jsonify({'err': str(e)}), 500
    
# get transaction history
@app.route('/player/transaction/history/<int:player_id>', methods=['GET'])
def get_player_transaction_history(player_id):

    tx_hist, err = db_connector.admin_get_user_currency_tx(player_id)
    
    if not err:
        return jsonify({'transactions_history': tx_hist}), 200
    
    return jsonify({'err': err}), 400

# get user market history
@app.route('/admin/user/market-history/<int:user_id>', methods=['PUT'])
def get_user_market_history(user_id):

    user_market_hist, err = db_connector.admin_get_user_market_hist(user_id)
    
    if not err:
        return jsonify({'market_history': user_market_hist}), 200
    
    return jsonify({'err': err}), 400

@app.route('/max_user_id', methods=['GET'])
def get_max_user_id():
    try:
        max_id = db_connector.get_max_user_id()
        return jsonify({'max_id': max_id}), 200
    except Exception as e:
        return jsonify({'err': str(e)}), 500
    
if __name__ == '__main__':
    app.run()
    