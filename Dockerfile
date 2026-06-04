# AgriMarket Recommendation Feature
# Phase 5: Nginx configuration
# Author: AJEICHEK ABEL NISSI (CT23A010)

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Compression (reduces JS/CSS transfer size by ~70%)
    gzip on;
    gzip_types text/plain text/css application/javascript application/json;
    gzip_min_length 1024;

    # Cache static assets aggressively (widget files rarely change)
    map $uri $cache_control {
        ~\.(js|css)$  "public, max-age=86400";   # 1 day
        default       "no-cache";
    }

    server {
        listen 80;
        server_name _;

        # ----------------------------------------------------------------
        # Health check endpoint (used by Docker healthcheck)
        # ----------------------------------------------------------------
        location /health {
            return 200 "ok\n";
            add_header Content-Type text/plain;
        }

        # ----------------------------------------------------------------
        # Static widget files — served directly by Nginx
        # GET /static/agri-widget.js
        # GET /static/agri-widget.css
        # ----------------------------------------------------------------
        location /static/ {
            root /usr/share/nginx/html;
            add_header Cache-Control $cache_control;
            add_header Access-Control-Allow-Origin "https://www.agromarket.cm";
        }

        # ----------------------------------------------------------------
        # Proxy to Phase 1 tracking API (port 5001)
        # POST /track/api/v1/events
        # ----------------------------------------------------------------
        location /track/ {
            rewrite ^/track/(.*) /$1 break;
            proxy_pass         http://agri-tracker:5001;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout 5s;
            proxy_read_timeout    10s;
        }

        # ----------------------------------------------------------------
        # Proxy to Phase 3 recommendation API (port 5002)
        # GET /rec/api/v1/recommendations
        # ----------------------------------------------------------------
        location /rec/ {
            rewrite ^/rec/(.*) /$1 break;
            proxy_pass         http://agri-api:5002;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout 5s;
            proxy_read_timeout    15s;
        }
    }
}
