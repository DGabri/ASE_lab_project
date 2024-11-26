from wtforms.validators import Email, InputRequired, Length, NumberRange, DataRequired
from wtforms import StringField, IntegerField
from password_strength import PasswordPolicy
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from wtforms import StringField
from flask_wtf import FlaskForm
from auth_DAO import AuthDAO
from functools import wraps
import requests
import datetime
import logging
import bcrypt
import json
import uuid
import jwt

app = Flask(__name__)

# configure logging
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
    username = StringField(validators=[
        InputRequired(message="Username required"), 
        InputRequired(message="Username required"), 
        Length(min=1, max=15, message="Username len must be between 1 and 15 chars long")])
    email = StringField(validators=[Email(message="Email is invalid"), InputRequired(message="Email required")])
    password = StringField('password', [InputRequired(message="Password is required")])
    user_type = IntegerField('user_type', validators=[
            DataRequired(message="User type required"),
            NumberRange(min=0, max=1, message="User type must be 0 (admin) or 1 (player)"),
        ])

# routes permission mapping
ROUTE_PERMISSIONS = {
    # user routes
    'DELETE:/player/<player_id>': [1, 0],          # delete account
    'PUT:/player/<player_id>': [1, 0],             # modify account username
    'GET:/player/collection/<player_id>': [1, 0],  # see player collection
    'PUT:/player/gold/<player_id>': [1, 0],        # refill user gold
    'PUT:/player/<player_id>': [1, 0],             #
    
    # admin routes
    'GET:/player/all': [0],                            # get all users
    'GET:/player/<player_id>': [0],                    # get a specific user
    'PUT:/admin/user/<user_id>/modify': [0],           # modify a user
    'PUT:/admin/user/ban/<user_id>': [0],              # ban user
    'PUT:/admin/user/unban/<user_id>': [0],            # unban user
    'GET:/player/gold/history/<player_id>': [0],       # get user gold refill history
    'PUT:/admin/user/market-history/<user_id>': [0]    # get user market history
}

# as defined in auth_scheme.sql
VALID_USER_TYPES = {
    0: "admin",
    1: "player"
}
##########################################################
# DB INITIALIZATION
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
        db = AuthDAO(config_json["db"]["db_name"])
        
        # read db initialization scheme from sql file
        with open(config_json["db"]["init_scheme"], 'r') as f:
            init_scheme_sql = f.read()
            db.cursor.executescript(init_scheme_sql)
            logger.warning("DB init successful")
        return db
    
    except Exception as e:
        logger.error(f"DB init failed: {str(e)}")
        raise

def init_admin(config):  
    try:
        # check if admin already exists
        db_connector.cursor.execute(
            "SELECT COUNT(*) FROM users WHERE user_type = 0"
        )
        admin_count = db_connector.cursor.fetchone()[0]
        
        if admin_count > 0:
            logger.info("Admin user already exists, skipping initialization")
            return
        
        # read admin credentials from config
        admin_info = config["admin_credentials"]
        
        # admin registration form
        admin_data = {
            'username': admin_info['username'],
            'email': admin_info['email'],
            'password': admin_info['password'],
            'user_type': admin_info['user_type']
        }
        
        # Generate password hash
        password_bytes = admin_data['password'].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        # Prepare user info for database
        user_info = {
            'username': admin_data['username'],
            'email': admin_data['email'],
            'password': hashed_password,
            'user_type': admin_data['user_type']
        }
        
        # create user in auth database
        user_id, err_msg = db_connector.create_user(user_info)
        
        if err_msg:
            logger.error(f"Failed to create admin user: {err_msg}")
            return
            
        # call user service to add admin
        user_data = {
            'username': admin_data['username'],
            'email': admin_data['email'],
            'user_id': user_id
        }
        
        try:
            res = requests.post(
                "http://user:5000/create_user",
                json=user_data,
                timeout=10
            )
            
            if res.status_code != 201:
                logger.error("Failed to sync admin with user service")
                db_connector.delete_user(user_id)
                return
                
            logger.info("Default admin user created successfully")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"User service connection failed: {str(e)}")
            db_connector.delete_user(user_id)
            
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        if 'user_id' in locals():
            db_connector.delete_user(user_id)


