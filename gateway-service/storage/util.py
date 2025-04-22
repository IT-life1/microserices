import pika
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def upload_to_gridfs(fs, file):
    try:
        logger.info("Starting file upload to GridFS...")
        fid = fs.put(file)
        logger.info(f"File uploaded to GridFS with ID: {fid}")
        return fid, None
    except Exception as err:
        logger.error(f"GridFS upload failed: {err}")
        return None, ("internal server error, fs level", 500)

def create_rabbitmq_channel(connection_params):
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue='video', durable=True)
        return connection, channel, None
    except Exception as err:
        logger.error(f"RabbitMQ connection failed: {err}")
        return None, None, ("internal server error, rabbitmq connection", 500)

def publish_to_rabbitmq(channel, message):
    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
        logger.info("Message published to RabbitMQ")
        return None
    except Exception as err:
        logger.error(f"Failed to publish to RabbitMQ: {err}")
        return ("internal server error, rabbitmq publish", 500)

def upload(file, fs, rabbitmq_params, access):
    # Проверка входных данных
    if not file or not hasattr(file, 'filename'):
        return "invalid file", 400
    
    if not access or not isinstance(access, dict):
        return "invalid access data", 400

    # Загрузка в GridFS
    fid, err = upload_to_gridfs(fs, file)
    if err:
        return err

    # Подготовка сообщения
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access.get("username", "unknown")
    }

    # Работа с RabbitMQ
    connection, channel, err = create_rabbitmq_channel(rabbitmq_params)
    if err:
        try:
            fs.delete(fid)
        except Exception as del_err:
            logger.error(f"Failed to delete file: {del_err}")
        return err

    try:
        err = publish_to_rabbitmq(channel, message)
        if err:
            raise Exception(err[0])
        return "success", 200
    except Exception as err:
        try:
            fs.delete(fid)
        except Exception as del_err:
            logger.error(f"Failed to delete file: {del_err}")
        return str(err), 500
    finally:
        try:
            if connection and connection.is_open:
                connection.close()
        except Exception as close_err:
            logger.error(f"Error closing connection: {close_err}")