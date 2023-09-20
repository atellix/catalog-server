# Dockerfile
FROM node:18-alpine

# create destination directory
RUN mkdir -p /usr/src/qmarket
WORKDIR /usr/src/qmarket

# update and install dependency
RUN apk update && apk upgrade
RUN apk add git

# copy the app, note .dockerignore
COPY package.json /usr/src/qmarket/package.json
COPY package-lock.json /usr/src/qmarket/package-lock.json
COPY tsconfig.json /usr/src/qmarket/tsconfig.json

RUN npm install -g npm@9.8.1
RUN npm install

COPY nuxt.config.ts /usr/src/qmarket/nuxt.config.ts
COPY src /usr/src/qmarket/src

RUN npm run build

EXPOSE 3000

ENV NUXT_HOST=0.0.0.0
ENV NUXT_PORT=3000

CMD [ "npm", "run", "start" ]
