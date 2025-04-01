import os
import requests
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def authenticate_user(basic_auth):
    auth_svc_address = os.environ.get("AUTH_SVC_ADDRESS")
    if not auth_svc_address:
        logger.error("Authentication service address is not configured")
        return None, ("Authentication service address is not configured", 500)

    try:
        response = requests.post(
            f"http://{auth_svc_address}/login",
            auth=basic_auth,
            timeout=5
        )
        return response, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication service is unavailable: {e}")
        return None, ("Authentication service is unavailable", 503)

def login(request):
    auth = request.authorization
    if not (auth and auth.username and auth.password):
        return None, ("missing credentials", 401)

    basic_auth = (auth.username, auth.password)
    response, error = authenticate_user(basic_auth)
    if error:
        return None, error

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)