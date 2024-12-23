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
TESTING = True

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
    user_type = StringField('user_type', [DataRequired(message="User type required")])


# routes permission mapping
ROUTE_PERMISSIONS = {
    # user routes
    'DELETE:/delete_user/<player_id>': [1, 0],     # delete account
    'PUT:/player/<player_id>': [1, 0],             # modify account username
    'GET:/player/collection/<player_id>': [1, 0],  # see player collection
    'PUT:/player/gold/<player_id>': [1, 0],        # refill user gold
    'PUT:/player/<player_id>': [1, 0],             # 
    'POST:/auction/complete': [1],                 # complete auction process
    'POST:/auction': [1,0],                        # create an auction
    'POST:/logout/<player_id>': [1,0],             # logout
    'POST:/token': [1,0],                          # login
    
    # admin routes
    'GET:/admin/logs': [0],                                  # get all logs
    'GET:/player/all': [0],                                  # get all players
    'GET:/player/<player_id>': [0],                          # get a specific user
    'PUT:/admin/user/modify/<user_id>': [0,1],                 # modify a user
    'GET:/admin/player/transaction/history/<player_id>': [0],# get user transaction history
    'GET:/admin/player/market-history/<player_id>': [0],     # get user market history
    'GET:/admin/logs': [0],                                  # get syslog
    
    # auction
    'POST:/create_auction': [1],                # create an auction
    'GET:/auction/<id>': [1, 0],                # get auction by id
    'POST:/bid/<auction_id>': [1],              # bid on an auction
    'POST:/auction/complete': [1],              # complete auction
    'GET:/history': [1, 0],                     # get historical auctions
    'GET:/running/<piece_id>': [1, 0],          # get open auctions with a specific piece id
    'PUT:/modify/<auction_id>': [1, 0],         # modify auction end time
    'GET:/running/all': [1, 0],                 # get all running auctions

    # banner
    'GET:/banner/<banner_id>': [1],             # get banner info
    'POST:/banner': [1],                        # add new banner
    'PUT:/banner/<banner_id>': [1],             # update banner
    'DELETE:/banner/<banner_id>': [1],          # delete a banner
    'GET:/banner/pull/<banner_id>': [1],        # pull a banner
    
    # piece
    'GET:/piece': [1],                          # list all pieces
    'POST:/piece': [1],                         # add new piece
    'PUT:/piece/<piece_id>': [1],               # update a piece
    'GET:/piece/all': [1]                       # get all pieces
}

# as defined in auth_scheme.sql
VALID_USER_TYPES = {
    0: "admin",
    1: "player"
}

# normalize routes to reroute to specific service
def normalize_route(route, method):
    if not route.startswith('/'):
        route = '/' + route
    
    parts = route.split('/')
    full_path = '/'.join(parts)
    normalized_parts = []
    
    for part in parts:
        if part.isdigit():
            if 'bid' in full_path:
                normalized_parts.append('<auction_id>')
            elif '/admin/user/modify' in full_path:
                normalized_parts.append('<user_id>')
            elif '/auction/running' in full_path:
                normalized_parts.append('<piece_id>')
            elif '/auction/auction' in full_path:
                normalized_parts.append('<auction_id>')
            elif '/modify' in full_path:
                normalized_parts.append('<auction_id>')
            elif any(x in full_path for x in ['player', 'delete_user', 'logout']):
                normalized_parts.append('<player_id>')
            elif '/banner' in full_path:
                #  add banner id only for GET PUT and DELETE
                if method in ['GET', 'PUT', 'DELETE']:
                    normalized_parts.append('<banner_id>')
                # POST does not need anything
                elif method == 'POST':
                    continue
                else:
                    normalized_parts.append('<banner_id>')
            elif '/piece' in full_path:
                # only PUT adds piece_id
                if method == 'PUT':
                    normalized_parts.append('<piece_id>')
                # skip others
                else:
                    continue
            elif '/piece' in full_path:
                normalized_parts.append('<piece_id>')
            elif '/running' in full_path:
                normalized_parts.append('<piece_id>')
            elif part == 'all':
                normalized_parts.append('all')
            else:
                normalized_parts.append('<id>')
        else:
            normalized_parts.append(part)
    
    return '/'.join(normalized_parts)

