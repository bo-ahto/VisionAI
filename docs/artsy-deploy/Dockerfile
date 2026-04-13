FROM nginx:alpine
COPY artsy-deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY artsy_kr_viewer.html /usr/share/nginx/html/index.html
COPY artsy_kr_artworks.json /usr/share/nginx/html/artsy_kr_artworks.json
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=5s \
  CMD wget -qO- http://localhost/ || exit 1
EXPOSE 80
