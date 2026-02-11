FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV VAULT_PATH=/app/vault

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies (browsers + system libs)
# We install the python package first to get the 'playwright' command
RUN pip install playwright && \
    playwright install --with-deps chromium

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY AI_Employee/ ./AI_Employee/

# Create vault directories
RUN mkdir -p /app/vault/Needs_Action \
    /app/vault/Pending_Approval \
    /app/vault/Approved \
    /app/vault/Rejected \
    /app/vault/Done \
    /app/vault/Logs

# Copy Next.js frontend
COPY AI_Employee/web-ui/ ./web-ui/
WORKDIR /app/web-ui
RUN npm install
RUN npm run build

WORKDIR /app

# Ecosystem for PM2
COPY AI_Employee/ecosystem.config.js .

# Install PM2 globally
RUN npm install -g pm2

# Expose Next.js port
EXPOSE 3000

# Start Supervisor/PM2
CMD ["pm2-runtime", "ecosystem.config.js"]
