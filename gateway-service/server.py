import os
import gridfs
import pika
import json
import logging
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Flask(__name__)

mongo_video = PyMongo(server, uri=os.environ.get('MONGODB_VIDEOS_URI'))
mongo_mp3 = PyMongo(server, uri=os.environ.get('MONGODB_MP3S_URI'))

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

def connect_to_rabbitmq(retries=5, delay=2):
    for attempt in range(retries):
        try:
            logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{retries})...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq", heartbeat=60))
            channel = connection.channel()
            logger.info("Successfully connected to RabbitMQ.")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as conn_err:
            logger.error(f"Failed to connect to RabbitMQ: {conn_err}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error("Max retries reached. Unable to connect to RabbitMQ.")
                raise
    return None, None

connection, channel = connect_to_rabbitmq()
if not connection or not channel:
    logger.error("Failed to establish RabbitMQ connection. Exiting...")
    raise Exception("RabbitMQ connection failed")

def authenticate_user(request):
    access, err = validate.token(request)
    if err:
        logger.warning("Unauthorized access attempt")
        return None, err
    return json.loads(access), None

def upload_file(f, fs, channel, access):
    if not f.filename.lower().endswith(('.mp4', '.avi', '.mov')):
        return "unsupported file format", 400

    if f.content_length > 100 * 1024 * 1024:  # 100 MB
        return "file too large", 413

    return util.upload(f, fs, channel, access)

@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err

@server.route("/upload", methods=["POST"])
def upload():
    access, err = authenticate_user(request)

    if err:
        return err

    if access["admin"]:
        if len(request.files) != 1:
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            err = upload_file(f, fs_videos, channel, access)

            if err:
                return err

        return "success!", 200
    else:
        return "not authorized", 401

@server.route("/download", methods=["GET"])
def download():
    access, err = authenticate_user(request)

    if err:
        return err

    if access["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except gridfs.errors.NoFile:
            logger.error(f"File with ID {fid_string} not found")
            return "file not found", 404
        except Exception as err:
            logger.error(f"Error downloading file: {err}")
            return "internal server error", 500

    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
