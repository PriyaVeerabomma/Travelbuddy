"""Post-trip agent. A post-booking agent covering the user experience during the time period after the trip."""

from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate

from subagents.post_travel import prompt
from tools.memory import memorize

# Create memorize tool
memorize_tool = Tool(
    name="memorize",
    description="Store important information for future reference",
    func=memorize
)

# Create the LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# Create prompt template
post_trip_prompt = ChatPromptTemplate.from_template(prompt.POSTTRIP_INSTR)

# Create the agent
post_trip_agent = create_openai_tools_agent(llm, [memorize_tool], post_trip_prompt)

# Create the executor
post_trip_executor = AgentExecutor(
    agent=post_trip_agent,
    tools=[memorize_tool],
    handle_parsing_errors=True,
    verbose=True
)