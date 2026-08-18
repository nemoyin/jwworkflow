# 前端镜像：生产构建 + nginx 静态托管，反代 /api 到后端容器
# 构建上下文：./frontend
FROM node:20-slim AS build
WORKDIR /fe
COPY package.json package-lock.json ./
# 国内网络：使用 npmmirror 镜像，避免 registry.npmjs.org 超时
RUN npm ci --registry=https://registry.npmmirror.com
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /fe/dist /usr/share/nginx/html
EXPOSE 80
