FROM nginx:alpine
COPY saatchi-deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY saatchi_kr_viewer.html /usr/share/nginx/html/index.html
COPY saatchi_kr_artworks.json /usr/share/nginx/html/saatchi_kr_artworks.json
COPY saatchi_kr_artists.json /usr/share/nginx/html/saatchi_kr_artists.json
EXPOSE 80
