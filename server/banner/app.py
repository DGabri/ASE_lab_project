from flask import Flask, request, make_response, jsonify
from DAOs.banners_DAO import BannersDAO
from classes.db_result import DBResultCode
from classes.banner import Banner
from classes.rates import Rates
from requests.exceptions import ConnectionError, HTTPError
from werkzeug.exceptions import UnsupportedMediaType
import sqlite3
import json
import requests
import random

mock_fun = None

try:
    with open('config.json') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print("File 'config' not found.")
except ValueError:
    print("Decoding JSON 'config' file has failed.")

app = Flask(__name__)
banners_dao = BannersDAO(config['db']['name'], config['db']['scheme'])
app.config['WTF_CSRF_ENABLED'] = False

def rates_are_valid(rates):
    if not 'common' in rates or rates['common'] < 0 or rates['common'] > 1:
        return False

    if not 'rare' in rates or rates['rare'] < 0 or rates['rare'] > 1:
        return False

    if not 'super_rare' in rates or rates['super_rare'] < 0 or rates['super_rare'] > 1:
        return False

    if rates['common'] + rates['rare'] + rates['super_rare'] != 1:
        return False

    return True

def banner_is_valid(banner, to_check):
    if to_check['name'] and (not 'name' in banner or not isinstance(banner['name'], str) or not banner['name']):
        return False

    if to_check['cost'] and (not 'cost' in banner or not isinstance(banner['cost'], int) or banner['cost'] <= 0):
        return False

    if to_check['pic'] and (not 'pic' in banner or not isinstance(banner['pic'], str) or not banner['pic']):
        return False

    if to_check['pieces_num'] and (not 'pieces_num' in banner or not isinstance(banner['pieces_num'], int) or banner['pieces_num'] <= 0):
        return False

    if to_check['rates'] and not rates_are_valid(banner['rates']):
        return False

    return True

# Get a banner info
@app.route('/banner/<int:banner_id>', methods = ['GET'])
def get_banner(banner_id):
    result = banners_dao.get_banner(banner_id)

    if result.code == DBResultCode.NOT_FOUND:
        return jsonify(message = result.message), 404

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500
    
    return jsonify(banner = result.content.to_dict()), 200

# Add a new banner
@app.route('/banner', methods = ['POST'])
def add_banner():
    try:
        banner = request.get_json()
    except UnsupportedMediaType as e:
        return jsonify(message = str(e)), 415

    if not banner_is_valid(banner, {
        'name': True,
        'cost': True,
        'pic': True,
        'pieces_num': True,
        'rates': True
    }):
        return jsonify(message = "Attributes not found or invalid."), 400

    new_rates = Rates(banner['rates']['common'], banner['rates']['rare'], banner['rates']['super_rare'])
    new_banner = Banner(None, banner['name'], banner['cost'], banner['pic'], banner['pieces_num'], new_rates)
    result = banners_dao.insert_banner(new_banner)

    if result.code == DBResultCode.NOT_FOUND:
        return jsonify(message = result.message), 404

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500

    return jsonify(banner_id = result.content), 201

# Update a banner
@app.route('/banner/<int:banner_id>', methods = ['PUT'])
def update_banner(banner_id):
    try:
        banner = request.get_json()
    except UnsupportedMediaType as e:
        return jsonify(message = str(e)), 415

    if not banner_is_valid(banner,  {
        'name': 'name' in banner,
        'cost': 'cost' in banner,
        'pic': 'pic' in banner,
        'pieces_num': 'pieces_num' in banner,
        'rates': 'rates' in banner
    }):
        return jsonify(message = "Attributes invalid."), 400

    rates = Rates.from_dict(banner['rates']) if 'rates' in banner else None
    
    banner = Banner(
        banner_id,
        banner['name'] if 'name' in banner else None,
        banner['cost'] if 'cost' in banner else None,
        banner['pic'] if 'pic' in banner else None,
        banner['pieces_num'] if 'pieces_num' in banner else None,
        rates
    )

    if all(not value or key == 'id' for key, value in banner.to_dict().items()):
        return jsonify(message = "No attribute found."), 400

    result = banners_dao.update_banner(banner)
    
    if result.code == DBResultCode.NOT_FOUND:
        return jsonify(message = result.message), 404

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500
    
    return jsonify(message = result.message), 200
    

# Delete a banner
@app.route('/banner/<int:banner_id>', methods = ['DELETE'])
def delete_banner(banner_id):
    result = banners_dao.delete_banner(banner_id)

    if result.code == DBResultCode.NOT_FOUND:
        return jsonify(message = result.message), 404

    if result.code == DBResultCode.ERROR:
        return jsonify(message = result.message), 500

    return jsonify(message = "Banner deleted."), 200

