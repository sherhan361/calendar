FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# API-\u0431\u0430\u0437\u0430 \u0432\u0448\u0438\u0432\u0430\u0435\u0442\u0441\u044f \u043d\u0430 \u044d\u0442\u0430\u043f\u0435 \u0441\u0431\u043e\u0440\u043a\u0438. \u041f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e \u0437\u0430\u043f\u0440\u043e\u0441\u044b \u0438\u0434\u0443\u0442 \u043d\u0430 /api,
# \u043a\u043e\u0442\u043e\u0440\u044b\u0439 nginx \u043f\u0440\u043e\u043a\u0441\u0438\u0440\u0443\u0435\u0442 \u043d\u0430 backend.
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
