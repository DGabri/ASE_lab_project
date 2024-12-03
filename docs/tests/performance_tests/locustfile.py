from locust import HttpUser, task, constant, SequentialTaskSet
import json

class QuickstartUser(HttpUser):
    wait_time = constant(1)

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.post('/auth/login', json = {
            "username": "player",
            "password": "ChessHeroes2024@",
        }, verify = False)

        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            self.user_id = response.json()['user']['id']
    
    # User endpoints
    @task
    def update_gold(self):
        response = self.client.put(f'/user/player/gold/{self.user_id}', json = {
            "amount": 10,
            "is_refill": True
        }, headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)

    @task
    def update_account(self):
        response = self.client.put(f'/user/player/{self.user_id}', json = {
            "username": "player"
        }, headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)

    @task
    def get_collection(self):
        response = self.client.get(f'/user/player/collection/{self.user_id}', headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)

    # Auction endpoints
    @task
    def add_auction(self):
        response = self.client.post('/auction/create_auction', json = {
            "piece_id": 1,
            "seller_id": self.user_id,
            "start_price": 100,
            "duration_hours": 0.000001
        }, headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)

    # Banner endpoints
    @task
    def get_banner(self):
        response = self.client.get('/banner/banner/1', headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)

    # Piece endpoints
    @task
    def get_piece(self):
        response = self.client.get('/piece/piece?id=1', headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)

    @task
    def get_all_pieces(self):
        response = self.client.get('/piece/piece/all', headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)