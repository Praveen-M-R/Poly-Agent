#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Celery worker and beat for checks app...${NC}"

# Check if celery is already running
if [ -f .celery.worker.pid ]; then
    echo -e "${RED}Celery worker is already running. Please stop it first using celery_stop.sh${NC}"
    exit 1
fi

if [ -f .celery.beat.pid ]; then
    echo -e "${RED}Celery beat is already running. Please stop it first using celery_stop.sh${NC}"
    exit 1
fi

# Start Celery worker
echo -e "${YELLOW}Starting Celery worker...${NC}"
celery -A Poly_Agent worker --loglevel=info --detach --pidfile=.celery.worker.pid
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Celery worker started successfully${NC}"
else
    echo -e "${RED}Failed to start Celery worker${NC}"
    exit 1
fi

# Start Celery beat
echo -e "${YELLOW}Starting Celery beat...${NC}"
celery -A Poly_Agent beat --loglevel=info --detach --pidfile=.celery.beat.pid
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Celery beat started successfully${NC}"
else
    echo -e "${RED}Failed to start Celery beat${NC}"
    exit 1
fi

echo -e "${GREEN}Celery worker and beat are now running for checks app${NC}"
echo -e "${YELLOW}You can stop them using celery_stop.sh${NC}"

chmod +x register_checks_tasks.sh 