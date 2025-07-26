from crewai import Agent
from textwrap import dedent
from langchain_groq import ChatGroq  # ✅ Make sure this is installed
from dotenv import load_dotenv
import os

from tools.search_tools import SearchTools
from tools.calculator_tools import CalculatorTools
import streamlit as st

load_dotenv()

class TravelAgents:
    def __init__(self):
      
        self.llm = ChatGroq(model="groq/llama-3.3-70b-versatile")

    def Trip_Planner_Agent(self):
        return Agent(
            role="The lead agent responsible for coordinating the entire trip planning process.",
            backstory=dedent("An experienced travel consultant with decades of experience."),
            goal=dedent("Develop a detailed, personalized travel itinerary covering all aspects."),
            allow_delegation=False,
            verbose=True,
            memory=True,
            llm=self.llm,
        )

    def Destination_Research_Agent(self):
        return Agent(
            role="An expert in destination insights, famous places, and cultural experiences.",
            backstory=dedent("A well-traveled explorer with deep knowledge of global cultures."),
            goal=dedent("Analyze and recommend the best destination details for the trip."),
            tools=[SearchTools.search_internet],
            allow_delegation=True,
            verbose=True,
            memory=True,
            llm=self.llm,
        )

    def Accommodation_Agent(self):
        return Agent(
            role="Accommodation advisor based on comfort, location, and budget.",
            backstory=dedent("A seasoned traveler who knows what makes a stay perfect."),
            goal=dedent("Provide a list of accommodation options with current pricing."),
            tools=[SearchTools.search_internet, CalculatorTools.calculate],
            allow_delegation=True,
            verbose=True,
            memory=True,
            llm=self.llm,
        )

    def Transportation_Agent(self):
        return Agent(
            role="Transport planner optimizing cost and efficiency.",
            backstory=dedent("Expert in travel logistics and multimodal transportation."),
            goal=dedent("Design detailed travel logistics for each leg of the trip."),
            tools=[SearchTools.search_internet, CalculatorTools.calculate],
            allow_delegation=True,
            verbose=True,
            memory=True,
            llm=self.llm,
        )

    def Weather_Agent(self):
        return Agent(
            role="Weather forecaster and climate advisor.",
            backstory=dedent("Meteorologist with expertise in travel-related climate concerns."),
            goal=dedent("Provide accurate weather forecasts and packing recommendations."),
            tools=[SearchTools.search_internet],
            allow_delegation=True,
            verbose=True,
            memory=True,
            llm=self.llm,
        )

    def Itinerary_Planner_Agent(self):
        return Agent(
            role="Detailed itinerary planner for the destination.",
            backstory=dedent("Planner skilled in balancing activities, relaxation, and cuisine."),
            goal=dedent("Craft daily schedules considering activities, food, weather, and mood."),
            tools=[SearchTools.search_internet],
            allow_delegation=True,
            verbose=True,
            memory=True,
            llm=self.llm,
        )

    def Budget_Analyst_Agent(self):
        return Agent(
            role="Financial strategist for travel planning.",
            backstory=dedent("Finance pro who turns budget trips into luxury experiences."),
            goal=dedent("Give a budget breakdown with savings and luxury tiers."),
            tools=[SearchTools.search_internet, CalculatorTools.calculate],
            allow_delegation=True,
            verbose=True,
            memory=True,
            llm=self.llm,
        )