# read config
config = load_config()

app.config.update(
    SECRET_KEY=config["SECRET_KEY"],
    JWT_SECRET_KEY=config["JWT_SECRET_KEY"],
    ISSUER=config["ISSUER"],
    AUDIENCE=config["AUDIENCE"],
    ALGORITHM=config["ALGORITHM"],
    ACCESS_TOKEN_EXPIRE_MINUTES=config["ACCESS_TOKEN_EXPIRE_MINUTES"],
    REFRESH_TOKEN_EXPIRE_DAYS=config["REFRESH_TOKEN_EXPIRE_DAYS"]
)

app.config['WTF_CSRF_ENABLED'] = False

# get db connection DAO
db_connector = init_db(config)
init_admin(config)
##########################################################

def create_id_token(user_data):
    """Create an OIDC-compliant ID token"""
    now = datetime.datetime.now(datetime.UTC)
    payload = {
        "iss": app.config['ISSUER'],
        "sub": str(user_data['user_id']),
        "aud": app.config['AUDIENCE'],
        "exp": now + datetime.timedelta(minutes=app.config['ID_TOKEN_EXPIRE_MINUTES']),
        "iat": now,
        "auth_time": now,
        "nonce": str(uuid.uuid4()),
        "preferred_username": user_data['username'],
        "email": user_data['email'],
        "role": VALID_USER_TYPES[user_data['user_type']]
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['ALGORITHM'])

# given user data create jwt
def generate_access_token(user_data):
    """Create an OAuth2.0-compliant access token"""
    now = datetime.datetime.now(datetime.UTC)
    
    payload = {
        "iss": app.config['ISSUER'],
        "sub": str(user_data['user_id']),
        "aud": app.config['AUDIENCE'],
        "exp": now + datetime.timedelta(minutes=app.config['ACCESS_TOKEN_EXPIRE_MINUTES']),
        "iat": now,
        "jti": str(uuid.uuid4()),
        "user_type": int(user_data['user_type']),
        "role": VALID_USER_TYPES[int(user_data['user_type'])]
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['ALGORITHM'])

# refresj the token
def generate_refresh_token(user_id):
    """Generate a refresh token with expiration"""
    now = datetime.datetime.now(datetime.UTC)
    expires_at = now + datetime.timedelta(days=app.config['REFRESH_TOKEN_EXPIRE_DAYS'])
    
    payload = {
        "iss": app.config['ISSUER'],
        "sub": str(user_id),
        "exp": expires_at,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['ALGORITHM'])
    return token, expires_at

# extract current user from auth header
def get_current_user():
    auth_header = request.headers.get('Authorization')
    
    # no header provided
    if not auth_header:
        return None
    
    try:
        # extract token
        token = auth_header.split(' ')[1]
        payload, error = verify_token(token)
        if error:
            return None
        return payload
    except:
        return None
    
# validate jwt
def verify_token(token):
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token,
            app.config["JWT_SECRET_KEY"],
            algorithms=[app.config['ALGORITHM']],
            audience=app.config['AUDIENCE'],
            issuer=app.config['ISSUER']
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

