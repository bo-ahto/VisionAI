FROM nginx:alpine
COPY artsy-deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY artsy_kr_viewer.html /usr/share/nginx/html/index.html
COPY artsy_kr_artworks.json /usr/share/nginx/html/artsy_kr_artworks.json
EXPOSE 80
