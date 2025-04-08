import jwt
import datetime
import os
import psycopg2
from flask import Flask, request
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

server = Flask(__name__)
JWT_SECRET = os.getenv('JWT_SECRET')

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST'),
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            port=5432
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def CreateJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )

@server.route('/login', methods=['POST'])
def login():
    auth_table_name = os.getenv('AUTH_TABLE')
    valid_tables = ['auth_user']
    if auth_table_name not in valid_tables:
        return 'Invalid table name', 400

    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

    try:
        logger.info(f"Connecting to bd")
        conn = get_db_connection()
        cur = conn.cursor()
        query = f"SELECT email, password FROM {auth_table_name} WHERE email = %s"
        logger.info(f"Executing query: {query}")
        cur.execute(query, (auth.username,))
        user_row = cur.fetchone()
        logger.info(f"Ending executing query: {query}")
        logger.info(f"Checking user_row")
        if not user_row:
            return 'User not found', 401

        email, stored_password = user_row
        if stored_password != auth.password:
            return 'Could not verify', 401
        logger.info(f"Creating token")
        return CreateJWT(email, JWT_SECRET, True), 200
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return 'Internal server error', 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@server.route('/validate', methods=['POST'])
def validate():
    encoded_jwt = request.headers.get('Authorization')
    if not encoded_jwt:
        return 'Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

    encoded_jwt = encoded_jwt.split(' ')[1]
    try:
        decoded_jwt = jwt.decode(encoded_jwt, JWT_SECRET, algorithms=["HS256"])
        return decoded_jwt, 200
    except jwt.ExpiredSignatureError:
        return 'Token expired', 401
    except jwt.InvalidTokenError:
        return 'Invalid token', 401

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)
