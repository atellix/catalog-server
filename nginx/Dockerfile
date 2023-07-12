FROM nginx

COPY run_nginx.sh /etc/nginx/run_nginx.sh
RUN mkdir -p /usr/share/nginx/html
RUN mkdir -p /etc/nginx/certs
COPY ssl/fullchain.pem /etc/nginx/certs/fullchain.pem
COPY ssl/privkey.pem /etc/nginx/certs/privkey.pem


