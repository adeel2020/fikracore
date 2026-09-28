FROM nginx:1.29-alpine
RUN addgroup -S gateway && adduser -S gateway -G gateway
COPY nginx.conf /etc/nginx/nginx.conf
RUN mkdir -p /var/cache/nginx /tmp/nginx && chown -R gateway:gateway /etc/nginx /var/cache/nginx /var/log/nginx /tmp/nginx
USER gateway
EXPOSE 8080 8443
CMD ["nginx", "-g", "daemon off;"]
