# Poly-Agent

**Monitor. Analyze. Visualize.**

Poly-Agent is an intelligent internal tool built to streamline software development, project visibility, and operational awareness. Designed for engineering teams, it brings together health monitoring, code analysis, and automated project visualization—enabling a more efficient and insightful development workflow.

---

## 🔍 Features

### 🖥️ Monitor
Track the health of your websites in real time:
- Uptime monitoring and performance checks
- Alert system for downtime or unusual behavior
- Dashboard for system status overview
- Response time tracking with threshold alerts
- Customizable check intervals and grace periods

### 📊 Analyze
Connects to your GitHub repositories to analyze engineering activity:
- Flags and filters commit comments by developers
- Counts lines of code per commit
- Evaluates and rates code quality over time

### 🧠 Visualize
Automatically generate insights and structure around your projects:
- Flowcharts to represent project logic and architecture
- Descriptive documentation for better team understanding
- Keeps documentation in sync with codebase updates

---

## 🚀 Getting Started

### Prerequisites
- GitHub access token with repository read permissions
- Admin access to internal project URLs for monitoring
- Redis for Celery task queue (used by health checks)
- Email account for sending notifications

### Installation

1. Clone the repository:
```bash
git clone <repository_url>
cd Poly-Agent
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the frontend:
```bash
cd frontend
npm install
cd ..
```

5. Start the application:
```bash
./start
```

This script will start the Django server, React development server, and Celery workers.

### Integrated User Interface

Poly-Agent features an integrated user interface that combines:

1. **React-based GitHub analysis tools** - For exploring organization members and repositories
2. **Django-based health monitoring system** - For tracking website and service health

Both systems are seamlessly integrated into a single user interface, allowing you to:

1. Navigate between GitHub data and health checks from the main navigation
2. Access health monitoring features from the "Health Monitoring" menu item
3. Create and manage health checks for your services
4. View uptime reports and performance metrics

### Health Checks

Poly-Agent includes a comprehensive health checking system that allows you to:

1. Create health checks for your services with customizable ping intervals
2. Monitor response times and receive alerts when they exceed thresholds
3. Get email notifications when services are down
4. Generate uptime and performance reports

To use the health checks feature:
1. Access the checks dashboard at the "Health Monitoring" section
2. Create a new check and configure its parameters
3. Use the provided ping URL in your service to notify Poly-Agent it's running
4. Set up notification preferences

**Starting the health checks background tasks:**
```bash
# Start Celery worker and beat for health checks
./register_checks_tasks.sh
```

