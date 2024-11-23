from wtforms.validators import Email, InputRequired, Length, NumberRange
from password_strength import PasswordPolicy
from flask import Flask, request, jsonify
from wtforms import StringField
from flask_wtf import FlaskForm
from auth_DAO import AuthDAO
from functools import wraps
import requests
import datetime
import logging
import bcrypt
import json
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['JWT_EXPIRATION_DAYS'] = 30
app.config['WTF_CSRF_ENABLED'] = False

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
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
    user_type = StringField('user_type', [
        InputRequired(message="User type required"),
        NumberRange(min=0, max=1, message="User type must be 1 (player) or 2 (admin)")
])

# routes permission mapping
ROUTE_PERMISSIONS = {
    # user routes
    'GET:/player/collection/<player_id>': [1, 0],
    'PUT:/player/gold/<player_id>': [1, 0],
    'PUT:/player/<player_id>': [1, 0],
    'DELETE:/player/<player_id>': [1, 0],
    
    # admin routes
    'GET:/player/all': [0],
    'GET:/player/<player_id>': [0],
    'PUT:/admin/user/<user_id>/modify': [0],
    'PUT:/admin/user/ban/<user_id>': [0],
    'PUT:/admin/user/unban/<user_id>': [0],
    'GET:/player/gold/history/<player_id>': [0],
    'PUT:/admin/user/market-history/<user_id>': [0]
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
            logger.info("DB init successful")
        return db
    
    except Exception as e:
        logger.error(f"DB init failed: {str(e)}")
        raise
    
# read config
config = load_config()

# get db connection DAO
db_connector = init_db(config)


##########################################################

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
    
# given user data create jwt
def generate_access_token(user_data):
    token_payload = {
        'user_id': user_data['user_id'],
        'user_type': user_data['user_type'],
        'username': user_data['username'],
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=app.config['JWT_EXPIRATION_DAYS'])
    }
    
    return jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

# refresj the token
def generate_refresh_token(user_id):
    new_expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    token = jwt.encode(
        {'user_id': user_id, 'exp': new_expiration},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return token, new_expiration

# validate jwt
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
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
        
        user_info = {
            'username': data['username'],
            'email': data['email'],
            'password': data['password'],
            'user_type': data['user_type'],
        }
        
        # validate password requirements
        valid_password = password_requirements.test(user_info["password"])
        
        if len(valid_password) > 0:
            db_connector.log_action(user_id, "ERR_create_player", "Invalid pwd")
            return jsonify({'error': 'Password must be at least 8 characters, contain an uppercase char and two numbers'}), 400    
        
        # generate password hash
        salt = bcrypt.gensalt()
        user_info["password"] = bcrypt.hashpw(str(user_info["password"]).encode('utf-8'), salt).decode('utf-8')
        
        # Create user in auth database
        user_id, err_msg = db_connector.create_user(user_info)
        
        if err_msg:
            return jsonify({'error': err_msg}), 400
            
        # call user service to add user
        user_data = {
            'username': data['username'],
            'email': data['email'],
            'user_id': user_id
        }
        
        try:
            res = requests.post("http://user_gateway:5000/user/create_user", json=user_data)
            
            if res.status_code != 201:
                # rollback user creation
                db_connector.delete_user(user_id)
                return jsonify({'error': 'Registration failed'}), 400
            
            # registration successful            
            return jsonify({'rsp': 'User created correctly', 'id': user_id}), 201

        except:
            return jsonify({'msg': 'User registered successfully','user_id': user_id}), 400
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing credentials'}), 400

        user_data, error = db_connector.verify_credentials(
            data['username'],
            data['password']
        )
        
        if error:
            return jsonify({'error': error}), 401

        # generate access and refresh tokens
        access_token = generate_access_token(user_data)
        refresh_token, expires_at = generate_refresh_token(user_data['user_id'])
        
        # save refresh token to db
        db_connector.store_refresh_token(refresh_token, user_data['user_id'], expires_at)

        return jsonify({'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'expires_in': app.config['JWT_EXPIRATION_DAYS']}), 200

    except Exception as e:
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

        route_key = f"{method}:{route}"
        print(route_key)
        allowed_roles = ROUTE_PERMISSIONS.get(route_key)
        
        if not allowed_roles:
            return jsonify({'error': 'Route not found'}), 404

        if payload['user_type'] not in allowed_roles:
            return jsonify({'error': 'Insufficient permissions'}), 403

        return jsonify({
            'valid': True, 'user': payload}), 200

    except Exception as e:
        logger.error(f'Token verification error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    try:
        # Test database connection
        db_connector.cursor.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'service': 'auth'})
    
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        
        return jsonify({'status': 'unhealthy', 'service': 'auth', 'error': str(e)}), 503

if __name__ == '__main__':
    app.run(debug=True)