# Make a pull for a banner
@app.route('/banner/pull/<int:banner_id>', methods = ['GET'])
def pull(banner_id):
    """
    1) Get the user_id
    2) Get the banner info
    3) Get pieces info
    4) Update the player gold
    5) Update player collection
    """

    # Get the user id
    if not mock_fun:
        authentication_header = request.headers.get("Authorization")
            
        if not authentication_header or not authentication_header.startswith("Bearer "):
            return jsonify(message = "Login required."), 401
        
        token = authentication_header.split(' ')[1]

        try:
            response = requests.post("https://auth:5000/authorize", json={
                "token": token,
                "route": 'token',
                "method": 'POST'
            }, timeout = 5, verify = False) # nosec
        except ConnectionError:
            return jsonify(message = "Auth service is down."), 500
        except HTTPError:
            return jsonify(message = response.content), response.status_code

    content = mock_fun('POST:/auth/authorize') if mock_fun else response.json()
    user_id = content['user']['sub']

    # Get the banner info
    content, code = get_banner(banner_id)

    if code != 200:
        return content, code

    banner = Banner.from_dict(content.get_json()['banner'])

    # Get player gold
    if not mock_fun:
        try:
            response = requests.get(f"https://user:5000/user/balance/{user_id}", timeout = 5, verify = False) # nosec
        except ConnectionError:
            return jsonify(message = "User service is down."), 500
        except HTTPError:
            return jsonify(message = response.content), response.status_code

        if response.status_code != 200:
            return jsonify(message = response.json()['error']), response.status_code

    content = mock_fun('GET:/user/user/balance') if mock_fun else response.json()
    player_gold = content['balance']

    if player_gold < banner.cost:
        return jsonify(message = "Insufficient amount of gold."), 403

    # Get pieces info
    if not mock_fun:
        try:
            response = requests.get("https://piece:5000/piece/all", timeout = 5, verify = False) # nosec
        except ConnectionError:
            return jsonify(message = "Piece service is down."), 500
        except HTTPError:
            return jsonify(message = response.content), response.status_code

        if response.status_code != 200:
            return jsonify(message = respose.json()['message']), response.status_code

    content = mock_fun('GET:/piece/piece/all') if mock_fun else response.json()
    pieces = content['pieces']

    # Update the player gold
    if not mock_fun:
        try:
            response = requests.put(f"https://user:5000/player/gold/{user_id}", json = {
                "amount": banner.cost * (-1),
                "is_refill": False
            }, timeout = 5, verify = False) # nosec
        except ConnectionError:
            return jsonify(message = "User service is down."), 500
        except HTTPError:
            return jsonify(message = response.content), response.status_code

        if response.status_code != 200:
            return jsonify(message = "Internal error in user service."), response.status_code

    pieces_pulled = []

    for i in range(banner.pieces_num):
        pieces_pulled.append(pull_piece(banner, pieces))
    
    # Update the player collection
    if not mock_fun:
        try:
            response = requests.post("https://user:5000/player/collection/update", json = {
                "user_id": user_id,
                "pieces_id": list(map(lambda piece: piece["id"], pieces_pulled))
            }, headers = {
                'Authorization': authentication_header,
                'X-API-Key': 'Chess_heroes_2024',
                'Content-Type': 'application/json'
            }, timeout = 5, verify = False) # nosec
        except ConnectionError:
            return jsonify(message = "User service is down."), 500
        except HTTPError:
            return jsonify(message = response.content), response.status_code

    return jsonify(pieces = pieces_pulled), 200

def select_piece_by_grade(pieces, grade):
    pieces_filtered = list(filter(lambda piece: piece['grade'] == grade, pieces))

    if len(pieces_filtered) == 0:
        return {}

    rand = random.randint(0, len(pieces_filtered) - 1) # nosec
    return pieces_filtered[rand]

def pull_piece(banner, pieces):
    rand = random.uniform(0, 1) # nosec
    piece_selected = {}

    if rand <= banner.rates.common:
        piece_selected = select_piece_by_grade(pieces, 'C')
    elif rand <= banner.rates.common + banner.rates.rare:
        piece_selected = select_piece_by_grade(pieces, 'R')
    else:
        piece_selected = select_piece_by_grade(pieces, 'SR')

    return piece_selected

if __name__ == '__main__':
    app.run(debug = True) # nosec