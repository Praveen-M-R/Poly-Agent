#!/bin/bash

# Check if worker pid file exists
if [ -f .celery.worker.pid ]; then
    echo "Stopping Celery worker..."
    kill $(cat .celery.worker.pid)
    rm .celery.worker.pid
else
    echo "No worker pid file found"
fi

# Check if beat pid file exists
if [ -f .celery.beat.pid ]; then
    echo "Stopping Celery beat scheduler..."
    kill $(cat .celery.beat.pid)
    rm .celery.beat.pid
else
    echo "No beat pid file found"
fi

echo "Celery workers and beat scheduler have been stopped" 