# Stage 1: Build the Vue app
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:1.25-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

CMD sh -c "export LISTEN_PORT=\${PORT:-80} && envsubst '\${LISTEN_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"

expose 80
