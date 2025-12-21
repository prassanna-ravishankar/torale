import logging

from torale.core.state_utils import compute_state_hash
from torale.monitoring.monitoring import MonitoringResult
from torale.monitoring.providers.comparison_provider import ComparisonProvider
from torale.monitoring.providers.extraction_provider import ExtractionProvider
from torale.monitoring.providers.schema_provider import SchemaProvider

logger = logging.getLogger(__name__)


class MonitoringPipeline:
    """
    Orchestrates monitoring execution using providers.

    Implements the structured agency approach:
    1. Agent generates/retrieves task-specific schema
    2. Agent extracts current state to schema
    3. Fast hash pre-filter for identical states
    4. Agent performs semantic comparison if hash differs
    5. Generate natural language summary

    This solves Issue #111 by using single extraction source for all decisions.
    """

    def __init__(
        self,
        schema_provider: SchemaProvider,
        extraction_provider: ExtractionProvider,
        comparison_provider: ComparisonProvider,
    ):
        self.schema_provider = schema_provider
        self.extraction_provider = extraction_provider
        self.comparison_provider = comparison_provider

    async def execute(
        self,
        task: dict,
        search_result: dict,
        previous_state: dict | None = None,
    ) -> MonitoringResult:
        """
        Execute monitoring pipeline.

        Args:
            task: Task configuration with search_query, condition_description
            search_result: Result from search provider with answer and sources
            previous_state: Previous extracted state (None if first execution)

        Returns:
            MonitoringResult with summary, sources, actions, and metadata
        """
        actions = ["searched"]

        # Step 1: Get or generate schema for this task
        logger.info("Step 1: Getting extraction schema")
        schema = await self.schema_provider.get_or_create_schema(task)
        logger.debug(f"Schema: {schema}")

        # Step 2: Extract current state according to schema
        logger.info("Step 2: Extracting current state")
        current_state = await self.extraction_provider.extract(search_result, schema)
        logger.debug(f"Extracted state: {current_state}")
        actions.append("extracted")

        # Step 3: Fast hash pre-filter
        if previous_state:
            prev_hash = compute_state_hash(previous_state)
            curr_hash = compute_state_hash(current_state)

            logger.debug(f"State hashes - prev: {prev_hash}, curr: {curr_hash}")

            if prev_hash == curr_hash:
                # Identical states - skip expensive LLM comparison
                logger.info("States identical (hash match) - no LLM comparison needed")
                return MonitoringResult(
                    summary="No changes detected since last check.",
                    sources=search_result.get("sources", []),
                    actions=actions + ["compared"],
                    metadata={
                        "changed": False,
                        "current_state": current_state,
                        "schema": schema,
                        "comparison_method": "hash",
                    },
                )

        # Step 4: Semantic comparison (LLM)
        logger.info("Step 4: Performing semantic comparison")
        change = await self.comparison_provider.compare(
            previous_state,
            current_state,
            schema,
        )
        logger.debug(f"Comparison result: {change}")
        actions.append("compared")

        # Step 5: Generate summary
        summary = self._generate_summary(
            search_result=search_result,
            current_state=current_state,
            change=change,
            is_first_execution=(previous_state is None),
        )

        return MonitoringResult(
            summary=summary,
            sources=search_result.get("sources", []),
            actions=actions,
            metadata={
                "changed": change.get("changed", False),
                "current_state": current_state,
                "schema": schema,
                "comparison_method": "semantic",
                "change_explanation": change.get("explanation", ""),
            },
        )

    def _generate_summary(
        self,
        search_result: dict,
        current_state: dict,
        change: dict,
        is_first_execution: bool,
    ) -> str:
        """
        Generate natural language summary for user.

        Combines search answer with change information.
        """
        answer = search_result.get("answer", "")
        changed = change.get("changed", False)
        explanation = change.get("explanation", "")

        if is_first_execution:
            # First execution - just report what we found
            return f"**First Check:** {answer}"

        if not changed:
            # No meaningful change
            return f"**No Changes:** {explanation}\n\n**Latest Info:** {answer}"

        # Something changed - highlight the change
        return f"**What Changed:** {explanation}\n\n**Latest Info:** {answer}"
