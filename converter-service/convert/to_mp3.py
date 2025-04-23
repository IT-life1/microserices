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
    Добавлена проверка целостности видеофайла перед конвертацией.
    """
    try:
        # Сначала проверяем, что файл существует и не пустой
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            raise ValueError("Input video file is missing or empty")

        logger.info(f"Starting conversion of {input_path} to {output_path}")
        
        # Проверяем, доступен ли ffmpeg
        if not moviepy.editor.ffmpeg_tools.ffmpeg_installed():
            raise RuntimeError("FFmpeg is not installed or not found in PATH")

        # Загружаем видео с проверкой
        try:
            video = moviepy.editor.VideoFileClip(input_path)
            if not video.audio:  # Проверяем наличие аудиодорожки
                raise ValueError("Video file has no audio track")
        except Exception as load_err:
            raise ValueError(f"Invalid video file: {str(load_err)}")

        # Конвертируем в аудио
        audio = video.audio
        audio.write_audiofile(output_path, verbose=False, logger=None)
        audio.close()
        video.close()
        
        # Проверяем результат
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Output audio file was not created properly")
            
        logger.info("Audio conversion completed successfully")
        return True
        
    except Exception as err:
        logger.error(f"Video to audio conversion failed: {str(err)}")
        # Удаляем неполный выходной файл, если он есть
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        raise

def start(message, fs_videos, fs_mp3s, channel):
    request_id = str(uuid.uuid4())
    logger.info(f"Processing request {request_id}")

    try:
        message = json.loads(message)
        if not message or "video_fid" not in message:
            logger.error(f"Invalid message format for request {request_id}")
            return "Invalid message format"

        # Получаем видеофайл
        logger.info(f"Retrieving video file for request {request_id}")
        try:
            out = fs_videos.get(ObjectId(message["video_fid"]))
            if out is None:
                raise ValueError("Video file not found in database")
        except Exception as db_err:
            logger.error(f"Database error for request {request_id}: {str(db_err)}")
            return "Video file retrieval failed"

        # Создаем временные файлы
        temp_video_path = tempfile.mktemp(suffix=".mp4")
        temp_audio_path = tempfile.mktemp(suffix=".mp3")

        try:
            # Сохраняем видео во временный файл
            with open(temp_video_path, "wb") as video_file:
                while chunk := out.read(1024 * 1024 * 10):  # 10MB chunks
                    video_file.write(chunk)

            # Проверяем размер файла
            if os.path.getsize(temp_video_path) == 0:
                raise ValueError("Downloaded video file is empty")

            # Конвертируем
            convert_video_to_audio(temp_video_path, temp_audio_path)

            # Сохраняем аудио в GridFS
            with open(temp_audio_path, "rb") as audio_file:
                fid = fs_mp3s.put(audio_file)

            message["mp3_fid"] = str(fid)

            # Отправляем сообщение
            mp3_queue = os.environ.get("MP3_QUEUE")
            if not mp3_queue:
                raise ValueError("MP3_QUEUE environment variable not set")

            channel.basic_publish(
                exchange="",
                routing_key=mp3_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )

            logger.info(f"Request {request_id} processed successfully")
            return None

        finally:
            # Удаляем временные файлы
            for path in [temp_video_path, temp_audio_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass

    except Exception as err:
        logger.error(f"Failed to process request {request_id}: {str(err)}")
        if "fid" in locals():
            try:
                fs_mp3s.delete(fid)
            except:
                pass
        return f"Processing failed: {str(err)}"