def requires_auth(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Authorization header is missing'}), 401
            
            try:
                # extract token and verify it
                token = auth_header.split(' ')[1]
                payload, error = verify_token(token)
                
                if error:
                    return jsonify({'error': error}), 401
                
                if payload['user_type'] not in allowed_roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 401
        return decorated
    return decorator

@app.route('/create_user', methods=['POST'])
def register():
    try:
        # validate user registration form data
        user_registration_form = UserRegistrationForm()
        
        # check if there are errors
        if not user_registration_form.validate():
            errors = {}
            for field, field_err in user_registration_form.errors.items():
                errors[field] = field_err
            return jsonify({'error': errors}), 400
        
        data = request.get_json()
        
        try:
            user_type = int(data['user_type'])
            if user_type not in VALID_USER_TYPES:
                return jsonify({'error': 'Invalid user type'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'User type must be an integer'}), 400
        
        user_info = {
            'username': data['username'],
            'email': data['email'],
            'password': data['password'],
            'user_type': user_type,
        }
        logger.warning(f"User_info: {user_info}")

        # validate password requirements
        valid_password = password_requirements.test(user_info["password"])
        
        if len(valid_password) > 0:
            db_connector.log_action(user_id, "ERR_create_player", "Invalid pwd")
            return jsonify({'error': 'Password must be at least 8 characters, contain an uppercase char and two numbers'}), 400    
        
        # generate password hash
        password_bytes = user_info["password"].encode("utf-8")
        salt = bcrypt.gensalt()
        user_info["password"] = bcrypt.hashpw(password_bytes, salt)
        
        logger.warning(f"Password bytes: {password_bytes}")
        logger.warning(f"User_info: {user_info}")
        # create user in auth database
        user_id, err_msg = db_connector.create_user(user_info)
        logger.warning(f"User id: {user_id}")
        
        if err_msg:
            return jsonify({'error': err_msg}), 400
            
        # call user service to add user
        user_data = {
            'username': data['username'],
            'email': data['email'],
            'user_id': user_id
        }
        logger.warning(f"User data for user service: {user_data}")
        try:
            res = requests.post("http://user:5000/create_user", json=user_data, timeout=10)
            
            if res.status_code != 201:
                # rollback user creation
                db_connector.delete_user(user_id)
                return jsonify({'error': 'Registration failed'}), 400
            
            # registration successful            
            return jsonify({'rsp': 'User created correctly', 'id': user_id}), 201

        except:
            return jsonify({'msg': 'Registration failed'}), 400
                    
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.warning(f"Login attempt for username: {data.get('username')}")
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing credentials'}), 400

        user_data, error = db_connector.verify_credentials(
            data['username'],
            data['password']
        )
        
        if error:
            logger.warning(f"Authentication failed: {error}")
            return jsonify({'error': "Wrong credentials"}), 401

        logger.warning(f"User authenticated successfully: {user_data}")

        # generate access and refresh tokens
        try:
            # Fixed: Add missing scope parameter
            access_token = generate_access_token(user_data)
            refresh_token, expires_at = generate_refresh_token(user_data['user_id'])
            expires_at = datetime.datetime.now(datetime.UTC) + timedelta(days=app.config['REFRESH_TOKEN_EXPIRE_DAYS'])

            # save refresh token to db
            db_connector.store_refresh_token(refresh_token, user_data['user_id'], expires_at)

            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'expires_in': app.config['ACCESS_TOKEN_EXPIRE_MINUTES'],
                'user': {
                    'id': user_data['user_id'],
                    'username': user_data['username'],
                    'user_type': user_data['user_type'],
                    'role': VALID_USER_TYPES[int(user_data['user_type'])]
                }
            }), 200

        except Exception as token_error:
            logger.error(f"Token generation error: {str(token_error)}", exc_info=True)
            return jsonify({'error': 'Error generating tokens'}), 500

    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/logout', methods=['POST'])
def logout():
    try:
        auth_header = request.headers.get('Authorization')
        refresh_token = request.json.get('refresh_token')
        
        if not auth_header:
            return jsonify({'error': 'Missing Authorization header'}), 401
        
        try:
            # get access token
            access_token = auth_header.split(' ')[1]
            payload, error = verify_token(access_token)
            
            if error:
                return jsonify({'error': error}), 401
                
            # extract user id from payload
            user_id = payload['user_id']
                
            # If refresh token provided, only invalidate that specific token
            if refresh_token:
                success = db_connector.revoke_user_refresh_token(user_id)
                      
                if success:  
                    return jsonify({'msg': 'Logged out successfully'}), 200
                
                return jsonify({'error': 'Error revoking token'}), 400
            
        except Exception as e:
            return jsonify({'error': "Error revoking token"}), 400
            
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
    
