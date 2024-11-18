from flask import Flask, request, make_response, jsonify
from DAOs.banners_DAO import BannersDAO
from db_result import DBResultCode
from classes.banner import Banner
from classes.rates import Rates
import sqlite3
import json
import requests
import random

with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
banners_dao = BannersDAO(config['db']['name'], config['db']['scheme'])

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

    if to_check['pieces_num'] and (not 'pieces_num' in banner or not isinstance(banner['pieces_num'], int) or banner['pieces_num'] < 0):
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
    banner = request.get_json()

    if not banner_is_valid(banner, {
        'name': True,
        'cost': True,
        'pic': True,
        'pieces_num': True,
        'rates': True
    }):
        return jsonify(message = "Attributes not found or invalid"), 400

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
    banner = request.get_json()

    if not banner_id(banner,  {
        'name': 'name' in banner,
        'cost': 'cost' in banner,
        'pic': 'pic' in banner,
        'pieces_num': 'pieces_num' in banner,
        'rates': 'rates' in banner
    }):
        return jsonify(message = "Attributes invalid"), 400

    banner = Banner(
        banner_id,
        banner['name'] if 'name' in banner else None,
        banner['cost'] if 'v' in banner else None,
        banner['pic'] if 'pic' in banner else None,
        banner['pieces_num'] if 'pieces_num' in banner else None,
        banner['rates'] if 'rates' in banner else None
    )

    if not vars(banner):
        return jsonify(message = "No attribute found"), 400

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

    return jsonify(message = "Banner deleted"), 200

# Make a pull for a banner
@app.route('/banner/pull/<int:banner_id>', methods = ['GET'])
def pull(banner_id):
    """
    1) Update player gold
    2) Get banner info
    3) Get pieces info
    4) Select at random the pieces
    5) Update player collection
    6) Return the pieces
    """

    # Make the request for the gold update

    if True: # Check if there was problem with the request to the player module
        content, code = get_banner(banner_id)

        if code != 200:
            return content, code

        banner = Banner.from_dict(content.get_json()['banner'])
        response = requests.get("http://localhost:5003/piece/all")
        pieces_pulled = []
        rand = random.randint(0, 1)

        if rand <= banner.rates.common:
            pass
        elif rand <= banner.rates.rare:
            pass
        else:
            pass

    return jsonify(message = "OK"), 200

if __name__ == '__main__':
    app.run(debug = True)