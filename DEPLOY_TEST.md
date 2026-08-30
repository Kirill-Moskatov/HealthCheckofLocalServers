# Упрощённая инструкция по деплою Pulse для тестирования на VPS

Быстрый старт для тестирования проекта на Ubuntu 22.04 LTS без домена и HTTPS.

---

## Быстрый старт (5 минут)

### 1. Подготовка сервера

```bash
# Обновляем систему и устанавливаем зависимости
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl
```

### 2. Клонирование проекта

```bash
# Клонируем репозиторий
cd /opt
sudo git clone https://github.com/Kirill-Moskatov/HealthCheckofLocalServers.git pulse
cd pulse
```

### 3. Настройка Python-окружения

```bash
# Создаём и активируем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

> **Важно:** Если файла `requirements.txt` нет, создайте его:
> ```bash
> pip freeze > requirements.txt
> ```

### 4. Конфигурация

```bash
# Создаём простой .env файл
cat > .env << EOF
HOST=0.0.0.0
PORT=8000
DEBUG=True
EOF
```

### 5. Запуск приложения

#### Вариант A: Прямой запуск (для быстрого теста)

```bash
# В активированном venv
python app/main.py
```

Приложение будет доступно по адресу: `http://<ваш-IP>:8000`

#### Вариант B: Запуск в фоне (рекомендуется)

```bash
# Используем nohup для работы в фоне
nohup /opt/pulse/venv/bin/python /opt/pulse/app/main.py > pulse.log 2>&1 &

# Проверяем, что процесс запущен
ps aux | grep main.py
```

### 6. Проверка работы

1. Откройте браузер: `http://<ваш-IP-сервера>:8000`
2. Проверьте health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

---

## Управление приложением

### Просмотр логов
```bash
tail -f pulse.log
```

### Остановка приложения
```bash
# Найти PID процесса
ps aux | grep main.py

# Остановить процесс
kill <PID>
```

### Перезапуск
```bash
# Остановить (см. выше)
kill <PID>

# Запустить снова
nohup /opt/pulse/venv/bin/python /opt/pulse/app/main.py > pulse.log 2>&1 &
```

---

## Обновление проекта

```bash
cd /opt/pulse
source venv/bin/activate
git pull origin main
pip install -r requirements.txt

# Перезапускаем приложение
ps aux | grep main.py | grep -v grep | awk '{print $2}' | xargs kill
nohup /opt/pulse/venv/bin/python /opt/pulse/app/main.py > pulse.log 2>&1 &
```

---

## Открытие порта в firewall (если включён)

```bash
# Для UFW
sudo ufw allow 8000/tcp
sudo ufw enable

# Для firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

## Troubleshooting

### Приложение не запускается
```bash
# Смотрим логи
tail -f pulse.log

# Проверяем, свободен ли порт
sudo lsof -i :8000
```

### Ошибка импортов
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Нет доступа извне
1. Проверьте firewall (см. выше)
2. Убедитесь, что в `.env` указано `HOST=0.0.0.0`
3. Проверьте правила безопасности вашего VPS-провайдера

---

## Примечания

- Эта инструкция **не включает** настройку HTTPS, домена и production-безопасности
- Для production-развёртывания используйте полную инструкцию в `DEPLOY.md`
- При тестировании рекомендуется использовать `DEBUG=True`, но **никогда не используйте его в production**

---

**Время развёртывания:** ~5 минут  
**Для тестирования и разработки**