@app.route('/refresh', methods=['POST'])
def refresh():
    try:
        refresh_token = request.json.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400

        user_id = db_connector.verify_refresh_token(refresh_token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401

        # extract user to generate access token
        db_connector.cursor.execute(
            'SELECT user_type FROM users WHERE id = ?',
            (user_id)
        )
        user = db_connector.cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_data = {
            'user_id': user_id,
            'user_type': user[1]
        }
        
        new_access_token = generate_access_token(user_data)
        
        return jsonify({ 'access_token': new_access_token, 'token_type': 'bearer', 'expires_in': app.config['JWT_EXPIRATION_DAYS']}), 200

    except Exception as e:
        logger.error(f'Token refresh error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
    
@app.route('/delete_user/<int:player_id>', methods=['DELETE'])
def delete(user_id):
    try:
        refresh_token = request.json.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400

        # have to be authenticated to delete user
        user_id = db_connector.verify_refresh_token(refresh_token)
        
        if not user_id:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401

        # delete user from auth db
        rsp, err = db_connector.delete_user(user_id["user_id"])
        
        if err:
            return jsonify({'error': 'error deleting user'}), 404

        
        return jsonify({'rsp': "user deleted successfully"}), 200

    except Exception as e:
        logger.error(f'Token refresh error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

##
def normalize_route(route):
    """
    Normalize route by replacing numeric IDs with placeholders
    Example: 'player/gold/1' -> 'player/gold/{player_id}'
    """
    if not route.startswith('/'):
        route = '/' + route
        
    parts = route.split('/')
    normalized_parts = []
    
    for part in parts:
        # Check if part is numeric (an ID)
        if part.isdigit():
            # Determine placeholder based on route context
            if 'player' in parts:
                normalized_parts.append('<player_id>')
            elif 'user' in parts:
                normalized_parts.append('<user_id>')
            else:
                normalized_parts.append('<id>')
        else:
            normalized_parts.append(part)
    
    return '/'.join(normalized_parts)

@app.route('/authorize', methods=['POST'])
def authorize():
    try:
        token = request.json.get('token')
        route = request.json.get('route')
        method = request.json.get('method')
        
        if not all([token, route, method]):
            return jsonify({'error': 'Please provide: token, route and method '}), 400

        payload, error = verify_token(token)
        
        if error:
            return jsonify({'error': error}), 401

        user_type = payload['user_type']
        normalized_route = normalize_route(route)
        
        route_key = f"{method}:{normalized_route}"
        logger.warning(f"Original route: {route}")
        logger.warning(f"Normalized route key: {route_key}")
        logger.warning(f"User type: {user_type}")
        
        
        logger.warning(f"Available routes: {list(ROUTE_PERMISSIONS.keys())}")
        allowed_roles = ROUTE_PERMISSIONS.get(route_key)
        logger.warning(f"Matching route: {route_key} -> allowed roles: {allowed_roles}")

        logger.warning(f"User_type: {user_type} Allowed roles: {allowed_roles}")

        if not allowed_roles:
            return jsonify({'error': 'Route not found', 'requested': route_key}), 404

        if user_type not in allowed_roles:
            return jsonify({'error': 'Insufficient permissions'}), 403

        return jsonify({'valid': True, 'user': payload}), 200

    except Exception as e:
        logger.error(f'Token verification error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/user/modify', methods=['PUT'])
def modify_user():
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'username' not in data:
            return jsonify({'error': 'username and user_id required'}), 400
            
        new_user_info = {
            'user_id': data['user_id'],
            'username': data['username']
        }
        
        # update db
        res, msg = db_connector.modify_user_account(new_user_info)
        
        if res:
            return jsonify({'rsp': msg}), 200
        else:
            return jsonify({'error': msg}), 400
            
    except Exception as e:
        logger.error(f"Error modifying user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
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


if __name__ == '__main__':
    app.run()