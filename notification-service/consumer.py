import pika
import os
import sys
import logging
from send import email

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Проверка переменных окружения
        queue_name = os.environ.get("MP3_QUEUE")
        if not queue_name:
            logger.error("Environment variable 'MP3_QUEUE' is not set")
            sys.exit(1)

        # Подключение к RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq", heartbeat=60)
        )
        channel = connection.channel()

        # Callback-функция
        def callback(ch, method, properties, body):
            try:
                err = email.notification(body)
                if err:
                    logger.error("Notification failed")
                    ch.basic_nack(delivery_tag=method.delivery_tag)
                else:
                    logger.info("Notification sent successfully")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag)

        # Запуск потребителя
        channel.basic_consume(
            queue=queue_name, on_message_callback=callback
        )

        logger.info("Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)