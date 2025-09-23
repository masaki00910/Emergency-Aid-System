# ===== DEPENDENCIES STAGE =====
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

# ===== BUILDER STAGE =====
FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build with increased memory and environment variables
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV NEXT_TELEMETRY_DISABLED=1

# Set build-time environment variables for Next.js
ENV NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyClMkxDt4S0hQHmY6p8eF2a3_Il4UvyRag
ENV NEXT_PUBLIC_API_URL=https://disaster-api-670435464520.asia-northeast1.run.app
ENV NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyCk3szzw0MWHuYxHv6a6F8olD_aKDNIZLY
ENV NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=sharelabai-hackathon2.firebaseapp.com
ENV NEXT_PUBLIC_FIREBASE_PROJECT_ID=sharelabai-hackathon2
ENV NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=sharelabai-hackathon2.firebasestorage.app
ENV NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=670435464520
ENV NEXT_PUBLIC_FIREBASE_APP_ID=1:670435464520:web:80d9ef3890bb138df94f7d

RUN npm run build

# ===== RUNNER STAGE =====
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# Start the application
CMD ["node", "server.js"]