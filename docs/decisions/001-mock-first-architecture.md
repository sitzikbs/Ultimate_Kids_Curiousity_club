# ADR 001: Mock-First Development Architecture

**Status**: ✅ Accepted  
**Date**: 2024-01-15  
**Deciders**: Team  
**Tags**: architecture, testing, cost-optimization

## Context

Building an AI-powered podcast generator requires integration with multiple expensive external APIs:
- **LLM APIs** (OpenAI, Anthropic): $0.01-0.06 per 1K tokens
- **TTS APIs** (ElevenLabs): $0.30 per 1K characters
- **Image APIs** (Flux, DALL-E): $0.04-0.08 per image

During development and testing, repeatedly calling these APIs would:
1. **Accumulate significant costs**: $50-200 for comprehensive testing
2. **Slow down development**: 5-30 second API calls for each test
3. **Create CI/CD complexity**: Need to manage API keys and budgets in CI
4. **Limit iteration speed**: Expensive to test changes

We need a development strategy that:
- Enables rapid iteration without API costs
- Maintains realistic testing behavior
- Supports easy switching to real APIs
- Preserves test coverage

## Decision

We will implement a **mock-first architecture** with the following components:

### 1. Provider Abstraction Layer
All external services accessed through abstract base classes:
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, ...) -> dict[str, Any]: pass

class BaseTTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, ...) -> dict[str, Any]: pass

class BaseImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, ...) -> Image: pass
```

### 2. Mock Provider Implementations
Mock providers return realistic fixture data:
- `MockLLMProvider`: Returns pre-generated JSON responses
- `MockTTSProvider`: Generates silent MP3 files with correct duration
- `MockImageProvider`: Returns placeholder images

### 3. Factory Pattern
Providers instantiated via factories based on settings:
```python
def create_llm_provider(settings: Settings) -> BaseLLMProvider:
    if settings.USE_MOCK_SERVICES:
        return MockLLMProvider()
    elif settings.LLM_PROVIDER == "openai":
        return OpenAIProvider(settings.OPENAI_API_KEY)
    elif settings.LLM_PROVIDER == "anthropic":
        return AnthropicProvider(settings.ANTHROPIC_API_KEY)
```

### 4. Global Mock Toggle
Single environment variable controls all mocking:
```bash
USE_MOCK_SERVICES=true  # Default for development
USE_MOCK_SERVICES=false # For production or real API testing
```

### 5. Realistic Mock Fixtures
Fixtures generated from real API responses during initial development:
- Store in `data/fixtures/llm/`, `data/fixtures/audio/`
- Include full response structure (content, metadata, token counts)
- Maintain realistic timings (artificial delays in mocks)

### 6. Gated Real API Tests
Real API tests marked with `@pytest.mark.real_api`:
- Not run in CI by default
- Require explicit opt-in: `pytest -m real_api`
- Track and report costs
- Budget threshold: Fail if cost > $10

## Consequences

### Positive
1. **Cost Savings**: ~$200 saved during development (100% mock tests are free)
2. **Fast Iteration**: Mock tests complete in <10 seconds vs 2-5 minutes for real APIs
3. **Deterministic Tests**: No flaky tests from API rate limits or transient failures
4. **Offline Development**: Work without internet or API keys
5. **Easy Onboarding**: New developers can start immediately without API setup
6. **CI/CD Simplicity**: No need to manage API keys or budgets in CI

### Negative
1. **Mock Maintenance**: Must update fixtures if API responses change
2. **Realism Gap**: Mocks may not catch all edge cases
3. **Initial Effort**: Requires building mock implementations
4. **Two Code Paths**: Must test both mock and real providers

### Mitigations
- **For Mock Maintenance**: Use real API responses as fixtures (copy-paste actual output)
- **For Realism Gap**: Require periodic real API integration tests (weekly)
- **For Initial Effort**: Amortized across project (pays off after first week)
- **For Two Code Paths**: Provider abstraction ensures identical interfaces

## Alternatives Considered

### Alternative 1: Real APIs Only
**Rejected because**:
- Cost: $50-200 for comprehensive testing
- Speed: 2-5 minutes per full test run
- CI/CD: Complex API key management

### Alternative 2: VCR/Record-Replay (pytest-vcr)
**Rejected because**:
- Still requires initial real API calls (cost)
- Cassettes become stale quickly
- Harder to customize test scenarios
- More complex debugging

### Alternative 3: Sandbox APIs
**Rejected because**:
- Not all providers offer sandboxes
- Sandbox behavior may differ from production
- Still requires API key management

### Alternative 4: API Call Budgets Only
**Rejected because**:
- Still incurs costs
- Doesn't address speed issues
- Complicates CI/CD

## Implementation Notes

### Mock Provider Example
```python
class MockLLMProvider(BaseLLMProvider):
    def __init__(self):
        self.fixtures_dir = Path("data/fixtures/llm")
    
    def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
        # Load fixture based on prompt keywords
        if "space" in prompt.lower():
            fixture = self.fixtures_dir / "ideation_space.json"
        else:
            fixture = self.fixtures_dir / "ideation_generic.json"
        
        return json.loads(fixture.read_text())
```

### Fixture Generation Workflow
1. Generate episode with real APIs (one-time cost: $5-10)
2. Capture all API responses and save as JSON
3. Use captured responses as fixtures for all future tests
4. Update fixtures only when API contracts change

## References

- [Test Doubles (Martin Fowler)](https://martinfowler.com/bliki/TestDouble.html)
- [Mock First Development](https://www.infoq.com/articles/mock-first-development/)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
