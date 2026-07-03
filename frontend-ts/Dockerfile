# Build stage
FROM node:20-slim AS build

WORKDIR /app

# Install dependencies efficiently
COPY package*.json ./
RUN npm install

# Build the app
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
