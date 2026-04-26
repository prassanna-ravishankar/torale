"""Supported toolkits + their Composio resource IDs.

Populated by `scratch/composio_seed.py`. One entry per supported connector.
The seed script is idempotent, so re-running after adding a toolkit is safe.

SYNC: Keep allowed_tools in sync with whatever is configured in the Composio
dashboard or via the seed script. The registry here is authoritative for
what Torale exposes; Composio's allowlist is what the agent actually sees.
"""

from pydantic import BaseModel, Field


class Toolkit(BaseModel):
    """One supported connector toolkit."""

    slug: str = Field(description="Composio toolkit slug, e.g. 'notion'")
    display_name: str = Field(description="User-facing name shown in UI")
    description: str = Field(description="One-sentence description for UI cards")
    auth_config_id: str = Field(description="Composio auth config ID (ac_xxx)")
    mcp_server_id: str = Field(description="Composio MCP server config UUID")
    allowed_tools: list[str] = Field(
        description="Tool slugs exposed to the agent (must match Composio config)",
    )


# Populated from the seed script output (`scratch/composio_seed.py`). Per-env:
# rerun the seed script against each Composio project (dev/staging/prod) and
# paste the output here, OR load from an env-specific JSON file at startup.
# For v1 we hardcode dev values; revisit before first staging deploy.
TOOLKIT_REGISTRY: list[Toolkit] = [
    Toolkit(
        slug="notion",
        display_name="Notion",
        description="Lets the agent read pages and databases in your Notion workspace.",
        auth_config_id="ac_aVNdb5ddTSeA",
        mcp_server_id="75ecf389-87f9-4144-b30d-a0da5e1d9859",
        allowed_tools=[
            "NOTION_SEARCH_NOTION_PAGE",
            "NOTION_FETCH_DATA",
        ],
    ),
    Toolkit(
        slug="linear",
        display_name="Linear",
        description="Lets the agent read issues, projects, and cycles from Linear.",
        auth_config_id="ac_C7CBThcBOWDZ",
        mcp_server_id="d894d6f0-fddb-49fa-8a9c-5c50562981c4",
        allowed_tools=[
            "LINEAR_GET_ALL_LINEAR_TEAMS",
            "LINEAR_GET_CYCLES_BY_TEAM_ID",
            "LINEAR_GET_CURRENT_USER",
        ],
    ),
    Toolkit(
        slug="github",
        display_name="GitHub",
        description="Lets the agent read issues, PRs, and repository metadata from GitHub.",
        auth_config_id="ac_zQFL3t2n4nGx",
        mcp_server_id="429a6a2a-af16-4774-bebe-7e4e1d4d7f57",
        allowed_tools=[
            "GITHUB_SEARCH_ISSUES_AND_PULL_REQUESTS",
            "GITHUB_LIST_REPOSITORY_ISSUES",
            "GITHUB_GET_A_PULL_REQUEST",
        ],
    ),
]


def get_toolkit(slug: str) -> Toolkit | None:
    """Look up a registered toolkit by slug."""
    for tk in TOOLKIT_REGISTRY:
        if tk.slug == slug:
            return tk
    return None
