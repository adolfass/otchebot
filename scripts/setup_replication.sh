#!/bin/bash
#
# Скрипт настройки репликации PostgreSQL
# Интерактивный скрипт для настройки streaming репликации
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Настройка репликации PostgreSQL${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ==================== ЗАПРОС ПАРАМЕТРОВ ====================

echo -e "${YELLOW}Введите параметры для настройки репликации:${NC}"
echo ""

# IP резервного сервера
read -p "IP адрес резервного сервера: " REPLICATION_IP
if [ -z "$REPLICATION_IP" ]; then
    echo -e "${RED}Ошибка: IP адрес не может быть пустым${NC}"
    exit 1
fi

# Путь к SSH ключу
read -p "Путь к SSH ключу (по умолчанию ~/.ssh/id_rsa): " SSH_KEY_PATH
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_rsa}
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}Предупреждение: SSH ключ не найден по пути $SSH_KEY_PATH${NC}"
fi

# Путь для хранения бэкапов на резервном сервере
read -p "Путь для хранения бэкапов на резервном сервере (по умолчанию /backup/otchebot): " BACKUP_PATH
BACKUP_PATH=${BACKUP_PATH:-/backup/otchebot}

# Пользователь PostgreSQL для репликации
read -p "Имя пользователя PostgreSQL для репликации (по умолчанию replicator): " REPLICATION_USER
REPLICATION_USER=${REPLICATION_USER:-replicator}

# Пароль для пользователя репликации
read -sp "Пароль для пользователя репликации: " REPLICATION_PASSWORD
echo ""
if [ -z "$REPLICATION_PASSWORD" ]; then
    echo -e "${RED}Ошибка: Пароль не может быть пустым${NC}"
    exit 1
fi

# Порт PostgreSQL
read -p "Порт PostgreSQL (по умолчанию 5432): " PG_PORT
PG_PORT=${PG_PORT:-5432}

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Параметры настроены:${NC}"
echo -e "${GREEN}========================================${NC}"
echo "  IP резервного сервера: $REPLICATION_IP"
echo "  SSH ключ: $SSH_KEY_PATH"
echo "  Путь для бэкапов: $BACKUP_PATH"
echo "  Пользователь репликации: $REPLICATION_USER"
echo "  Порт PostgreSQL: $PG_PORT"
echo ""

# ==================== НАСТРОЙКА ОСНОВНОГО СЕРВЕРА ====================

echo -e "${YELLOW}Настройка основного сервера PostgreSQL...${NC}"

# Создание пользователя репликации
echo "Создание пользователя репликации..."
psql -U postgres -c "CREATE ROLE $REPLICATION_USER WITH REPLICATION LOGIN PASSWORD '$REPLICATION_PASSWORD';" 2>/dev/null || {
    echo -e "${YELLOW}Пользователь уже существует или ошибка подключения${NC}"
}

# Настройка postgresql.conf
echo "Настройка postgresql.conf..."

PG_CONF_PATH=$(psql -U postgres -t -c "SHOW config_file;" | tr -d ' ')
PG_CONF_DIR=$(dirname "$PG_CONF_PATH")

# Резервная копия конфигурации
cp "$PG_CONF_PATH" "${PG_CONF_PATH}.backup"

# Добавление настроек репликации
cat >> "$PG_CONF_PATH" << EOF

# Репликация (добавлено скриптом setup_replication.sh)
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3
wal_keep_size = 64MB
EOF

echo -e "${GREEN}postgresql.conf обновлён${NC}"

# Настройка pg_hba.conf
echo "Настройка pg_hba.conf..."

PG_HBA_PATH="$PG_CONF_DIR/pg_hba.conf"
cp "$PG_HBA_PATH" "${PG_HBA_PATH}.backup"

# Добавление правил для репликации
cat >> "$PG_HBA_PATH" << EOF

# Репликация (добавлено скриптом setup_replication.sh)
host    replication     $REPLICATION_USER     $REPLICATION_IP/32            scram-sha-256
host    replication     $REPLICATION_USER     127.0.0.1/32                  scram-sha-256
host    replication     $REPLICATION_USER     ::1/128                       scram-sha-256
EOF

echo -e "${GREEN}pg_hba.conf обновлён${NC}"

# Перезагрузка PostgreSQL
echo "Перезагрузка PostgreSQL..."
systemctl restart postgresql || {
    echo -e "${YELLOW}Не удалось перезагрузить PostgreSQL через systemctl${NC}"
    echo "Перезагрузите PostgreSQL вручную: sudo systemctl restart postgresql"
}

echo -e "${GREEN}Основной сервер настроен${NC}"
echo ""

# ==================== НАСТРОЙКА РЕЗЕРВНОГО СЕРВЕРА ====================

echo -e "${YELLOW}Настройка резервного сервера...${NC}"
echo "Для завершения настройки выполните следующие команды на резервном сервере ($REPLICATION_IP):"
echo ""

cat << EOF
# 1. Создайте директорию для данных
sudo mkdir -p /var/lib/postgresql/14/replica
sudo chown postgres:postgres /var/lib/postgresql/14/replica

# 2. Выполните pg_basebackup с основного сервера
sudo -u postgres pg_basebackup -h $REPLICATION_IP -D /var/lib/postgresql/14/replica -U $REPLICATION_USER -P -R -X stream -C -S replica_slot

# 3. Создайте файл standby.signal
sudo -u postgres touch /var/lib/postgresql/14/replica/standby.signal

# 4. Настройте postgresql.conf для standby
echo "primary_conninfo = 'host=$REPLICATION_IP port=$PG_PORT user=$REPLICATION_USER password=$REPLICATION_PASSWORD'" >> /var/lib/postgresql/14/replica/postgresql.auto.conf

# 5. Запустите PostgreSQL
sudo systemctl start postgresql

# 6. Проверьте статус репликации
sudo -u postgres psql -c "SELECT * FROM pg_stat_replication;"
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Настройка завершена!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "1. Выполните команды выше на резервном сервере"
echo "2. Проверьте репликацию: SELECT * FROM pg_stat_replication;"
echo "3. Настройте скрипт backup.sh для ежедневных бэкапов"
echo ""
