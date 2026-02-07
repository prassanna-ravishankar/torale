"""Prompt sanitization utilities to prevent injection attacks."""


class PromptSanitizer:
    """Wraps untrusted user input in XML-style tags to prevent prompt injection.

    Follows the existing pattern established by format_execution_history() which
    uses <execution-history> tags with explicit data-only labeling.
    """

    @staticmethod
    def wrap(tag: str, content: str, note: str | None = None) -> str:
        """Wrap untrusted content in XML-style safety tags.

        Args:
            tag: Tag name (e.g., "user-task", "user-context")
            content: Untrusted user input to wrap
            note: Optional instruction to the LLM about treating this as data

        Returns:
            Formatted string with content wrapped in tags

        Example:
            >>> PromptSanitizer.wrap("user-task", "iPhone release date")
            '<user-task>\\niPhone release date\\n</user-task>'
        """
        lines = [f"<{tag}>"]

        if note:
            lines.append(note)

        lines.append(content)
        lines.append(f"</{tag}>")

        return "\n".join(lines)
