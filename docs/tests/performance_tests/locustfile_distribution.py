from locust import HttpUser, task, constant, events
import json

distribution = {
    'C': 0,
    'R': 0,
    'SR': 0
}

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

    @task
    def update_gold(self):
        response = self.client.put(f'/user/player/gold/{self.user_id}', json = {
            "amount": 50,
            "is_refill": True
        }, headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)
    
    @task
    def pull(self):
        response = self.client.get('/banner/banner/pull/1', headers = {
            'Authorization': 'Bearer ' + self.access_token
        }, verify = False)

        if response.status_code == 200:
            pieces = response.json()['pieces']

            for piece in pieces:
                distribution[piece['grade']] += 1

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        print("\nTotal pieces number: " + str(sum(distribution.values())) + "\n\nDistribution:\n" + json.dumps(distribution, indent = 4) + '\n')