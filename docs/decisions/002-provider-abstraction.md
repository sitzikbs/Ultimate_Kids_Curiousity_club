# ADR 002: Provider Abstraction Pattern

**Status**: ✅ Accepted  
**Date**: 2024-01-15  
**Deciders**: Team  
**Tags**: architecture, design-patterns, extensibility

## Context

The podcast generator integrates with multiple external AI services:
- **LLM Providers**: OpenAI (GPT-4), Anthropic (Claude), future alternatives
- **TTS Providers**: ElevenLabs, Google Cloud TTS, OpenAI TTS
- **Image Providers**: Flux, DALL-E, Imagen (future)

Each provider has:
- Different API interfaces and SDKs
- Different authentication mechanisms
- Different response formats
- Different pricing models
- Different rate limits and error handling

We need a design that:
1. **Decouples business logic** from provider-specific implementation
2. **Enables easy switching** between providers without code changes
3. **Supports multiple providers** simultaneously (e.g., OpenAI for ideation, Anthropic for scripting)
4. **Facilitates testing** with mock implementations
5. **Allows adding new providers** without modifying existing code

## Decision

We will implement the **Abstract Factory Pattern** with **Strategy Pattern** for provider management:

### 1. Base Provider Interfaces
Define abstract base classes for each service type:

```python
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate text from LLM."""
        pass
    
    @abstractmethod
    def get_cost(self, tokens_used: dict[str, int]) -> float:
        """Calculate cost for token usage."""
        pass

class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs
    ) -> dict[str, Any]:
        """Synthesize speech from text."""
        pass
    
    @abstractmethod
    def list_voices(self) -> list[dict[str, Any]]:
        """List available voices."""
        pass
    
    @abstractmethod
    def get_cost(self, characters: int) -> float:
        """Calculate cost for character count."""
        pass
```

### 2. Concrete Provider Implementations
Each provider implements the base interface:
- `OpenAIProvider(BaseLLMProvider)`
- `AnthropicProvider(BaseLLMProvider)`
- `MockLLMProvider(BaseLLMProvider)`
- `ElevenLabsProvider(BaseTTSProvider)`
- `GoogleTTSProvider(BaseTTSProvider)`
- etc.

### 3. Factory Classes
Factories instantiate providers based on configuration:

```python
class LLMProviderFactory:
    @staticmethod
    def create(settings: Settings) -> BaseLLMProvider:
        if settings.USE_MOCK_SERVICES:
            return MockLLMProvider()
        
        if settings.LLM_PROVIDER == "openai":
            return OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )
        elif settings.LLM_PROVIDER == "anthropic":
            return AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_MODEL
            )
        else:
            raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
```

### 4. Dependency Injection
Services receive providers via constructor injection:

```python
class ScriptingService:
    def __init__(self, llm_provider: BaseLLMProvider, prompt_enhancer: PromptEnhancer):
        self.llm = llm_provider
        self.enhancer = prompt_enhancer
    
    def generate_script(self, ideation: IdeationOutput, characters: list[Character]) -> Script:
        # Business logic uses abstract interface, not specific provider
        prompt = self.enhancer.enhance_prompt(...)
        response = self.llm.generate(prompt)
        return self._parse_script(response)
```

### 5. Configuration-Driven Selection
Provider selection controlled via settings:

```bash
# .env
USE_MOCK_SERVICES=false
LLM_PROVIDER=openai      # or anthropic
TTS_PROVIDER=elevenlabs  # or google, openai
IMAGE_PROVIDER=flux      # or dalle
```

## Consequences

### Positive
1. **Loose Coupling**: Business logic independent of provider implementation
2. **Easy Switching**: Change provider via configuration, no code changes
3. **Testability**: Inject mock providers for testing
4. **Extensibility**: Add new providers by implementing interface
5. **Provider Comparison**: Easy to benchmark providers side-by-side
6. **Cost Optimization**: Switch to cheaper providers without refactoring

### Negative
1. **Abstraction Overhead**: Lowest common denominator API (can't use provider-specific features)
2. **Boilerplate**: Each provider requires wrapper implementation
3. **Interface Stability**: Changes to base interface affect all providers

### Mitigations
- **For Abstraction Overhead**: Use `**kwargs` for provider-specific parameters
- **For Boilerplate**: Templates and code generation for new providers
- **For Interface Stability**: Careful interface design, use semantic versioning

## Alternatives Considered

### Alternative 1: Direct Provider Integration
**Rejected because**:
- Tight coupling to specific provider APIs
- Difficult to switch providers
- Hard to test without real API calls
- Vendor lock-in risk

### Alternative 2: Adapter Pattern Only
**Rejected because**:
- Still requires manual instantiation
- No centralized configuration
- Harder to manage multiple providers

### Alternative 3: Plugin System
**Rejected because**:
- Over-engineered for current needs
- Complex to implement and maintain
- Not needed for known set of providers

## Implementation Guidelines

### Adding a New Provider
1. Create class implementing base interface:
   ```python
   class NewLLMProvider(BaseLLMProvider):
       def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
           # Implementation
           pass
   ```

2. Add factory case:
   ```python
   elif settings.LLM_PROVIDER == "new_provider":
       return NewLLMProvider(api_key=settings.NEW_PROVIDER_API_KEY)
   ```

3. Update settings schema:
   ```python
   LLM_PROVIDER: str = "openai"  # openai, anthropic, new_provider
   NEW_PROVIDER_API_KEY: str | None = None
   ```

4. Add tests:
   ```python
   def test_new_provider():
       provider = NewLLMProvider(api_key="test")
       result = provider.generate("test prompt")
       assert result["content"]
   ```

### Provider Interface Design Principles
1. **Return Normalized Structures**: All providers return same dict structure
2. **Include Metadata**: Always include cost, model, timing information
3. **Raise Standard Exceptions**: Use custom exceptions (APIError, ValidationError)
4. **Support Retry Logic**: Providers should handle transient failures
5. **Log Consistently**: Use structured logging for debugging

### Example Provider Response Format
```python
{
    "content": "Generated text or data",
    "metadata": {
        "model": "gpt-4",
        "tokens": {"input": 150, "output": 200},
        "duration_ms": 1234,
        "provider": "openai"
    },
    "cost": 0.015
}
```

## References

- [Abstract Factory Pattern](https://refactoring.guru/design-patterns/abstract-factory)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Dependency Injection](https://martinfowler.com/articles/injection.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
