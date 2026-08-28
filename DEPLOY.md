# Инструкция по деплою Pulse на VPS

Этот документ описывает процесс развёртывания проекта Pulse (HealthCheck of Local Servers) на виртуальном сервере под управлением Linux (Ubuntu 22.04 LTS).

## Требования

- VPS с Ubuntu 22.04 LTS (или аналогичный Debian-based дистрибутив)
- Доменное имя (опционально, но рекомендуется для HTTPS)
- root-доступ или пользователь с правами sudo
- Открытые порты: 22 (SSH), 80 (HTTP), 443 (HTTPS)

---

## Шаг 1: Подготовка сервера

### 1.1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2. Установка зависимостей
```bash
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx curl
```

### 1.3. Создание пользователя для приложения (опционально, но рекомендуется)
```bash
sudo adduser --system --group --no-create-home pulse
```

---

## Шаг 2: Клонирование репозитория

### 2.1. Клонируем проект
```bash
cd /opt
sudo git clone https://github.com/Kirill-Moskatov/HealthCheckofLocalServers.git pulse
sudo chown -R pulse:pulse /opt/pulse
```

### 2.2. Переходим в директорию проекта
```bash
cd /opt/pulse
```

---

## Шаг 3: Настройка Python-окружения

### 3.1. Создаём виртуальное окружение
```bash
sudo -u pulse python3 -m venv /opt/pulse/venv
```

### 3.2. Активируем и устанавливаем зависимости
```bash
sudo -u pulse /opt/pulse/venv/bin/pip install --upgrade pip
sudo -u pulse /opt/pulse/venv/bin/pip install -r requirements.txt
```

> **Примечание:** Убедитесь, что файл `requirements.txt` существует в корне проекта. Если его нет, создайте его на основе установленных зависимостей вашего локального окружения:
> ```bash
> pip freeze > requirements.txt
> ```

---

## Шаг 4: Настройка конфигурации

### 4.1. Создаём файл окружения
```bash
sudo nano /opt/pulse/.env
```

Пример содержимого `.env`:
```env
HOST=127.0.0.1
PORT=8000
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 4.2. Настраиваем права доступа
```bash
sudo chown pulse:pulse /opt/pulse/.env
chmod 600 /opt/pulse/.env
```

---

## Шаг 5: Настройка systemd-сервиса

### 5.1. Создаём unit-файл
```bash
sudo nano /etc/systemd/system/pulse.service
```

Содержимое файла:
```ini
[Unit]
Description=Pulse HealthCheck Dashboard
After=network.target

[Service]
User=pulse
Group=pulse
WorkingDirectory=/opt/pulse
ExecStart=/opt/pulse/venv/bin/python /opt/pulse/app/main.py
Environment="PATH=/opt/pulse/venv/bin"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2. Активируем и запускаем сервис
```bash
sudo systemctl daemon-reload
sudo systemctl enable pulse
sudo systemctl start pulse
sudo systemctl status pulse
```

Сервис должен работать и слушать порт 8000 на localhost.

---

## Шаг 6: Настройка Nginx

### 6.1. Создаём конфиг сайта
```bash
sudo nano /etc/nginx/sites-available/pulse
```

Содержимое конфига (без HTTPS):
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/pulse/app/web;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 6.2. Активируем сайт
```bash
sudo ln -s /etc/nginx/sites-available/pulse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Шаг 7: Настройка HTTPS (рекомендуется)

### 7.1. Получаем сертификат Let's Encrypt
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot автоматически обновит конфиг Nginx и настроит редирект с HTTP на HTTPS.

### 7.2. Проверяем автообновление сертификата
```bash
sudo certbot renew --dry-run
```

---

## Шаг 8: Проверка работы

1. Откройте браузер и перейдите по адресу `https://your-domain.com`
2. Проверьте главную страницу дашборда
3. Убедитесь, что карточки сервисов отображаются корректно
4. Проверьте `/health` endpoint: `curl https://your-domain.com/health`

---

## Шаг 9: Мониторинг и логи

### Просмотр логов приложения
```bash
sudo journalctl -u pulse -f
```

### Просмотр логов Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Перезапуск сервиса
```bash
sudo systemctl restart pulse
```

### Остановка сервиса
```bash
sudo systemctl stop pulse
```

---

## Обновление проекта

Для обновления кода из репозитория:

```bash
cd /opt/pulse
sudo -u pulse git pull origin main
sudo systemctl restart pulse
```

---

## Безопасность

1. **Настройте firewall:**
   ```bash
   sudo ufw allow 'Nginx Full'
   sudo ufw allow OpenSSH
   sudo ufw enable
   ```

2. **Отключите root-логин по SSH:**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # PermitRootLogin no
   sudo systemctl restart sshd
   ```

3. **Настройте автоматические обновления безопасности:**
   ```bash
   sudo apt install -y unattended-upgrades
   sudo dpkg-reconfigure --priority=low unattended-upgrades
   ```

---

## Troubleshooting

### Сервис не запускается
```bash
sudo journalctl -u pulse --no-pager -n 50
```

### Ошибки Nginx
```bash
sudo nginx -t
sudo systemctl status nginx
```

### Порт занят
```bash
sudo lsof -i :8000
sudo netstat -tulpn | grep 8000
```

### Проблемы с правами доступа
```bash
sudo chown -R pulse:pulse /opt/pulse
sudo chmod -R 755 /opt/pulse
```

---

## Дополнительные ресурсы

- [Официальная документация FastAPI](https://fastapi.tiangolo.com/deployment/)
- [Документация Nginx](https://nginx.org/en/docs/)
- [Let's Encrypt Certbot](https://certbot.eff.org/)

---

**Дата обновления инструкции:** 2025-06-18  
**Версия проекта:** Этап 2 (Дашборд M3)
