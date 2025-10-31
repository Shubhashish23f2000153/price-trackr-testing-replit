FROM node:20-alpine AS builder
WORKDIR /app

# This ARG now correctly receives the key from docker-compose.yml
ARG VITE_VAPID_PUBLIC_KEY

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# --- THIS IS THE NEW FIX ---
# We use 'sed' to find our placeholder in api.ts and replace it with the real key.
# This happens *before* the build, so the key is hard-coded into the code.
RUN echo "--- Injecting VAPID key into api.ts ---" && \
    sed -i "s|VITE_VAPID_PUBLIC_KEY_PLACEHOLDER|${VITE_VAPID_PUBLIC_KEY}|g" /app/src/services/api.ts

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]