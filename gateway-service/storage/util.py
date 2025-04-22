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
    Упрощенная и надежная версия функции upload
    """
    try:
        # Проверка входных данных
        if not f or not hasattr(f, 'filename'):
            return "invalid file", 400
        
        if not access or not isinstance(access, dict):
            return "invalid access data", 400

        # Загрузка в GridFS
        try:
            fid = fs.put(f)
            logger.info(f"Uploaded file to GridFS: {fid}")
        except Exception as gridfs_err:
            logger.error(f"GridFS upload failed: {gridfs_err}")
            return "gridfs upload error", 500

        # Подготовка сообщения
        message = {
            "video_fid": str(fid),
            "mp3_fid": None,
            "username": access.get("username", "unknown")
        }

        # Работа с RabbitMQ
        try:
            connection = pika.BlockingConnection(rabbitmq_params)
            channel = connection.channel()
            channel.queue_declare(queue='video', durable=True)
            
            channel.basic_publish(
                exchange='',
                routing_key='video',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2  # persistent
                )
            )
            logger.info("Message published to RabbitMQ")
            
            return None, 200
            
        except Exception as rabbit_err:
            logger.error(f"RabbitMQ error: {rabbit_err}")
            try:
                fs.delete(fid)
                logger.info(f"Deleted file {fid} after RabbitMQ failure")
            except Exception as del_err:
                logger.error(f"Failed to delete file: {del_err}")
            
            return "rabbitmq publish error", 500
            
        finally:
            if 'connection' in locals() and connection.is_open:
                connection.close()
                
    except Exception as global_err:
        logger.error(f"Unexpected error: {global_err}")
        return "internal server error", 500