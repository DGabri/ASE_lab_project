from flask import Flask, request, Response
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# microservices urls mapping
MICROSERVICES_URLS = {
    "auction": "http://auction:5000",
    "auth": "http://auth:5000",
    "banner": "http://banner:5000",
    "piece": "http://piece:5000",
    "user": "http://user:5000"
}

@app.route('/<microservice>/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<microservice>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def admin_gateway(microservice, path):
    if microservice not in MICROSERVICES_URLS:
        return {"error": f"Service: '{microservice}' not found"}, 404

    # create target url
    target_url = f"{MICROSERVICES_URLS[microservice]}/{path}"
    logger.info(f"Forwarding to: {microservice} {target_url}")

    try:
        # forward request to microservice
        response = requests.request(
            method=request.method,
            url=target_url,
            data=request.get_data(),
            headers={key: value for key, value in request.headers if key != 'Host'},
            params=request.args,
            allow_redirects=False
        )

        # forward response to caller
        return Response(response.content, status=response.status_code, headers=dict(response.headers))

    except requests.exceptions.RequestException as e:
        return {"error": "Service unavailable"}, 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)