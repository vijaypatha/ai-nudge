# Use an official Node.js runtime as a parent image
FROM node:20-alpine AS base

# Set working directory
WORKDIR /app

# Install dependencies (this layer is cached)
COPY package.json ./
COPY package-lock.json ./
RUN npm install --omit=dev # Install only production dependencies first

# Copy the rest of the application code
COPY . .

# Build the Next.js application
# RUN npm run build # This would typically be here, but for --output=standalone, it's different. See below.

# --- Production Stage ---
FROM node:20-alpine AS production

WORKDIR /app

# Copy environment variables, if any are needed at build time for Next.js
# ENV NODE_ENV production # Already set by Next.js start

# Copy built assets from the build stage
# If using default `next build` (not standalone output):
# COPY --from=base /app/.next ./.next
# COPY --from=base /app/public ./public
# COPY --from=base /app/package.json ./package.json
# COPY --from=base /app/node_modules ./node_modules # if not bundling them

# For Next.js 14+ with output: "standalone" in next.config.js (recommended for Docker)
# The build command `npm run build` in the 'base' stage should have created a folder
# typically at .next/standalone. We copy that.
# Ensure next.config.js has `output: 'standalone'` for this to work best.
# For now, assuming standard build without explicit standalone for simplicity in this step,
# but will adjust if `next.config.js` is updated for `output: 'standalone'`.

COPY --from=base /app/.next ./.next
COPY --from=base /app/public ./public
COPY --from=base /app/package.json ./package.json
# If node_modules are not bundled by Next.js build (they usually are for server components, but client might need some)
# We already ran npm install in base, so node_modules are there.
# For a smaller image, you'd ensure only necessary node_modules are copied or re-installed.
# However, with `npm install --omit=dev`, we already have only production deps.
COPY --from=base /app/node_modules ./node_modules


# Expose port 3000
EXPOSE 3000

# Command to run the Next.js application
CMD ["npm", "start"]

# --- Development Stage (Optional, if you want a dev Docker setup) ---
# FROM node:20-alpine AS development
# WORKDIR /app
# COPY package.json ./
# COPY package-lock.json ./
# RUN npm install
# COPY . .
# EXPOSE 3000
# CMD ["npm", "run", "dev"]
