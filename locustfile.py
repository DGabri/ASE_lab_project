from locust import HttpUser, task
import json

class QuickstartUser(HttpUser):
    @task()
    def get_all(self):
        self.client.get('/piece/all')