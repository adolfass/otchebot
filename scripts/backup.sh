#!/bin/bash
#
# Скрипт ежедневного бэкапа PostgreSQL
# Сжатие, ротация (7 дней), отправка на резервный сервер
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== КОНФИГУРАЦИЯ ====================

# Путь для хранения бэкапов (локально)
BACKUP_DIR="${BACKUP_DIR:-/backup/otchebot}"

# Резервный сервер
BACKUP_SERVER="${BACKUP_SERVER:-}"
BACKUP_SSH_KEY="${BACKUP_SSH_KEY:-~/.ssh/id_rsa}"
REMOTE_BACKUP_PATH="${REMOTE_BACKUP_PATH:-/backup/otchebot}"

# Параметры PostgreSQL
PG_USER="${PG_USER:-otchebot_user}"
PG_DB="${PG_DB:-otchebot}"
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"

# Количество дней хранения бэкапов
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Дата для имени файла
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="otchebot_backup_${DATE}.sql.gz"

# ==================== ФУНКЦИИ ====================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==================== ПРОВЕРКИ ====================

log_info "Проверка конфигурации..."

# Создание директории для бэкапов
if [ ! -d "$BACKUP_DIR" ]; then
    log_info "Создание директории для бэкапов: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Проверка pg_dump
if ! command -v pg_dump &> /dev/null; then
    log_error "pg_dump не найден. Установите PostgreSQL client."
    exit 1
fi

# ==================== СОЗДАНИЕ БЭКАПА ====================

log_info "Создание бэкапа базы данных $PG_DB..."

# Полный бэкап с сжатием
PGPASSWORD="${PG_PASSWORD:-}" pg_dump -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    log_info "Бэкап создан: $BACKUP_DIR/$BACKUP_FILE"
    
    # Размер файла
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    log_info "Размер бэкапа: $BACKUP_SIZE"
else
    log_error "Ошибка создания бэкапа"
    exit 1
fi

# ==================== ОТПРАВКА НА РЕЗЕРВНЫЙ СЕРВЕР ====================

if [ -n "$BACKUP_SERVER" ]; then
    log_info "Отправка бэкапа на резервный сервер $BACKUP_SERVER..."
    
    # Создание удалённой директории
    ssh -i "$BACKUP_SSH_KEY" "$BACKUP_SERVER" "mkdir -p $REMOTE_BACKUP_PATH" 2>/dev/null || {
        log_warn "Не удалось создать удалённую директорию"
    }
    
    # Копирование бэкапа
    scp -i "$BACKUP_SSH_KEY" "$BACKUP_DIR/$BACKUP_FILE" "$BACKUP_SERVER:$REMOTE_BACKUP_PATH/" 2>/dev/null && {
        log_info "Бэкап отправлен на резервный сервер"
    } || {
        log_warn "Не удалось отправить бэкап на резервный сервер"
    }
else
    log_warn "BACKUP_SERVER не настроен, отправка на резервный сервер пропущена"
fi

# ==================== РОТАЦИЯ БЭКАПОВ ====================

log_info "Удаление старых бэкапов (старше $RETENTION_DAYS дней)..."

# Удаление локальных старых бэкапов
find "$BACKUP_DIR" -name "otchebot_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Удаление удалённых старых бэкапов
if [ -n "$BACKUP_SERVER" ]; then
    ssh -i "$BACKUP_SSH_KEY" "$BACKUP_SERVER" "find $REMOTE_BACKUP_PATH -name 'otchebot_backup_*.sql.gz' -type f -mtime +$RETENTION_DAYS -delete" 2>/dev/null || true
fi

log_info "Ротация завершена"

# ==================== ПРОВЕРКА БЭКАПА ====================

log_info "Проверка целостности бэкапа..."

# Проверка архива
if gzip -t "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null; then
    log_info "Бэкап прошёл проверку целостности"
else
    log_error "Бэкап повреждён!"
    exit 1
fi

# ==================== ЗАВЕРШЕНИЕ ====================

log_info "========================================="
log_info "Бэкап завершён успешно!"
log_info "========================================="
log_info "Файл: $BACKUP_DIR/$BACKUP_FILE"
log_info "Размер: $BACKUP_SIZE"
log_info "Хранение: $RETENTION_DAYS дней"

# Вывод списка текущих бэкапов
echo ""
log_info "Текущие бэкапы:"
ls -lh "$BACKUP_DIR"/otchebot_backup_*.sql.gz 2>/dev/null | tail -10 || echo "Нет бэкапов"

exit 0
