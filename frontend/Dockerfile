# Production build with nginx - faster than dev
FROM node:20-alpine as builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
ENV PORT=80
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
