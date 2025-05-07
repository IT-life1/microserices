import os
import gridfs
import pika
import json
from flask import Flask, request, send_file, jsonify  # Добавлен jsonify
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId
import logging
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Flask(__name__)
CORS(server, origins=["http://158.160.64.194:3000"])

# Инициализация MongoDB
mongo_video = PyMongo(server, uri=os.environ.get('MONGODB_VIDEOS_URI'))
mongo_mp3 = PyMongo(server, uri=os.environ.get('MONGODB_MP3S_URI'))

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

def get_rabbitmq_params():
    return pika.ConnectionParameters(
        host="rabbitmq",
        heartbeat=600,
        blocked_connection_timeout=300
    )

@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)
    if err:
        return jsonify({"error": err}), 401
    return jsonify({"token": token}), 200

@server.route("/upload", methods=["POST"])
def handle_upload():
    # Аутентификация
    access_data, err = validate.token(request)
    if err:
        return jsonify({"error": err}), 401

    try:
        # Преобразуем access_data в словарь
        if isinstance(access_data, str):
            access_dict = json.loads(access_data)
        else:
            access_dict = access_data
        
        # Проверка прав
        if not access_dict.get("admin"):
            return jsonify({"error": "not authorized"}), 401

    except json.JSONDecodeError:
        return jsonify({"error": "invalid access token format"}), 401
    except Exception as e:
        logger.error(f"Error processing access data: {e}")
        return jsonify({"error": "internal server error"}), 500

    # Проверка файлов
    if len(request.files) != 1:
        return jsonify({"error": "exactly 1 file required"}), 400

    file = next(iter(request.files.values()))

    # Проверка типа файла
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
        return jsonify({"error": "unsupported file format"}), 400

    # Проверка размера
    if file.content_length > 100 * 1024 * 1024:  # 100 MB
        return jsonify({"error": "file too large"}), 413

    # Обработка загрузки
    try:
        result = util.upload(
            file=file,
            fs=fs_videos,
            rabbitmq_params=get_rabbitmq_params(),
            access=access_dict
        )
        
        if isinstance(result, tuple):
            return jsonify({"error": result[0]}), result[1]
        return jsonify({"message": "success"}), 200
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return jsonify({"error": "upload processing failed"}), 500

@server.route("/download", methods=["GET"])
def download():
    # Аутентификация
    access_data, err = validate.token(request)
    if err:
        return jsonify({"error": err}), 401

    try:
        if isinstance(access_data, str):
            access_dict = json.loads(access_data)
        else:
            access_dict = access_data
        
        if not access_dict.get("admin"):
            return jsonify({"error": "not authorized"}), 401

    except json.JSONDecodeError:
        return jsonify({"error": "invalid access token format"}), 401
    except Exception as e:
        logger.error(f"Error processing access data: {e}")
        return jsonify({"error": "internal server error"}), 500

    fid_string = request.args.get("fid")
    if not fid_string:
        return jsonify({"error": "fid is required"}), 400

    try:
        out = fs_mp3s.get(ObjectId(fid_string))
        return send_file(out, download_name=f"{fid_string}.mp3")
    except gridfs.errors.NoFile:
        return jsonify({"error": "file not found"}), 404
    except Exception as err:
        logger.error(f"Download error: {err}")
        return jsonify({"error": "internal server error"}), 500

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)