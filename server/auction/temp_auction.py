import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest
import json
from app import app  # Import your Flask app (the one you've defined in your script)

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def check_condition(condition, message):
    if not condition:
        pytest.fail(message)

def test_create_auction(client):
    data = {
        "piece_id": 1,
        "creator_id": 1,
        "start_price": 100.0,
        "end_date": "2024-12-31T23:59:59"
    }
    response = client.post('/create_auction', json=data)
    check_condition(response.status_code == 201, f"Expected status code 201 but got {response.status_code}")
    response_json = response.get_json()
    check_condition('id' in response_json, "Response JSON does not contain 'id'")

def test_create_auction_missing_field(client):
    data = {
        "piece_id": 1,
        "creator_id": 1,
        "start_price": 100.0
    }
    response = client.post('/create_auction', json=data)
    check_condition(response.status_code == 400, f"Expected status code 400 but got {response.status_code}")
    response_json = response.get_json()
    check_condition('error' in response_json, "Response JSON does not contain 'error'")
    check_condition(response_json['error'] == 'Missing required fields', 
                    f"Expected error message 'Missing required fields' but got '{response_json.get('error')}'")

def test_get_auction_info(client):
    response = client.get('/auction/1')
    check_condition(response.status_code == 200, f"Expected status code 200 but got {response.status_code}")
    response_json = response.get_json()
    check_condition('piece_id' in response_json, "Response JSON does not contain 'piece_id'")

def test_get_auction_info_not_found(client):
    response = client.get('/auction/99999')
    check_condition(response.status_code == 404, f"Expected status code 404 but got {response.status_code}")
    response_json = response.get_json()
    check_condition('error' in response_json, "Response JSON does not contain 'error'")

def test_place_bid(client):
    data = {
        "user_id": 1,
        "bid_amount": 300.0
    }
    response = client.post('/auction/bid/1', json=data)
    response_json = response.get_json()
    check_condition('error' in response_json, "Response JSON does not contain 'error'")
    check_condition(response_json['error'] == 'Auction is not active', 
                    f"Expected error 'Auction is not active' but got {response_json.get('error')}")

def test_place_bid_low_amount(client):
    data = {
        "user_id": 1,
        "bid_amount": 100.0
    }
    response = client.post('/auction/bid/1', json=data)
    check_condition(response.status_code == 400, f"Expected status code 400 but got {response.status_code}")
    response_json = response.get_json()
    check_condition('error' in response_json, "Response JSON does not contain 'error'")

def test_place_bid_invalid_bid_amount(client):
    data = {
        "user_id": 1,
        "bid_amount": -50.0
    }
    response = client.post('/auction/bid/1', json=data)
    check_condition(response.status_code == 400, f"Expected status code 400 but got {response.status_code}")

def test_place_bid_missing_fields(client):
    data = {
        "user_id": 1,
    }
    response = client.post('/auction/bid/1', json=data)
    check_condition(response.status_code == 400, f"Expected status code 400 but got {response.status_code}")

def test_get_active_auctions(client):
    response = client.get('/auction/running/all')
    check_condition(response.status_code == 200, f"Expected status code 200 but got {response.status_code}")
    response_json = response.get_json()
    check_condition(isinstance(response_json, list), "Response is not a list")

def test_get_past_auctions(client):
    response = client.get('/auction/history')
    check_condition(response.status_code == 200, f"Expected status code 200 but got {response.status_code}")
    response_json = response.get_json()
    check_condition(isinstance(response_json, list), "Response is not a list")

def test_modify_auction(client, mocker):
    data = {
        "status": "ended"
    }
    mocker.patch('auction_service.AuctionService.get_auction_by_id', return_value={"id": 1, "status": "open"})
    mocker.patch('auction_service.AuctionService.modify_auction', return_value={"message": "Auction closed successfully"})
    response = client.put('/auction/modify/1', json=data)
    check_condition(response.status_code == 200, f"Expected status code 200 but got {response.status_code}")
    response_json = response.get_json()
    check_condition('message' in response_json, "Response JSON does not contain 'message'")
    check_condition(response_json['message'] == 'Auction closed successfully', 
                    f"Expected message 'Auction closed successfully' but got {response_json.get('message')}")
