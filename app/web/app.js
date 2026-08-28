/**
 * Pulse Dashboard — Material Design 3
 * Автообновление данных каждые 60 секунд
 */

const API_BASE = '/api';
const REFRESH_INTERVAL = 60000; // 60 секунд

// Состояние приложения
let services = [];
let stats = [];
let incidents = [];

/**
 * Форматирование времени простоя
 */
function formatDowntime(seconds) {
    if (seconds === null || seconds === undefined) return '';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}ч ${minutes}м`;
    }
    return `${minutes}м`;
}

/**
 * Форматирование даты
 */
function formatDate(isoString) {
    if (!isoString) return '';
    
    const date = new Date(isoString);
    return date.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Форматирование длительности инцидента
 */
function formatDuration(seconds) {
    if (seconds === null || seconds === undefined) return '?';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}ч ${minutes}м`;
    }
    return `${minutes}м`;
}

/**
 * Получение данных с API
 */
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

/**
 * Загрузка всех данных
 */
async function loadData() {
    const [servicesData, statsData, incidentsData] = await Promise.all([
        fetchAPI('/services'),
        fetchAPI('/stats?weeks=10'),
        fetchAPI('/incidents?limit=10')
    ]);
    
    if (servicesData) services = servicesData;
    if (statsData) stats = statsData;
    if (incidentsData) incidents = incidentsData;
    
    renderDashboard();
}

/**
 * Рендеринг заголовка
 */
function renderHeader() {
    const onlineCount = services.filter(s => s.status === 'up').length;
    const totalCount = services.length;
    
    document.getElementById('services-online').textContent = onlineCount;
    document.getElementById('services-total').textContent = totalCount;
}

/**
 * Рендеринг карточек сервисов
 */
function renderServiceCards() {
    const container = document.getElementById('services-container');
    
    if (services.length === 0) {
        container.innerHTML = '<p class="body-large text-on-surface-variant">Нет сервисов для отображения</p>';
        return;
    }
    
    container.innerHTML = services.map(service => {
        const serviceStats = stats.find(s => s.service_id === service.id);
        const uptimePercent = serviceStats ? serviceStats.uptime_percent : 0;
        
        let statusClass = 'unknown';
        let statusText = 'Неизвестно';
        
        if (service.status === 'up') {
            statusClass = 'up';
            statusText = 'Работает';
        } else if (service.status === 'down') {
            statusClass = 'down';
            statusText = 'Не работает';
        }
        
        return `
            <article class="service-card service-card--${statusClass}">
                <div class="service-card__header">
                    <h3 class="service-card__name">${escapeHtml(service.name)}</h3>
                    <span class="service-card__status service-card__status--${statusClass}">${statusText}</span>
                </div>
                
                <p class="service-card__url">${escapeHtml(service.url)}</p>
                
                <div class="service-card__metrics">
                    <div class="metric">
                        <div class="metric__value">${service.last_http_status || '-'}</div>
                        <div class="metric__label">HTTP статус</div>
                    </div>
                    <div class="metric">
                        <div class="metric__value">${service.last_latency_ms ? `${service.last_latency_ms} мс` : '-'}</div>
                        <div class="metric__label">Задержка</div>
                    </div>
                    <div class="metric">
                        <div class="metric__value">${uptimePercent}%</div>
                        <div class="metric__label">Аптайм 10 нед</div>
                    </div>
                </div>
                
                ${service.current_downtime_seconds 
                    ? `<p class="service-card__downtime">⚠️ Не работает: ${formatDowntime(service.current_downtime_seconds)}</p>`
                    : ''
                }
                
                <div class="service-card__uptime-bar">
                    <div class="service-card__uptime-fill" style="width: ${uptimePercent}%"></div>
                </div>
                
                <div class="service-card__actions">
                    <button class="btn btn--primary" onclick="triggerCheck(${service.id})">
                        Проверить сейчас
                    </button>
                    <button class="btn btn--tonal" onclick="showServiceDetails(${service.id})">
                        Детали
                    </button>
                </div>
            </article>
        `;
    }).join('');
}

/**
 * Рендеринг списка инцидентов
 */
function renderIncidents() {
    const list = document.getElementById('incidents-list');
    
    if (incidents.length === 0) {
        list.innerHTML = '<li class="incident-item"><p class="body-large text-on-surface-variant">Инцидентов нет</p></li>';
        return;
    }
    
    list.innerHTML = incidents.map(incident => {
        const service = services.find(s => s.id === incident.service_id);
        const serviceName = service ? service.name : 'Сервис #' + incident.service_id;
        
        return `
            <li class="incident-item">
                <div class="incident-item__info">
                    <p class="incident-item__service">${escapeHtml(serviceName)}</p>
                    <p class="incident-item__time">${formatDate(incident.started_at)}</p>
                </div>
                <span class="incident-item__duration">${formatDuration(incident.duration_seconds)}</span>
            </li>
        `;
    }).join('');
}

/**
 * Ренеринг уведомлений (заглушка - данные будут на этапе 3)
 */
function renderNotifications() {
    const list = document.getElementById('notifications-list');
    list.innerHTML = '<li class="notification-item"><p class="body-large text-on-surface-variant">Уведомления появятся после этапа 3</p></li>';
}

/**
 * Рендеринг всего дашборда
 */
function renderDashboard() {
    renderHeader();
    renderServiceCards();
    renderIncidents();
    renderNotifications();
}

/**
 * Экранирование HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Ручная проверка сервиса
 */
async function triggerCheck(serviceId) {
    try {
        const response = await fetch(`${API_BASE}/services/${serviceId}/check`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Обновляем данные сразу после проверки
            await loadData();
        } else {
            alert('Ошибка при проверке сервиса');
        }
    } catch (error) {
        console.error('Error triggering check:', error);
        alert('Ошибка соединения с сервером');
    }
}

/**
 * Показать детали сервиса (заглушка для будущего функционала)
 */
function showServiceDetails(serviceId) {
    const service = services.find(s => s.id === serviceId);
    if (service) {
        alert(`Сервис: ${service.name}\nURL: ${service.url}\nСтатус: ${service.status}`);
    }
}

/**
 * Инициализация
 */
document.addEventListener('DOMContentLoaded', () => {
    // Первая загрузка
    loadData();
    
    // Автообновление каждые 60 секунд
    setInterval(loadData, REFRESH_INTERVAL);
});
