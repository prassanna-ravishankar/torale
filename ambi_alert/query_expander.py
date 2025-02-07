"""Query expansion and translation module."""

from typing import Optional

from smolagents import HfApiModel
from smolagents.agents import MultiStepAgent
from smolagents.memory import ActionStep


class QueryExpanderAgent(MultiStepAgent):
    """Agent that expands user queries into more comprehensive search terms."""

    def __init__(self, model: Optional[HfApiModel] = None):
        """Initialize the query expander agent.

        Args:
            model: Optional HfApiModel instance. If None, creates a new one.
        """
        super().__init__(
            tools=[],  # No tools needed, just LLM abilities
            model=model or HfApiModel(),
            name="query_expander",
            description="""This agent specializes in expanding search queries to cover different aspects of a topic.
            It takes a user query and generates multiple related search queries that help capture the full scope
            of what the user wants to monitor.""",
        )

    def initialize_system_prompt(self) -> str:
        """Get the system prompt for this agent.

        Returns:
            The system prompt describing the agent's role
        """
        return """You are a query expansion specialist. Your role is to take user queries and expand them
        into multiple specific search queries that cover different aspects of the topic. You focus on
        creating queries that are:
        1. Specific and well-defined
        2. Cover different aspects of the topic
        3. Include related terms and synonyms
        4. Consider both current state and future developments

        When you receive a query, analyze it and return expanded queries using the final_answer tool.
        Return just the expanded queries, one per line, without any additional text or formatting.

        Example:
        User: "next iPhone"
        Assistant: Let me expand this query.
        <tool>final_answer
        iPhone 16 release date
        iPhone 16 specifications leak
        iPhone 16 Pro features
        Apple smartphone roadmap 2024</tool>"""

    def step(self, memory_step: ActionStep) -> Optional[list[str]]:
        """Execute one step of query expansion.

        Args:
            memory_step: The current memory step

        Returns:
            List of expanded queries if final step, None otherwise
        """
        messages = self.write_memory_to_messages()
        chat_message = self.model(messages)
        memory_step.model_output_message = chat_message

        # Process the response
        response = chat_message.content
        if "final_answer" not in response.lower():
            return None

        # Extract queries from the response
        queries_text = response.split("final_answer")[-1].strip()
        expanded_queries = [
            q.strip()
            for q in queries_text.split("\n")
            if q.strip() and not q.strip().startswith(("-", "*", "•", "<", ">"))
        ]

        # Ensure we have at least one query
        if not expanded_queries:
            expanded_queries = [self.task]  # Fall back to original query

        return expanded_queries

    def run(self, query: str) -> list[str]:
        """Expand a user query into multiple search-optimized queries.

        Args:
            query: The original user query

        Returns:
            A list of expanded search queries
        """
        result = super().run(query)
        if isinstance(result, list):
            return result
        return [query]  # Fallback to original query if something goes wrong