##########################################################
# DB INITIALIZATION
# load config
def load_config():
    config_path = "./config.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
        
    except FileNotFoundError:
        raise RuntimeError(f"[AUTH] Config not found")
    
    except json.JSONDecodeError:
        raise RuntimeError(f"[AUTH] Invalid JSON in config")

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
        logger.error(f"[AUTH] DB init failed: {str(e)}")
        raise

def init_admin(config):  
    try:
        # atomic transaction
        with db_connector.connection:
            
            # check if admin already present
            db_connector.cursor.execute(
                "SELECT COUNT(*) FROM users WHERE user_type = 0"
            )
            admin_count = db_connector.cursor.fetchone()[0]
            
            logging.info(f"[AUTH] Admin count: {admin_count}")
            
            if admin_count > 0:
                logger.info("Admin user already exists, skipping initialization")

                db_connector.cursor.execute("SELECT id, username, email, user_type FROM users")
                users = db_connector.cursor.fetchall()
                logger.info("[AUTH] Current users in DB:")
                for user in users:
                    logger.info(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Type: {user[3]}")
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
            
            # hash password
            password_bytes = admin_data['password'].encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt)
            admin_data['password'] = hashed_password
            
            logging.info(f"[AUTH] Admin data signup: {admin_data}")
            
            # create user in auth database within same transaction
            user_id, err_msg = db_connector.create_user(admin_data)
            
            if err_msg:
                logger.error(f"[AUTH] Failed to create admin user: {err_msg}")
                return
                
            # print db after insertion
            db_connector.cursor.execute("SELECT id, username, email, user_type FROM users")
            users = db_connector.cursor.fetchall()
            logger.info("[AUTH] Users in DB after admin creation:")
            for user in users:
                logger.info(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Type: {user[3]}")
                
            # call user service to add admin
            user_data = {
                'username': admin_data['username'],
                'email': admin_data['email'],
                'user_id': user_id
            }
            
            if not TESTING:
                try:
                    res = requests.post(
                        "https://user:5000/create_user",
                        json=user_data,
                        timeout=10, 
                        verify=False
                    ) # nosec
                    
                    if res.status_code == 200:
                        logger.info("[AUTH] Admin user already exists in user service")
                        # print db after 
                        db_connector.cursor.execute("SELECT id, username, email, user_type FROM users")
                        users = db_connector.cursor.fetchall()
                        logger.info("[AUTH] Final users in DB:")
                        for user in users:
                            logger.info(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Type: {user[3]}")
                        return
                    elif res.status_code == 201:
                        logger.info("[AUTH] Default admin user created successfully")
                        db_connector.connection.commit()
                        # print db after 
                        db_connector.cursor.execute("SELECT id, username, email, user_type FROM users")
                        users = db_connector.cursor.fetchall()
                        logger.info("[AUTH] Final users in DB after successful creation:")
                        for user in users:
                            logger.info(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Type: {user[3]}")
                        return
                    else: 
                        logger.error("[AUTH] Failed to sync admin with user service")
                        raise Exception("Failed to sync with user service")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"[AUTH] User service connection failed: {str(e)}")
                    raise
                            
    except Exception as e:
        logger.error(f"[AUTH] Error creating admin user: {str(e)}")
        if 'db_connector' in locals() and db_connector.connection:
            db_connector.connection.rollback()

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
        "role": VALID_USER_TYPES[int(user_data['user_type'])],
        "scope": None
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

def verify_user_access(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'err': 'Authorization header is missing'}), 401

        try:
            # get token and verify it
            token = auth_header.split(' ')[1]
            payload, error = verify_token(token)
            
            if error:
                return jsonify({'err': error}), 401

            # get the user id from url or request
            target_id = kwargs.get('player_id') or kwargs.get('user_id')
            
            # if user id is not in url get it from body
            if not target_id and request.is_json:
                target_id = request.json.get('user_id')
                
            if not target_id:
                return jsonify({'err': 'No target user specified'}), 400

            # get user id from token
            token_user_id = int(payload.get('sub'))
            
            # permit access if:
            # 1. User is accessing hist data (ID match)
            # 2. User is an admin (user_type = 0)
            if token_user_id != target_id and payload.get('user_type') != 0:
                return jsonify({'err': 'Cannot access or modify other users\' data'}), 403

            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'err': str(e)}), 401
    return decorated

