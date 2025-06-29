#!/bin/bash

# Start Redis server (if not already running)
echo "Starting Redis server..."
redis-server --daemonize yes

# Start Celery worker
echo "Starting Celery worker..."
celery -A Poly_Agent worker -l INFO &
echo $! > .celery.worker.pid

# Start Celery beat scheduler
echo "Starting Celery beat scheduler..."
celery -A Poly_Agent beat -l INFO &
echo $! > .celery.beat.pid

echo "Celery workers and beat scheduler are running"
echo "Use './celery_stop.sh' to stop the workers" 