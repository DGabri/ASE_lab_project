from flask import Flask, request, jsonify
from users_DAO import UsersDAO
import logging
import json
import bcrypt
from wtforms.validators import Email, InputRequired, Length
from wtforms import StringField
from flask_wtf import FlaskForm
from password_strength import PasswordPolicy
from werkzeug.exceptions import HTTPException

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
        raise RuntimeError(f"Config not found")
    
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON in config")

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
        logger.error(f"DB init failed: {str(e)}")
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
            return jsonify({'error': 'Missing required fields'}), 400
        
        user_info = {
            'username': data['username'],
            'email': data['email'],
            'user_id': data['user_id']
        }
        
        logger.info(f"Received create user request with data: {data}")
        
        # validate user id as int
        try:
            data['user_id'] = int(data['user_id'])
        except (ValueError, TypeError):
            return jsonify({'error': 'user_id must be int'}), 400
            
        # create user in DB, get error message if any
        user_id, err_msg = db_connector.create_user_account(user_info)
        logger.warning(f"Created User ID: {user_id}, error msg: {err_msg}")
            
        if err_msg:
            logger.error(f"Error creating user: {err_msg}")
            db_connector.log_action(user_id, "ERR_create_player", err_msg)
            return jsonify({'error': err_msg}), 400
            
        if user_id:
            logger.info(f"Successfully created user with ID: {user_id}")
            db_connector.log_action(user_id, "create_player", "created_user")
            return jsonify({'rsp': 'User created correctly', 'id': user_id}), 201
        
        db_connector.log_action(user_id, "ERR_create_player", "Error creating account")
        return jsonify({'error': 'error creating account'}), 500

    except Exception as e:
        app.logger.error(f'Error creating user: {str(e)}')
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# Delete account
@app.route('/player/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):

    if player_id is None:
        db_connector.log_action(player_id, "ERR_delete_user", "User id to delete not provided")
        return jsonify({'error': 'Please provide a player id to delete'}), 400
        
    res, msg = db_connector.delete_user_account(player_id)
    
    if res:
        db_connector.log_action(player_id, "delete_user", f"Deleted user: {player_id}")
        return jsonify({'rsp': msg}), 200
    
    db_connector.log_action(player_id, "ERR_delete_user", "Error deleting user")
    return jsonify({'error': f'Error deleting player: {msg}'}), 400

# Modify account (only username)
@app.route('/player/<int:player_id>', methods=['PUT'])
def update_player(player_id):
    data = request.get_json()
    
    new_user_info = {
        'user_id': player_id,
        'username': data.get('username')
    }
    
    print(new_user_info)
    res, msg = db_connector.modify_user_account(new_user_info)
    
    if res:
        db_connector.log_action(player_id, "modify_user", msg)
        return jsonify({'rsp': msg}), 200
    
    db_connector.log_action(player_id, "ERR_modify_user", msg)
    return jsonify({'error': msg}), 400

# See collection
@app.route('/player/collection/<int:player_id>', methods=['GET'])
def get_player_collection(player_id):

    res, collection, msg = db_connector.get_user_gacha_collection(player_id)
    
    if res:
        db_connector.log_action(player_id, "get_collection", "Retrieved collection for user")
        return jsonify({'rsp': msg, 'collection': collection}), 200
    
    db_connector.log_action(player_id, "ERR_get_collection", "Error retrieving collection for user")
    return jsonify({'error': msg}), 400

# See info of a gacha in my collection
def get_collection_gacha_info(gacha_id):
    #db_connector.log_action(player_id, "ERR_get_collection", "Error retrieving collection for user")
    pass

# See system gacha collection
def get_system_gachas():
    """ Request to pieces service """
    #db_connector.log_action(player_id, "ERR_get_collection", "Error retrieving collection for user")
    pass

# See system gacha collection
def get_system_gacha_info(gacha_id):
    """ Request to pieces service """
    #db_connector.log_action(player_id, "ERR_get_collection", "Error retrieving collection for user")
    pass

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
        return jsonify({'error': 'Error updating balance'}), 400
                
    db_connector.log_action(player_id, "refill_gold", f"Updated balance: {new_balance}")
    return jsonify({'message': 'Successfully updated player gold', 'player_id': player_id, 'new_balance': new_balance}), 200

#######################

##  ADMIN ENDPOINTS  ##
# Check all user profiles
# Modify a specific user
# Check a player currency transaction
# Check player market history
# Check all gacha collection
# Modify gacha collection
# Modify a gacha info

# Check syslog of last 5 minutes
def check_system_logs():
    pass

# Ban player account
@app.route('/admin/user/ban/<int:user_id>', methods=['PUT'])
def ban_user(user_id):

    # pass 0 to ban user
    res, msg = db_connector.admin_set_user_account_status(user_id, 0)
    
    if res:
        db_connector.log_action(user_id, "ban_user", "Ban successful")
        return jsonify({'rsp': msg}), 200
    
    db_connector.log_action(user_id, "ERR_ban_user", "Ban unsuccessful")
    return jsonify({'error': msg}), 400 

# Extra unban user
@app.route('/admin/user/unban/<int:user_id>', methods=['PUT'])
def unban_user(user_id):

    # pass 1 to unban user
    res, msg = db_connector.admin_set_user_account_status(user_id, 1)
    
    if res:
        db_connector.log_action(user_id, "unban_user", "Unban successful")
        return jsonify({'rsp': msg}), 200
    
    db_connector.log_action(user_id, "unban_user", "Unban unsuccessful")
    return jsonify({'error': msg}), 400 
#######################

# Admin Routes
@app.route('/player/all', methods=['GET'])
def get_all_players():

    res, players = db_connector.admin_get_all_users()

    return jsonify({'rsp': players}), 200


@app.route('/player/<int:player_id>', methods=['GET'])
def get_player(player_id):
    res, user = db_connector.admin_get_user(player_id)


@app.route('/admin/user/modify/<int:user_id>', methods=['PUT'])
def admin_modify_user(user_id):

    update = request.get_json()
    
    res, msg = db_connector.admin_modify_user(user_id, update)

@app.route('/player/gold/history/<int:player_id>', methods=['GET'])
def get_player_transaction_history(player_id):

    res, tx_hist = db_connector.admin_get_user_currency_tx(player_id)
    return jsonify({'transactions_history': tx_hist}), 200

@app.route('/admin/user/market-history/<int:user_id>', methods=['PUT'])
def get_user_market_history(user_id):

    res, user_market_hist = db_connector.admin_get_user_market_hist(user_id)
    return jsonify({'market_history': user_market_hist}), 200

def check_all_gacha_collections():
    pass

def check_all_sys_gacha_collections():
    pass

def modify_gacha_collection():
    pass

def check_gacha_info(gacha_id):
    """ PIECE SERVICE QUERY """
    pass

def modify_gacha_info(gacha_id):
    """ PIECE SERVICE QUERY """
    pass

def check_auction_market():
    """ AUCTION SERVICE QUERY """
    pass

if __name__ == '__main__':
    app.run(debug=True)