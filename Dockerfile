FROM python:3.12-slim
WORKDIR /app

# Install system dependencies including supervisor and nginx
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    unzip \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create nginx directories and set up log redirection
RUN mkdir -p /var/log/nginx /var/cache/nginx /var/run && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy configuration files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY nginx.conf /app/nginx.conf

# Copy application code
COPY . .

# Initialize Reflex
RUN reflex init

# Create log directory for supervisor
RUN mkdir -p /var/log

# Expose only port 80 (nginx will handle all traffic)
EXPOSE 80

# Run supervisord to manage all services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]