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
    """
    Загружает файл в GridFS.
    """
    try:
        logger.info("Starting file upload to GridFS...")
        fid = fs.put(file)
        logger.info(f"File successfully uploaded to GridFS with ID: {fid}")
        return fid, None
    except Exception as err:
        logger.error(f"Failed to upload file to GridFS: {err}")
        return None, "internal server error, fs level"

def create_rabbitmq_channel(connection_params):
    """
    Создает новое соединение и канал RabbitMQ
    """
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue='video', durable=True)
        logger.info("RabbitMQ channel successfully created.")
        return channel, None
    except Exception as err:
        logger.error(f"Failed to create RabbitMQ channel: {err}")
        return None, f"internal server error, rabbitmq channel issue: {err}"

def publish_to_rabbitmq(channel, message):
    """
    Публикует сообщение в RabbitMQ
    """
    try:
        logger.info("Starting message publishing to RabbitMQ...")
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
        logger.info(f"Message successfully published to RabbitMQ: {message}")
        return None
    except pika.exceptions.AMQPConnectionError as conn_err:
        logger.error(f"RabbitMQ connection error: {conn_err}")
        return "internal server error, rabbitmq connection issue"
    except pika.exceptions.ChannelClosedByBroker as broker_err:
        logger.error(f"RabbitMQ channel closed by broker: {broker_err}")
        return "internal server error, rabbitmq channel closed by broker"
    except Exception as err:
        logger.error(f"RabbitMQ publish error: {err}")
        return f"internal server error, rabbitmq issue: {err}"

def upload(f, fs, rabbitmq_params, access):
    """
    Обрабатывает загрузку файла, публикацию в RabbitMQ и очистку при ошибках.
    """
    logger.info("Starting file upload process...")

    if not f:
        logger.warning("No file provided for upload.")
        return "missing file", 400

    if not access or "username" not in access:
        logger.warning("Missing or incomplete user credentials.")
        return "missing user credentials", 400

    # Загрузка файла в GridFS
    fid, error = upload_to_gridfs(fs, f)
    if error:
        return error, 500

    # Подготовка сообщения
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }
    logger.info(f"Prepared message for RabbitMQ: {message}")

    # Создаем канал и публикуем сообщение
    channel, error = create_rabbitmq_channel(rabbitmq_params)
    if error:
        fs.delete(fid)
        return error, 500

    error = publish_to_rabbitmq(channel, message)
    
    # Закрываем соединение в любом случае
    try:
        channel.close()
        channel.connection.close()
    except Exception as close_err:
        logger.error(f"Error closing RabbitMQ connection: {close_err}")

    if error:
        fs.delete(fid)
        return error, 500

    return None, 200