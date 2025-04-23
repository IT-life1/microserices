import pika
import os
import logging
from pymongo import MongoClient
import gridfs
import uuid
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Подключение к MongoDB (оставляем, так как оно может потребоваться для проверок)
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
        
        try:
            message = json.loads(body.decode('utf-8'))
            logger.debug(f"Message content: {message}")
            
            # Проверка наличия обязательных полей
            if "video_fid" not in message:
                raise ValueError("Missing video_fid in message")
            
            # Эмулируем успешную конвертацию
            logger.info(f"Processing message {request_id}")
            
            # Добавляем фиктивный mp3_fid (в реальной системе здесь будет настоящий ID)
            message["mp3_fid"] = "converted_" + message["video_fid"]
            
            # Отправляем сообщение в следующую очередь
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
            
            logger.info(f"Message {request_id} forwarded to MP3 queue")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing message {request_id}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    # Запуск потребителя
    try:
        queue_name = os.environ.get("VIDEO_QUEUE")
        if not queue_name:
            raise ValueError("Environment variable VIDEO_QUEUE is not set")

        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_consume(
            queue=queue_name, 
            on_message_callback=callback,
            auto_ack=False  # Подтверждаем сообщения только после успешной обработки
        )
        logger.info(f"Consumer started for queue: {queue_name}")
        
        print("Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Failed to start consumer: {e}")
    finally:
        try:
            connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Failed to close RabbitMQ connection: {e}")

if __name__ == "__main__":
    main()