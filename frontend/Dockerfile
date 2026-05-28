FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

# In production the frontend talks to the same host via nginx (/api relative path)
ENV REACT_APP_API_ORIGIN=

RUN npm run build

# ── Production image ──────────────────────────────────────────────────────────
FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
