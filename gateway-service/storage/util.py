import pika
import json
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def upload_to_gridfs(fs, file):
    try:
        fid = fs.put(file)
        return fid, None
    except Exception as err:
        logger.error(f"Failed to upload file to GridFS: {err}")
        return None, "internal server error, fs level"

def publish_to_rabbitmq(channel, message):
    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
        return None
    except pika.exceptions.AMQPConnectionError as conn_err:
        logger.error(f"RabbitMQ connection error: {conn_err}")
        return "internal server error, rabbitmq connection issue"
    except Exception as err:
        logger.error(f"RabbitMQ publish error: {err}")
        return f"internal server error, rabbitmq issue: {err}"

def upload(f, fs, channel, access):
    if not f:
        return "missing file", 400

    if not access or "username" not in access:
        return "missing user credentials", 400

    fid, error = upload_to_gridfs(fs, f)
    if error:
        return error, 500

    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    error = publish_to_rabbitmq(channel, message)
    if error:
        try:
            fs.delete(fid)
        except Exception as delete_err:
            logger.error(f"Failed to delete file from GridFS: {delete_err}")
            return "internal server error, cleanup failed", 500
        return error, 500

    return None, 200