FROM node:22-alpine AS build

WORKDIR /app

COPY apps/web/package*.json ./
RUN npm install

COPY apps/web ./
ARG VITE_API_HTTP_URL=http://127.0.0.1:8000
ARG VITE_API_WS_URL=ws://127.0.0.1:8000
ENV VITE_API_HTTP_URL=$VITE_API_HTTP_URL
ENV VITE_API_WS_URL=$VITE_API_WS_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
