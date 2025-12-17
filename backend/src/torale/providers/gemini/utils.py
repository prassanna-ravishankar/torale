"""Shared utilities for Gemini providers."""


def format_schema_for_prompt(schema: dict) -> str:
    """
    Format schema as human-readable text for LLM prompt.

    Converts structured schema dict into a readable list format for Gemini prompts.

    Args:
        schema: Dict mapping field names to field specs (type, description)

    Returns:
        Formatted schema string for prompt inclusion
    """
    lines = []
    for field_name, field_spec in schema.items():
        field_type = field_spec.get("type", "string")
        field_desc = field_spec.get("description", "")
        lines.append(f"- {field_name} ({field_type}): {field_desc}")

    return "\n".join(lines)
