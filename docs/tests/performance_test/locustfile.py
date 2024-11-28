from locust import HttpUser, task, between, events
import json

distribution = {
    'C': 0,
    'R': 0,
    'SR': 0
}

class QuickstartUser(HttpUser):
    
    @task
    def pull(self):
        response = self.client.get('/banner/pull/1', verify = False)

        if response.status_code == 200:
            pieces = response.json()['pieces']

            for piece in pieces:
                distribution[piece['grade']] += 1

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        print("\nTotal pieces number: " + str(sum(distribution.values())) + "\n\nDistribution:\n" + json.dumps(distribution, indent=4) + '\n')