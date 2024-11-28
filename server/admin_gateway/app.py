from flask import Flask, request, Response, jsonify
from urllib.parse import urljoin
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False

# Microservices URLs mapping
MICROSERVICES_URLS = {
    "auction": "https://auction:5005",
    "auth": "https://auth:5000",
    "banner": "https://banner:5000",
    "piece": "https://piece:5000",
    "user": "https://user:5000"
}

# routes that do not need auth
PUBLIC_ROUTES = {
    ("POST", "auth/create_user"),
    ("POST", "auth/login")
}

# routes that are strictly for the admin
ADMIN_ROUTES = {
    ("POST", "auth/create_user"),
    ("DELETE", "user/player"),
    ("PUT", "user/player"),
    ("GET", "user/player/collection"),
    ("PUT", "user/player/gold"),
    ("POST", "user/auction/complete"),
}
def verify_admin_authentication(token, route, method):
    """
    Verify both authentication and admin authorization with auth service
    """
    try:
        auth_response = requests.post(
            f"{MICROSERVICES_URLS['auth']}/authorize",
            json={
                "token": token,
                "route": route,
                "method": method
            },
            timeout=10, 
            verify=False
        ) # nosec
        
        if auth_response.status_code == 200:
            # Additional check for admin role
            user_data = auth_response.json().get('user', {})
            if user_data.get('user_type') != 0:  # 0 is admin type as per auth service
                return {"error": "Admin access required"}, 403
                
        return auth_response.json(), auth_response.status_code
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Auth service error: {str(e)}")
        return {"error": "Auth service unavailable"}, 503

def is_public_route(method, microservice, path):
    """Check if the requested route is public"""
    route = f"{microservice}/{path}"
    return (method, route) in PUBLIC_ROUTES

@app.route('/<microservice>/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<microservice>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def admin_gateway(microservice, path):
    """
    Main gateway route handler that enforces admin authentication
    """
    # Check if requested service exists
    if microservice not in MICROSERVICES_URLS:
        return jsonify({"error": f"Service: '{microservice}' not found"}), 404

    # Create target URL
    target_microservice = MICROSERVICES_URLS[microservice]
    target_url = f"{target_microservice}/{path}"
    logger.info(f"[ADMIN GATEWAY] Forwarding to: {microservice} {target_url}")

    # Skip authentication for public routes
    if is_public_route(request.method, microservice, path):
        logger.info(f"[ADMIN GATEWAY] Allowing public route: {request.method} {microservice}/{path}")
    else:
        # Verify admin authentication for protected routes
        authentication_header = request.headers.get("Authorization")
        
        if not authentication_header or not authentication_header.startswith("Bearer "):
            return jsonify({"error": "Admin login required"}), 401
        
        token = authentication_header.split(' ')[1]
        
        # Verify admin authentication and authorization
        auth_response, auth_return_code = verify_admin_authentication(token, path, request.method)
        logging.info(f"[ADMIN GATEWAY] auth_response: {auth_response} response code: {auth_return_code}")
        
        if auth_return_code != 200:
            if auth_return_code == 401:
                return jsonify({"error": "Please login as admin"}), 401
            elif auth_return_code == 403:
                return jsonify({"error": "Admin access required"}), 403
            else:
                return jsonify(auth_response), auth_return_code

    try:
        # Forward request to microservice
        response = requests.request(
            method=request.method,
            url=target_url,
            data=request.get_data(),
            headers={key: value for key, value in request.headers if key != 'Host'},
            params=request.args,
            allow_redirects=False,
            timeout=10, 
            verify=False
        ) # nosec

        # Forward response to caller
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"[ADMIN GATEWAY] Service error: {str(e)}")
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

if __name__ == '__main__':
    app.run(port=81)  # Running on different port than user gateway