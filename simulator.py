import time
import random
import requests
from datetime import datetime

# URL нашего эндпоинта приема логов
API_URL = "http://127.0.0.1:8000/api/logs"

# Набор тестовых IP-адресов и пользователей для симуляции
ATTACKER_IPS = ["192.168.1.100", "203.0.113.42", "10.0.0.15"]
TARGET_USERS = ["admin", "root", "administrator", "postgres", "user1"]

def generate_log_line():
    """Генерирует случайную строку лога (обычную или атаку)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 70% шанс сгенерировать неудачный вход от атакующего IP, 30% - обычный трафик
    if random.random() < 0.7:
        ip = random.choice(ATTACKER_IPS)
        user = random.choice(TARGET_USERS)
        event_type = "LOGIN_FAILED"
    else:
        ip = f"192.168.1.{random.randint(10, 200)}"
        user = "guest"
        event_type = random.choice(["LOGIN_SUCCESS", "LOGIN_FAILED"])

    return f"[{timestamp}] {event_type} user={user} ip={ip}"

def main():
    print("[*] SecPulse Log Simulator запущен. Нажмите Ctrl+C для остановки.")
    print(f"[*] Отправка логов на {API_URL}...\n")
    
    try:
        while True:
            log_line = generate_log_line()
            payload = {"log_line": log_line}
            
            try:
                response = requests.post(API_URL, json=payload, timeout=3)
                if response.status_code == 200:
                    alerts = response.json()
                    if alerts:
                        for alert in alerts:
                            print(f"[!] АЛЕРТ ОБНАРУЖЕН! Тип: {alert['alert_type']} | Пользователь: {alert['username']} | IP: {alert['ip_address']} | Попыток: {alert['failed_attempts']}")
                    else:
                        print(f"[+] Лог отправлен: {log_line}")
                else:
                    print(f"[-] Ошибка API: {response.status_code} - {response.text}")
            except requests.exceptions.Timeout:
                print("[-] Запрос к API превысил тайм-аут. Повторная попытка будет выполнена следующим циклом.")
            except requests.exceptions.ConnectionError:
                print("[-] Не удалось подключиться к серверу. Убедитесь, что FastAPI запущен!")
            
            # Пауза между отправкой логов (1.5 секунды)
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        print("\n[*] Симулятор остановлен.")

if __name__ == "__main__":
    main()
