import pika
import os
import logging
from pymongo import MongoClient
import gridfs
from convert import to_mp3
import uuid

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Подключение к MongoDB
    client = MongoClient(os.environ.get('MONGODB_URI'))
    db_videos = client.videos
    db_mp3s = client.mp3s
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # Подключение к RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq', heartbeat=60)
    )
    channel = connection.channel()

    # Callback-функция
    def callback(ch, method, properties, body):
        request_id = str(uuid.uuid4())
        logger.info(f"Processing message with ID: {request_id}")
        try:
            err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
            if err:
                logger.error(f"Error processing message {request_id}: {err}")
                ch.basic_nack(delivery_tag=method.delivery_tag)
            else:
                logger.info(f"Successfully processed message {request_id}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Unexpected error for message {request_id}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    # Запуск потребителя
    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"), on_message_callback=callback
    )

    print("Waiting for messages, to exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)