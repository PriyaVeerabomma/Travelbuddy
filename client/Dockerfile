FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the code
COPY . .

# Expose port for development server (typically 3000 for React)
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]