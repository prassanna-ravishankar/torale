"""Provider factory for dynamic provider selection based on configuration."""

from torale.providers.comparison_provider import ComparisonProvider
from torale.providers.extraction_provider import ExtractionProvider
from torale.providers.schema_provider import SchemaProvider
from torale.providers.search_provider import SearchProvider


class ProviderFactory:
    """Factory for creating provider instances based on configuration."""

    _PROVIDER_REGISTRY = {
        "gemini": {
            "schema": "torale.providers.gemini.GeminiSchemaProvider",
            "extraction": "torale.providers.gemini.GeminiExtractionProvider",
            "comparison": "torale.providers.gemini.GeminiComparisonProvider",
            "search": "torale.providers.gemini.GeminiSearchProvider",
        },
        # Future providers can be added here:
        # "openai": {
        #     "schema": "torale.providers.openai.OpenAISchemaProvider",
        #     "extraction": "torale.providers.openai.OpenAIExtractionProvider",
        #     "comparison": "torale.providers.openai.OpenAIComparisonProvider",
        #     "search": "torale.providers.openai.OpenAISearchProvider",
        # },
    }

    @classmethod
    def create_schema_provider(cls, provider_type: str = "gemini") -> SchemaProvider:
        """Create a schema provider based on configuration."""
        return cls._create_provider(provider_type, "schema")

    @classmethod
    def create_extraction_provider(cls, provider_type: str = "gemini") -> ExtractionProvider:
        """Create an extraction provider based on configuration."""
        return cls._create_provider(provider_type, "extraction")

    @classmethod
    def create_comparison_provider(cls, provider_type: str = "gemini") -> ComparisonProvider:
        """Create a comparison provider based on configuration."""
        return cls._create_provider(provider_type, "comparison")

    @classmethod
    def create_search_provider(cls, provider_type: str = "gemini") -> SearchProvider:
        """Create a search provider based on configuration."""
        return cls._create_provider(provider_type, "search")

    @classmethod
    def _create_provider(cls, provider_type: str, provider_role: str):
        """Internal method to dynamically import and instantiate provider."""
        if provider_type not in cls._PROVIDER_REGISTRY:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Available: {list(cls._PROVIDER_REGISTRY.keys())}"
            )

        provider_class_path = cls._PROVIDER_REGISTRY[provider_type][provider_role]
        module_path, class_name = provider_class_path.rsplit(".", 1)

        # Dynamic import
        import importlib

        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)

        return provider_class()