def requires_auth(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'err': 'Authorization header is missing'}), 401
            
            try:
                # extract token and verify it
                token = auth_header.split(' ')[1]
                payload, error = verify_token(token)
                
                if error:
                    return jsonify({'err': error}), 401
                
                if payload['user_type'] not in allowed_roles:
                    return jsonify({'err': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'err': str(e)}), 401
        return decorated
    return decorator

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
            return jsonify({'err': errors}), 400
        
        data = request.get_json()
        
        try:
            user_type = int(data['user_type'])
            if user_type not in VALID_USER_TYPES:
                return jsonify({'err': 'Invalid user type'}), 400
        except (ValueError, TypeError):
            return jsonify({'err': 'User type must be an integer'}), 400
        
        user_info = {
            'username': data['username'],
            'email': data['email'],
            'password': data['password'],
            'user_type': user_type,
        }
        logger.warning(f"[AUTH] User_info: {user_info}")

        # validate password requirements
        valid_password = password_requirements.test(user_info["password"])
        
        if len(valid_password) > 0:
            return jsonify({'err': 'Password must be at least 8 characters, contain an uppercase char and two numbers'}), 400    
        
        # generate password hash
        password_bytes = user_info["password"].encode("utf-8")
        salt = bcrypt.gensalt()
        user_info["password"] = bcrypt.hashpw(password_bytes, salt)
        
        logger.warning(f"[AUTH] Password bytes: {password_bytes}")
        logger.warning(f"[AUTH] User_info: {user_info}")
        # create user in auth database
        user_id, err_msg = db_connector.create_user(user_info)
        logger.warning(f"[AUTH] User id: {user_id}")
        
        if err_msg:
            return jsonify({'err': err_msg}), 400
            
        # call user service to add user
        user_data = {
            'username': data['username'],
            'email': data['email'],
            'user_id': user_id
        }
        logger.warning(f"[AUTH] User data for user service: {user_data}")

        if TESTING and data["username"] == "duplicate_username":
            # rollback user creation
            db_connector.delete_user(user_id)
            return jsonify({'err': 'Username already present'}), 400
        if TESTING:
            return jsonify({'rsp': 'User created correctly', 'id': user_id}), 201
        
        try:
            res = requests.post("https://user:5000/create_user", json=user_data, timeout=10, verify=False) # nosec
            
            if res.status_code != 201:
                # rollback user creation
                db_connector.delete_user(user_id)
                return jsonify({'err': 'Registration failed'}), 400
            
            # registration successful            
            return jsonify({'rsp': 'User created correctly', 'id': user_id}), 201

        except:
            return jsonify({'msg': 'Registration failed'}), 400
                    
    except Exception as e:
        return jsonify({'err': f'Internal server error: {e}'}), 500


@app.route('/token', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.warning(f"[AUTH] Login attempt for username: {data.get('username')}")
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'err': 'Missing credentials'}), 400

        user_data, error = db_connector.verify_credentials(
            data['username'],
            data['password']
        )
        
        if error:
            logger.warning(f"[AUTH] Authentication failed: {error}")
            return jsonify({'err': "Wrong credentials"}), 401

        logger.warning(f"[AUTH] User authenticated successfully: {user_data}")

        # generate access and refresh tokens
        try:
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
            logger.error(f"[AUTH] Token generation error: {str(token_error)}", exc_info=True)
            return jsonify({'err': 'Error generating tokens'}), 500

    except Exception as e:
        logger.error(f"[AUTH] Login error: {str(e)}", exc_info=True)
        return jsonify({'err': 'Internal server error'}), 500


