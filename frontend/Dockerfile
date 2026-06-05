# Build stage
FROM node:18-alpine AS build-stage

WORKDIR /app

# Copy package lock and configurations
COPY frontend/package.json ./
COPY frontend/tsconfig*.json ./
COPY frontend/vite.config.ts ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/index.html ./

# Install npm dependencies
RUN npm install

# Copy source code
COPY frontend/src ./src

# Build static bundle
RUN npm run build

# Nginx production stage
FROM nginx:alpine

# Copy built bundle assets
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy Nginx proxy configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
