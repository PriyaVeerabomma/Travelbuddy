# FastAPI User Authentication with Auth0 and PostgreSQL

This project implements a user authentication system using FastAPI, SQLAlchemy, PostgreSQL, and Auth0.

## Project Structure

```
server/
├── controllers/
│   └── userController.py      # User business logic
├── middlewares/
│   ├── auth.py                # Auth middleware
│   ├── conn_database.py       # Database connection
│   └── init_db.py             # Database initialization
├── model/
│   └── userModel.py           # User model definitions
├── routes/
│   └── userRoute.py           # User route definitions
├── .env                       # Environment variables (not in version control)
├── Dockerfile                 # Docker container configuration
├── main.py                    # Main application entry point
└── requirements.txt           # Project dependencies
```

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**

Create a `.env` file in the root directory with the following variables:

```
# PostgreSQL Database Configuration
DB_HOST=pg-travelbuddy-watchwave.b.aivencloud.com
DB_PORT=10075
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=your_password_here
DB_SSL_MODE=require

# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_AUDIENCE=your-auth0-api-identifier

# Application Settings
FRONTEND_URL=http://localhost:3000
PORT=8000
```

Replace `your_password_here` with your actual Aiven PostgreSQL password.

3. **Run the application:**

```bash
python main.py
```

The API will be available at http://localhost:8000.

## API Endpoints

- `POST /api/users/`: Create a new user
- `GET /api/users/`: Get current user details (requires authentication)
- `PUT /api/users/`: Update user details (requires authentication)

## Authentication

This API uses Auth0 for authentication. The client should obtain a JWT token from Auth0 and include it in the `Authorization` header as `Bearer {token}`.

## Docker Support

The application can be containerized using Docker:

```bash
# Build the Docker image
docker build -t user-auth-api .

# Run the container
docker run -p 8000:8000 --env-file .env user-auth-api
```

## Swagger Documentation

FastAPI automatically generates Swagger documentation, which can be accessed at http://localhost:8000/docs when the application is running.

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**

Create a `.env` file in the root directory by copying the `.env.example` file:

```bash
cp .env.example .env
```

Then edit the `.env` file with your actual credentials:

```
# PostgreSQL Database Configuration
DB_HOST=your_host
DB_PORT=your_port
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password_here
DB_SSL_MODE=your_requirement

# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_AUDIENCE=your-auth0-api-identifier

# Application Settings
FRONTEND_URL=http://localhost:3000
```

Replace `your_password_here` with your actual Aiven PostgreSQL password.

3. **Set up PostgreSQL:**

Create a PostgreSQL database and update the `DATABASE_URL` environment variable.

4. **Run the application:**

```bash
python main.py
```

The API will be available at http://localhost:8000.

## API Endpoints

- `POST /api/users/`: Create a new user
- `GET /api/users/`: Get current user details (requires authentication)
- `PUT /api/users/`: Update user details (requires authentication)

## Authentication

This API uses Auth0 for authentication. The client should obtain a JWT token from Auth0 and include it in the `Authorization` header as `Bearer {token}`.

## Swagger Documentation

FastAPI automatically generates Swagger documentation, which can be accessed at http://localhost:8000/docs when the application is running.