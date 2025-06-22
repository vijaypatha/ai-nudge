# frontend/Dockerfile

# Use an official Node.js runtime as a parent image
FROM node:20-alpine AS base

# Set working directory
WORKDIR /app

# Ensure a clean slate for dependencies
# Remove existing node_modules and .next if they somehow persist, though WORKDIR should make this less critical
RUN rm -rf node_modules .next

# Copy package.json and package-lock.json first to leverage Docker caching
COPY package.json ./
COPY package-lock.json ./

# Use npm ci for clean, reproducible installs in automated environments
# npm ci ensures dependencies are installed exactly as per package-lock.json
RUN npm ci

# Explicitly install SWC variants if not already installed by npm ci correctly
# This step might be redundant if npm ci works perfectly, but helps in tricky cases
RUN npm install @next/swc-linux-x64@latest @next/swc-wasm@latest --save-dev || true

# Copy the rest of the application code
COPY . .

# Build the Next.js application for production
# This uses the dependencies installed above
RUN npm run build

# --- Production Stage ---
FROM node:20-alpine AS production

WORKDIR /app

# Copy built assets from the base stage
COPY --from=base /app/.next ./.next
COPY --from=base /app/public ./public
COPY --from=base /app/package.json ./package.json

# Copy only production dependencies if needed by `npm start`.
# npm ci in the base stage already ensures only prod deps are needed for build.
# For runtime, next start bundles most. But if node_modules are still needed for start,
# ensure to copy from base if they were installed with --omit=dev.
# Since `npm ci` was used above, all deps are installed, so copy them.
COPY --from=base /app/node_modules ./node_modules

# Expose port 3000
EXPOSE 3000

# Command to run the Next.js application
CMD ["npm", "start"]