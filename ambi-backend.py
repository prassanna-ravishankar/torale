from smolagents import (
    DuckDuckGoSearchTool,
    HfApiModel,
    ToolCallingAgent,
    VisitWebpageTool,
)

# Setup the model
model = HfApiModel()

# Create a single search agent
search_agent = ToolCallingAgent(
    tools=[DuckDuckGoSearchTool(), VisitWebpageTool()],
    model=model,
    name="search_agent",
    description="This is an agent that searches for and visits relevant websites."
)

# Run the search directly
results = search_agent.run("Find websites about artificial intelligence")

print(results)