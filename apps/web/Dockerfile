FROM node:22-alpine AS builder
ARG NPM_REGISTRY=https://registry.npmjs.org
RUN npm install --global pnpm@11.16.0 --registry=${NPM_REGISTRY}
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm config set registry ${NPM_REGISTRY} \
    && pnpm install --frozen-lockfile --fetch-retries 5
COPY apps/web ./apps/web
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN pnpm --filter @yyglobal/web build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
