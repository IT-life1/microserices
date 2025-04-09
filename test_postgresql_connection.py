import subprocess
import time
import psycopg2
from contextlib import closing

def run_port_forward():
    """
    Запускает kubectl port-forward в фоновом режиме.
    Возвращает объект процесса для последующего завершения.
    """
    command = ["kubectl", "port-forward", "svc/db", "5432:5432"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Port-forward запущен. Ожидание готовности...")
    time.sleep(5)  # Ждем, пока порт станет доступен
    return process

def test_postgresql_connection():
    """
    Проверяет подключение к PostgreSQL через localhost:5432.
    """
    try:
        connection = psycopg2.connect(
            host="localhost",
            port=5432,
            user="alex",
            password="sova",
            database="authdb"
        )
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            print("Результат выполнения запроса:", result)
        print("Тест успешно пройден.")
    except Exception as e:
        print("Ошибка при подключении к базе данных:", e)
    finally:
        if connection:
            connection.close()

def main():
    # Запускаем port-forward
    port_forward_process = None
    try:
        port_forward_process = run_port_forward()
        # Выполняем тест подключения
        test_postgresql_connection()
    finally:
        # Завершаем процесс port-forward
        if port_forward_process:
            port_forward_process.terminate()
            stdout, stderr = port_forward_process.communicate()
            if stdout:
                print("Port-forward stdout:", stdout.decode())
            if stderr:
                print("Port-forward stderr:", stderr.decode())
            print("Port-forward завершен.")

if __name__ == "__main__":
    main()
