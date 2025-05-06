FROM node:14-alpine

WORKDIR /app

# Clean install
RUN rm -rf node_modules package-lock.json

# Copy package.json
COPY package.json ./

# Install with legacy peer deps and frozen lockfile
RUN npm cache clean --force && \
    npm install --legacy-peer-deps

# Copy the rest of the files
COPY . .

# Start the app
CMD ["npm", "start"]