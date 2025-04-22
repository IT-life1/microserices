import pika
import os
import logging
from pymongo import MongoClient
import gridfs
import uuid

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Подключение к MongoDB
    try:
        client = MongoClient(os.environ.get('MONGODB_URI'))
        db_videos = client.videos
        db_mp3s = client.mp3s
        fs_videos = gridfs.GridFS(db_videos)
        fs_mp3s = gridfs.GridFS(db_mp3s)
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return

    # Подключение к RabbitMQ
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq', heartbeat=60)
        )
        channel = connection.channel()
        logger.info("Successfully connected to RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return

    # Callback-функция
    def callback(ch, method, properties, body):
        request_id = str(uuid.uuid4())
        logger.info(f"Received message with ID: {request_id}")
        logger.debug(f"Message body: {body.decode('utf-8')}")

        try:
            # Логируем, что сообщение успешно обработано
            logger.info(f"Processing message {request_id}: Message acknowledged")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            # Логируем ошибку при обработке сообщения
            logger.error(f"Error processing message {request_id}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    # Запуск потребителя
    try:
        queue_name = os.environ.get("VIDEO_QUEUE")
        if not queue_name:
            raise ValueError("Environment variable VIDEO_QUEUE is not set")

        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_consume(
            queue=queue_name, on_message_callback=callback
        )
        logger.info(f"Consumer started for queue: {queue_name}")
    except Exception as e:
        logger.error(f"Failed to start consumer: {e}")
        return

    print("Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    finally:
        try:
            connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Failed to close RabbitMQ connection: {e}")

if __name__ == "__main__":
    main()