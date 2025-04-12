import os
import requests
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_token(token: str):
    auth_svc_address = os.environ.get("AUTH_SVC_ADDRESS")
    if not auth_svc_address:
        logger.error("Authentication service address is not configured")
        return None, ("Authentication service address is not configured", 500)

    try:
        response = requests.post(
            f"http://auth:5000/validate",
            headers={"Authorization": token},
            timeout=5
        )
        return response, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication service is unavailable: {e}")
        return None, ("Authentication service is unavailable", 503)

def token(request):
    token = request.headers.get("Authorization")
    if not token:
        return None, ("missing credentials", 401)

    response, error = validate_token(token)
    if error:
        return None, error

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