@app.route('/logout/<int:player_id>', methods=['POST'])
def logout(player_id):
    try:
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'err': 'Missing Authorization header'}), 401
        
        try:
            # verify access token
            access_token = auth_header.split(' ')[1]
            payload, error = verify_token(access_token)
            
            if error:
                return jsonify({'err': error}), 401
                
            # verify the user is logging out their own account or is an admin
            token_user_id = int(payload.get('sub'))
            user_type = payload.get('user_type')
            if token_user_id != player_id and user_type != 0:  # Allow admin to logout anyone
                return jsonify({'err': 'Cannot logout other users'}), 403
                
            logger.info(f"[AUTH-LOGOUT] Logging out user: {player_id}")
            success, message = db_connector.revoke_user_refresh_token(player_id)
                    
            if success:  
                return jsonify({'msg': message}), 200
            
            return jsonify({'err': message}), 404  # 404 if no tokens found
            
        except Exception as e:
            logger.error(f"[AUTH] Error during logout: {str(e)}")
            return jsonify({'err': "Error during logout"}), 400
            
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        return jsonify({'err': 'Internal server error'}), 500
    
@app.route('/refresh', methods=['POST'])
def refresh():
    try:
        refresh_token = request.json.get('refresh_token')
        if not refresh_token:
            return jsonify({'err': 'Refresh token required'}), 400

        user_id = db_connector.verify_refresh_token(refresh_token)
        if not user_id:
            return jsonify({'err': 'Invalid or expired refresh token'}), 401

        # extract user to generate access token
        db_connector.cursor.execute(
            'SELECT user_type FROM users WHERE id = ?',
            (user_id)
        )
        user = db_connector.cursor.fetchone()
        
        if not user:
            return jsonify({'err': 'User not found'}), 404

        user_data = {
            'user_id': user_id,
            'user_type': user[1]
        }
        
        new_access_token = generate_access_token(user_data)
        
        return jsonify({ 'access_token': new_access_token, 'token_type': 'bearer', 'expires_in': app.config['JWT_EXPIRATION_DAYS']}), 200

    except Exception as e:
        logger.error(f'Token refresh error: {str(e)}')
        return jsonify({'err': 'Internal server error'}), 500
    
