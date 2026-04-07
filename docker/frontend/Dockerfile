FROM nginx:alpine
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY website/ /usr/share/nginx/html/
EXPOSE 80
