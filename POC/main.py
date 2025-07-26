from crewai import Crew, Process
from agents import TravelAgents
from tasks import TravelTasks
from tools.file_io import save_markdown
from dotenv import load_dotenv

load_dotenv()

class TripCrew:
    def __init__(self, origin, destination, date_range, interests, person):
        self.origin = origin
        self.destination = destination
        self.date_range = date_range
        self.interests = interests
        self.person = person

    def run(self):
        # ✅ Initialize agents and share the LLM
        agents = TravelAgents()
        self.llm = agents.llm  # ✅ Grab the LLM to reuse as manager_llm
        tasks = TravelTasks()

        # Define your custom agents
        Trip_Planner_Agent = agents.Trip_Planner_Agent()
        Destination_Research_Agent = agents.Destination_Research_Agent()
        Accommodation_Agent = agents.Accommodation_Agent()
        Transportation_Agent = agents.Transportation_Agent()
        Weather_Agent = agents.Weather_Agent()
        Itinerary_Planner_Agent = agents.Itinerary_Planner_Agent()
        Budget_Analyst_Agent = agents.Budget_Analyst_Agent()

        # Define your custom tasks
        Research_Destination_Highlights = tasks.Research_Destination_Highlights(
            Destination_Research_Agent, 
            self.origin, 
            self.destination,
            self.date_range, 
            self.interests, 
            self.person)

        Discover_Local_Cuisine = tasks.Discover_Local_Cuisine(
            Destination_Research_Agent, 
            self.destination,
            self.date_range, 
            self.person)

        Find_Your_Perfect_Stay = tasks.Find_Your_Perfect_Stay(
            Accommodation_Agent, 
            self.destination,
            self.date_range, 
            self.person)

        Transportation_Between_Destinations = tasks.Transportation_Between_Destinations(
            Transportation_Agent, 
            self.origin, 
            self.destination,
            self.date_range, 
            self.person)

        Plan_Local_Transportation = tasks.Plan_Local_Transportation(
            Transportation_Agent, 
            self.destination,
            self.date_range, 
            self.person)

        Info_Transportation_Passes = tasks.Info_Transportation_Passes(
            Transportation_Agent, 
            self.destination,
            self.date_range, 
            self.person)

        Weather_Forecasts = tasks.Weather_Forecasts(
            Weather_Agent, 
            self.destination,
            self.date_range)

        Daily_Itineraries = tasks.Daily_Itineraries(
            Itinerary_Planner_Agent, 
            self.destination,
            self.date_range, 
            self.interests, 
            self.person)

        Budget_Plan = tasks.Budget_Plan(
            Budget_Analyst_Agent, 
            self.destination,
            self.date_range, 
            self.person)

        Final_Trip_Plan = tasks.Final_Trip_Plan(
            Trip_Planner_Agent,
            [
                Research_Destination_Highlights, Discover_Local_Cuisine,
                Find_Your_Perfect_Stay, Transportation_Between_Destinations,
                Plan_Local_Transportation, Info_Transportation_Passes,
                Weather_Forecasts, Daily_Itineraries, Budget_Plan
            ],
            self.origin, 
            self.destination,
            self.date_range, 
            self.interests, 
            self.person,
            save_markdown)

        # ✅ Create the crew with shared LLM for manager_llm
        crew = Crew(
            agents=[
                Destination_Research_Agent,
                Accommodation_Agent,
                Transportation_Agent,
                Weather_Agent,
                Itinerary_Planner_Agent,
                Budget_Analyst_Agent,
                Trip_Planner_Agent
            ],
            tasks=[
                Research_Destination_Highlights,
                Discover_Local_Cuisine,
                Find_Your_Perfect_Stay,
                Transportation_Between_Destinations,
                Plan_Local_Transportation,
                Info_Transportation_Passes,
                Weather_Forecasts,
                Daily_Itineraries,
                Budget_Plan,
                Final_Trip_Plan
            ],
            process=Process.sequential,
            manager_llm=self.llm,  # ✅ FIXED: Prevents LiteLLM fallback
            verbose=True,
            max_rpm=5
        )

        result = crew.kickoff()
        return result


# ✅ CLI/Run this file directly
if __name__ == "__main__":
   pass
