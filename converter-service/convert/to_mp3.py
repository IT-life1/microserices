import pika
import json
import tempfile
import os
from bson.objectid import ObjectId
import logging
import moviepy.editor
import uuid

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_video_to_audio(input_path, output_path):
    """
    Конвертирует видеофайл в аудиофайл с использованием moviepy.
    """
    try:
        logger.info("Converting video to audio...")
        audio = moviepy.editor.VideoFileClip(input_path).audio
        audio.write_audiofile(output_path)
        logger.info("Audio conversion completed.")
    except Exception as err:
        logger.error(f"Failed to convert video to audio: {str(err)}")
        raise

def start(message, fs_videos, fs_mp3s, channel):
    request_id = str(uuid.uuid4())
    logger.info(f"Processing request {request_id}")

    try:
        # Проверка входных данных
        message = json.loads(message)
        if not message or "video_fid" not in message:
            logger.error(f"Invalid message format for request {request_id}")
            return "Invalid message format"

        # Получение видеофайла из MongoDB
        logger.info(f"Retrieving video file from MongoDB for request {request_id}")
        out = fs_videos.get(ObjectId(message["video_fid"]))

        # Создание временного файла для видео
        with tempfile.NamedTemporaryFile(delete=True) as tf:
            logger.info(f"Writing video content to temporary file for request {request_id}")
            while chunk := out.read(1024 * 1024 * 10):  # Чтение по 10 МБ
                tf.write(chunk)

            # Конвертация видео в аудио
            tf_path = tempfile.mktemp(suffix=".mp3")
            convert_video_to_audio(tf.name, tf_path)

        # Сохранение MP3-файла в MongoDB
        logger.info(f"Saving MP3 file to MongoDB for request {request_id}")
        with open(tf_path, "rb") as f:
            data = f.read()
            fid = fs_mp3s.put(data)

        # Удаление временного MP3-файла
        os.remove(tf_path)

        # Обновление сообщения
        message["mp3_fid"] = str(fid)

        # Публикация сообщения в RabbitMQ
        mp3_queue = os.environ.get("MP3_QUEUE")
        if not mp3_queue:
            logger.error(f"Environment variable 'MP3_QUEUE' is not set for request {request_id}")
            return "Environment variable 'MP3_QUEUE' is not set"

        logger.info(f"Publishing message to RabbitMQ for request {request_id}")
        channel.basic_publish(
            exchange="",
            routing_key=mp3_queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )

    except Exception as err:
        logger.error(f"An error occurred for request {request_id}: {str(err)}")
        if "fid" in locals():
            fs_mp3s.delete(fid)
        return f"Failed: {str(err)}"