# Multi-stage build for Next.js

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application files
COPY . .

# Set environment variable for build
ENV NEXT_TELEMETRY_DISABLED=1

# Build application (for production)
# RUN npm run build

# Stage 3: Development
FROM node:20-alpine AS development
WORKDIR /app

# Set environment variables
ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev)
RUN npm ci

# Copy application files
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Default command
CMD ["npm", "run", "dev"]

# Stage 4: Production (commented out for now, will use in production)
# FROM node:20-alpine AS production
# WORKDIR /app
#
# ENV NODE_ENV=production \
#     NEXT_TELEMETRY_DISABLED=1
#
# RUN addgroup --system --gid 1001 nodejs && \
#     adduser --system --uid 1001 nextjs
#
# COPY --from=builder /app/public ./public
# COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
# COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
#
# USER nextjs
#
# EXPOSE 3000
#
# ENV PORT=3000
#
# CMD ["node", "server.js"]
