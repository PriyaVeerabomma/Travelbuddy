#  TravelBuddy – AI-Powered Travel Planning Assistant

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0+-00a393.svg)](https://fastapi.tiangolo.com/)
[![React.js](https://img.shields.io/badge/-ReactJs-61DAFB?logo=react&logoColor=white&style=for-the-badge)
[![Docker](https://img.shields.io/badge/Docker-20.10.8+-blue.svg)](https://www.docker.com/)
[![LLM Agents](https://img.shields.io/badge/Agents-CrewAI%20%2B%20LLMs-purple.svg)](https://github.com/joaomdmoura/crewAI)
[![Vector DB](https://img.shields.io/badge/Vector%20Search-Pinecone-009adf.svg)](https://www.pinecone.io/)
[![Data Warehouse](https://img.shields.io/badge/Data%20Analytics-Snowflake-29b5e8.svg)](https://www.snowflake.com/)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI-blueviolet.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-Codelabs-blue.svg)](https://codelabs-preview.appspot.com/?file_id=1kMzJ_qRJrDknPFatF1raPvsoJUatl_-tfJuICo7p4EM#0)

**TravelBuddy** is a next-gen AI travel planner that creates fully personalized travel itineraries through natural language conversations. Built using a modular, multi-agent architecture, semantic search, and real-time travel APIs, it offers a unified, intelligent travel planning experience.

## Project URLs
- Code Labs: [Codelabs Documentation](https://codelabs-preview.appspot.com/?file_id=1tutswOpFN6G73kNlOOBUUXkxT-XiGBHQ0f_FO67wKHs#0)
- Application: [Front End](https://travelai.me/)
- Swagger: [Swagger](http://34.45.163.161:8000/docs)
- Airflow: [Airflow](http://159.89.95.178:8080/home)
- Live Demo : [Travel AI](https://travelai.me/)
- Walkthrough Video : [Application Walkthrough](https://drive.google.com/drive/folders/1898HGutXjQIxwx3OVnr_Yvx9Uq_SKAE1?usp=sharing)
- Github Tasks: [GitHub Issues and Tasks](https://github.com/DAMG7245/Travel_Buddy/issues?q=is%3Aissue%20state%3Aclosed&page=1)
---

##  Key Features

-  **Multi-Agent Architecture** – Dedicated AI agents for flights, hotels, weather, events, safety, and itinerary creation.
-  **Semantic Search** – Enables personalized travel recommendations based on user intent.
-  **Real-Time Integrations** – Connects with leading travel APIs like OpenWeather, Amadeus, Booking.com, Google Places, and more.
-  **Snowflake Analytics** – Stores and visualizes trends in travel data, such as flight pricing, weather patterns.
-  **Auto-Generated Itineraries** – End-to-end travel plans, exportable as PDFs(coming soon).

---
##  Project Overview

###  User Interaction Flow
1. Start a conversation with TravelBuddy.
2. Describe your travel preferences or ask for suggestions.
3. Backend routes the request to specialized agents.
4. Agents fetch and analyze flights, weather, hotels, etc.
5. The itinerary agent assembles a plan.
6. Receive a full itinerary with options to adjust/export.

##  Core Features

### 1. Multi-Agent Architecture
- Specialized AI agents (weather, flights, hotel, events, itinerary)
- Root agent dynamically coordinates all sub-agents

### 2. Semantic Search & Personalization
- Intent understanding via Pinecone vector embeddings
- Personalized recommendations based on interests

### 3. Real-Time Integrations
- Connected to OpenWeather, Amadeus, TripAdvisor, Eventbrite, and more

### 4. Intelligent Itinerary Generation
- Unified output from all agents
- Travel plan delivered as JSON or PDF

### 5. Travel Analytics
- Hotel pricing trends, weather forecasts, attraction popularity
- Powered by Snowflake dashboards

---
## Methodology

### Data Gathering
- APIs: OpenWeather, Amadeus, Booking, TripAdvisor
- Normalized and validated upon ingestion

### Agentic Execution
- rootAgent receives task
- Delegates to:
  - planning_agent (hotels, restaurants, flights)
  - explore_agent (places)
  - weather_agent (forecast)
  - itinerary_agent (final assembly)

### Itinerary Assembly
- Aggregates outputs
- Routes to itinerary_agent
- Final JSON returned or exported as PDF

### Challenges

- Travel planning is fragmented across platforms
- Lack of semantic search and true personalization
- Manual itinerary creation is time-consuming
- Contextual factors like weather or advisories are not integrated

### Opportunities

- Natural language understanding for preferences
- Vector embeddings for intent-based recommendations
- Unified travel experience in one platform
- Learn from user feedback to improve over time

---

##  Architecture

## AgentFlow
![image](https://github.com/user-attachments/assets/afd57572-3403-44e0-b285-9eb53e23ac75)

## MCP flow
![image](https://github.com/user-attachments/assets/9172176b-ae8e-42aa-885b-f9a7f0bf16ca)

## User Flow

![image](https://github.com/user-attachments/assets/86233095-7990-4194-9c4f-5303fce3bd28)


##  Data Pipeline

1. **User Query Ingestion** – Requests originate from client-side React frontend and are routed through FastAPI endpoints.
2. **Intent Parsing & Agent Dispatch** – rootAgent interprets user intent and activates relevant sub-agents (weather, explore, planning).
3. **Real-Time API Retrieval** – Each sub-agent calls external APIs (OpenWeather, Amadeus, Booking, etc.) for live travel data.
4. **Data Transformation** – Responses are normalized and structured by internal parsers and tool modules (`tools/*.py`).
5. **Analytics Integration** – Cleaned data is logged to Snowflake for trend analysis, pricing models, and user insights.
6. **Itinerary Compilation** – itinerary_agent consolidates outputs into a cohesive, step-wise travel plan.
7. **Response Delivery** – Final results returned via API/UI as structured JSON .

---   
##  Microservices & APIs

| Service              | Purpose                              | Example Endpoint                          |
|----------------------|---------------------------------------|-------------------------------------------|
| Weather              | Forecasts & historical trends         | `/api/weather/forecast/{location}`        |
| Flight Search        | Flight offers and pricing             | `/api/flights/search`                     |
| Hotel Booking        | Accommodation matching                | `/api/hotels/search`                      |
| Attractions & Tours  | POI recommendations                   | `/api/attractions/recommended`           |
| Event Discovery      | Local events during travel            | `/api/events/search/{location}`           |
| Safety Advisory      | Risk alerts and travel warnings       | `/api/safety/advisory/{country}`          |
| Itinerary Generator  | Full trip plan generation             | `/api/itinerary/generate`                 |




##  Technology Stack

### Backend
- ![Python](https://img.shields.io/badge/Python-FFD43B?style=flat&logo=python&logoColor=blue)
- ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
- ![JWT](https://img.shields.io/badge/JWT-black?style=flat&logo=JSON%20web%20tokens)
- ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)

### Frontend
- ![Next.js](https://img.shields.io/badge/Next.js-black?style=flat&logo=next.js&logoColor=white)
- ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white)
- ![shadcn/ui](https://img.shields.io/badge/shadcn/ui-gray?style=flat&logo=vercel&logoColor=white)


### AI/ML
- ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
- LangGraph


### Cloud & DevOps
- ![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazon-aws&logoColor=white)
- ![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=flat&logo=docker&logoColor=white)
- ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
- ![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-017CEE?style=flat&logo=Apache%20Airflow&logoColor=white)

- ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi&logoColor=white)
- ![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)
- ![Pinecone](https://img.shields.io/badge/Pinecone-009adf?style=flat&logo=pinecone&logoColor=white)
- ![Snowflake](https://img.shields.io/badge/Snowflake-29b5e8?style=flat&logo=snowflake&logoColor=white)
- ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
- ![Groq](https://img.shields.io/badge/Groq%20LLaMA3-ff4b4b?style=flat&logo=groq&logoColor=white)
- ![Amadeus](https://img.shields.io/badge/Amadeus_API-0071C5?style=flat&logo=airfrance&logoColor=white)
- ![OpenWeather](https://img.shields.io/badge/OpenWeather-FF7E00?style=flat&logo=OpenWeatherMap&logoColor=white)


# Travel_Buddy Setup Guide

## Prerequisites

1. **Python 3.8+**
   - Python 3.8 or newer
   - Verify with: `python --version` or `python3 --version`

2. **Node.js and npm**
   - Node.js 16+ and npm 8+ recommended
   - Verify with: `node --version` and `npm --version`

3. **API Keys**
   - OpenAI API key
   - OpenWeather API key
   - Google Maps API key
   - Google Places API key
   - Amadeus API credentials (client ID and secret)

4. **Database**
   - PostgreSQL database
   - Snowflake account for analytics

5. **Docker and Docker Compose** (optional)
   - For containerized deployment

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Travel_Buddy.git
cd Travel_Buddy
```

### 2. Set Up Environment Variables

1. Copy the sample .env file:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your credentials:
```
# PostgreSQL Database Configuration
DB_HOST=your-postgres-host
DB_PORT=your-postgres-port
DB_NAME=travelbuddy
DB_USER=your-username
DB_PASSWORD=your-password
DB_SSL_MODE=require

# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain
AUTH0_AUDIENCE=your-auth0-audience

# API Keys
OPENAI_API_KEY=your-openai-api-key
OPENWEATHER_API_KEY=your-openweather-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
GOOGLE_PLACES_API_KEY=your-google-places-api-key
AMADEUS_CLIENT_ID=your-amadeus-client-id
AMADEUS_CLIENT_SECRET=your-amadeus-client-secret

# Snowflake Configuration
SNOWFLAKE_USER=your-snowflake-user
SNOWFLAKE_PASSWORD=your-snowflake-password
SNOWFLAKE_ACCOUNT=your-snowflake-account
SNOWFLAKE_WAREHOUSE=your-snowflake-warehouse
SNOWFLAKE_DATABASE=your-snowflake-database
SNOWFLAKE_SCHEMA=your-snowflake-schema

# Other settings
FRONTEND_URL=http://localhost:3000
PORT=8000
```

### 3. Set Up Backend

1. Create a Python virtual environment:
```bash
python -m venv myenv
```

2. Activate the virtual environment:
   - Windows: `myenv\Scripts\activate`
   - macOS/Linux: `source myenv/bin/activate`

3. Install backend dependencies:
```bash
cd server
pip install -r requirements.txt
cd ../flight_service
pip install -r requirements.txt
cd ..
```

### 4. Set Up Frontend

```bash
cd client
npm install
cd ..
```

### 5. Start the Services

**Option 1: Individual services (development)**

1. Start the backend server:
```bash
cd server
python main.py
```

2. Start the flight service (new terminal):
```bash
cd flight_service
python -m app.main
```

3. Start the frontend (new terminal):
```bash
cd client
npm run dev
```

**Option 2: Docker Compose**

```bash
docker-compose up
```

### 6. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Flight Service API: http://localhost:8001
```
Project Structure

Travel_Buddy/
├── client/                     # Frontend React application
│   ├── src/                    # React source code
│   │   ├── components/         # UI components
│   │   │   ├── ChatComponent.tsx  # Main chat interface
│   │   │   ├── MapComponent.tsx   # Map visualization
│   │   │   └── WeatherDisplay.tsx # Weather display
│   │   ├── pages/              # Application pages
│   │   └── api/                # API integration
│   ├── package.json            # Frontend dependencies
│   └── .env                    # Frontend environment variables
│
├── server/                     # Main backend server
│   ├── agents/                 # AI agent system
│   │   ├── rootAgent.py        # Main agent coordinator
│   │   └── prompt.py           # Agent prompts
│   ├── subagents/              # Specialized AI agents
│   │   ├── explore/            # Exploration agent
│   │   ├── planning/           # Planning agent
│   │   └── pre_travel/         # Pre-travel agent
│   ├── tools/                  # External API integrations
│   │   ├── weather_tool.py     # Weather data integration
│   │   ├── flight_search.py    # Flight search tool
│   │   └── hotel_search.py     # Hotel search tool
│   ├── main.py                 # Main server entry point
│   └── requirements.txt        # Backend dependencies
│
├── flight_service/             # Flight microservice
│   ├── app/                    # Flight service code
│   │   ├── main.py             # Flight service entry point
│   │   ├── api/                # Flight API endpoints
│   │   └── services/           # Flight data services
│   └── requirements.txt        # Flight service dependencies
│
├── weekly-weather-mcp-master/  # Model Context Protocol for weather
│   ├── simplified_mcp_server.py # MCP server implementation
│   └── weather_agent.py        # Weather agent implementation
│
├── .gitignore                  # Git ignored files
├── .env                        # Project environment variables
├── docker-compose.yaml         # Docker configuration
└── README.md                   # Project documentation
```
##  Notes

1. **Weather MCP Server**
   - Weather tool uses the Model Context Protocol (MCP) server
   - Verify the MCP server path in `server/tools/weather_tool.py`
   - Adjust path based on your setup

2. **Database Setup**
   - Server creates tables automatically on startup
   - Verify database credentials in the .env file

3. **Auth0 Setup**
   - Configure settings in Auth0 dashboard
   - Update Auth0 configuration in .env and frontend code

4. **Troubleshooting**
   - API key errors: Verify all keys in .env
   - Database issues: Check database is running and accessible
   - MCP server issues: Verify path and API keys (OpenWeather and OpenAI)

## 👥 Contributors

- Sai Priya Veerabomma
- Sai Srunith Silvery
- Vishal Prasanna

---

## 📜 License

MIT License – Feel free to fork, extend, and build upon TravelBuddy.

---
## 🤖 AI Usage Disclosure

AI tools such as OpenAI GPT, LangChain, and GitHub Copilot were used for implementing multi-agent travel assistance, generating responses, and supporting development tasks like code scaffolding and prompt tuning.