@app.route('/delete_user/<int:player_id>', methods=['DELETE'])
@verify_user_access
def delete_user(player_id):
    try:
        # delete user from user service
        if TESTING and player_id == 20:
            return jsonify({'err': 'User not present'}), 404
        if not TESTING:
            try:
                res = requests.delete(
                    f"https://user:5000/player/{player_id}",
                    timeout=10, 
                    verify=False
                ) # nosec
                
                if not res.status_code == 200:
                    # get error message from user service
                    error_msg = res.json().get('err', 'Unknown error from user service')
                    logger.error(f"[AUTH] Failed to delete user from user service: {res.status_code} - {error_msg}")
                    return jsonify({'err': error_msg}), res.status_code
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"[AUTH] User service connection error during deletion: {str(e)}")
                return jsonify({'err': "User service connection error during deletion"}), 500

        # delete from auth if successfully deleted from user service
        rsp, err = db_connector.delete_user(player_id)
        logging.info(f"[AUTH] Delete user: {rsp}")
        
        if err:
            return jsonify({'err': 'Error deleting user from auth service'}), 404

        return jsonify({'rsp': "User deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f'Delete user error: {str(e)}')
        return jsonify({'err': 'Internal server error'}), 500
    
@app.route('/authorize', methods=['POST'])
def authorize():
    try:
        token = request.json.get('token')
        route = request.json.get('route')
        method = request.json.get('method')
        
        if not all([token, route, method]):
            return jsonify({'err': 'Please provide: token, route and method '}), 400

        payload, error = verify_token(token)
        
        if error:
            return jsonify({'err': error}), 401

        user_type = payload['user_type']
        normalized_route = normalize_route(route, method)
        
        route_key = f"{method}:{normalized_route}"
         
        allowed_roles = ROUTE_PERMISSIONS.get(route_key)
        logger.warning(f"[AUTH] Matching route: {route_key} -> allowed roles: {allowed_roles}")

        if not allowed_roles:
            return jsonify({'err': 'Route not found', 'requested': route_key}), 404

        if user_type not in allowed_roles:
            return jsonify({'err': 'Insufficient permissions'}), 403

        return jsonify({'valid': True, 'user': payload}), 200

    except Exception as e:
        return jsonify({'err': f'Internal server error: {e}'}), 500

@app.route('/user/modify/<int:user_id>', methods=['PUT'])
@verify_user_access
def modify_user(user_id):
    try:
        data = request.get_json()
        
        if not data or 'username' not in data:
            return jsonify({'err': 'username required'}), 400
            
        new_user_info = {
            'user_id': user_id,
            'username': data['username']
        }
        
        # update auth db
        res, msg = db_connector.modify_user_account(new_user_info)
        
        if not res:
            return jsonify({'err': msg}), 400
            
        return jsonify({'rsp': msg}), 200
            
    except Exception as e:
        logger.error(f"[AUTH] Error modifying user: {str(e)}")
        return jsonify({'err': 'Internal server error'}), 500
    
# used to check if the user is the same as the one provided in body
@app.route('/introspect', methods=['POST'])
def verify_user():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'err': 'Authorization header missing'}), 401

        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'err': 'user_id required  body'}), 400
            
        try:
            # extract and verify token
            token = auth_header.split(' ')[1]
            payload, error = verify_token(token)
            
            if error:
                return jsonify({'err': error}), 401
            
            # get user id from token and request
            token_user_id = int(payload.get('sub'))
            request_user_id = int(data['user_id'])
            
            # check if they match
            if token_user_id != request_user_id and payload.get('user_type') != 0:
                return jsonify({'err': 'User ID does not match token'}), 403

            return jsonify({'valid': True}), 200
            
        except Exception as e:
            return jsonify({'err': str(e)}), 401
            
    except Exception as e:
        return jsonify({'err': 'Internal server error'}), 500
    

# OIDC userinfo endpoint
@app.route('/userinfo', methods=['GET', 'POST'])
def userinfo():
    try:
        # get auth header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'err': 'Missing Authorization header'}), 401

        # validate token
        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({'err': 'Invalid Authorization header format'}), 401

        token = parts[1]
        
        # verify token with function
        payload, error = verify_token(token)
        if error:
            return jsonify({'err':  error}), 401

        # get user info from db
        try:
            db_connector.cursor.execute("""
                SELECT id, username, email, user_type 
                FROM users 
                WHERE id = ?
            """, (payload['sub'],))
            
            user = db_connector.cursor.fetchone()
            if not user:
                return jsonify({
                    'error': 'invalid_token',
                    'error_description': 'User not found'
                }), 401

            
            oidc_user_info = {
                'sub': str(user[0]),
                'name': user[1],
                'preferred_username': user[1],
                'email': user[2],
                'email_verified': False,
                'roles': [VALID_USER_TYPES[user[3]]],
                'updated_at': int(datetime.datetime.now(datetime.UTC).timestamp()),
                'zoneinfo': 'UTC',
                'locale': 'en-US'
            }

            return jsonify(oidc_user_info), 200

        except Exception as db_error:
            return jsonify({'err': 'Error retrieving user information'}), 500

    except Exception as e:
        return jsonify({'err': 'Internal server error'}), 500
        
        
if __name__ == '__main__':
    app.run()