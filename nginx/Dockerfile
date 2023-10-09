FROM nginx

COPY run_nginx.sh /etc/nginx/run_nginx.sh
RUN mkdir -p /usr/share/nginx/html
RUN mkdir -p /etc/nginx/certs
COPY certs /etc/nginx/certs/
COPY dist /usr/share/nginx/html


