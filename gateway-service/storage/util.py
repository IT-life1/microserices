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

def ensure_channel_open(connection):
    """
    Проверяет, открыт ли канал, и создает новый, если текущий закрыт.
    """
    try:
        if connection.is_closed:
            logger.warning("RabbitMQ connection is closed, attempting to reconnect...")
            connection.connect()
        
        channel = connection.channel()
        logger.info("RabbitMQ channel successfully opened.")
        return channel, None
    except Exception as err:
        logger.error(f"Failed to open RabbitMQ channel: {err}")
        return None, f"internal server error, rabbitmq channel issue: {err}"

def publish_to_rabbitmq(connection, message):
    """
    Публикует сообщение в RabbitMQ, пересоздавая канал при необходимости.
    """
    try:
        # Проверяем и открываем канал
        channel, error = ensure_channel_open(connection)
        if error:
            return error

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
        channel.close()  # Закрываем канал после использования
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

def upload(f, fs, rabbitmq_connection, access):
    """
    Обрабатывает загрузку файла, публикацию в RabbitMQ и очистку при ошибках.
    """
    # Логирование начала процесса
    logger.info("Starting file upload process...")

    # Проверка наличия файла
    if not f:
        logger.warning("No file provided for upload.")
        return "missing file", 400

    # Проверка наличия данных пользователя
    if not access or "username" not in access:
        logger.warning("Missing or incomplete user credentials.")
        return "missing user credentials", 400

    # Загрузка файла в GridFS
    fid, error = upload_to_gridfs(fs, f)
    if error:
        logger.error(f"GridFS upload failed with error: {error}")
        return error, 500

    # Подготовка сообщения для RabbitMQ
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }
    logger.info(f"Prepared message for RabbitMQ: {message}")

    # Публикация сообщения в RabbitMQ
    error = publish_to_rabbitmq(rabbitmq_connection, message)
    if error:
        logger.error(f"Failed to publish message to RabbitMQ: {error}")

        # Очистка файла из GridFS в случае ошибки
        try:
            logger.info(f"Attempting to delete file from GridFS with ID: {fid}")
            fs.delete(fid)
            logger.info(f"File with ID {fid} successfully deleted from GridFS.")
        except Exception as delete_err:
            logger.error(f"Failed to delete file from GridFS: {delete_err}")
            return "internal server error, cleanup failed", 500

        return error, 500

    # Успешное завершение
    logger.info("File upload and RabbitMQ publishing completed successfully.")
    return None, 200