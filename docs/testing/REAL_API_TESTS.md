# Real API Tests Guide

This document explains how to run real API tests that call actual services (OpenAI, Anthropic, ElevenLabs, etc.) and incur costs.

## ⚠️ Important Warnings

- **Real API tests cost money!** Each test run may cost $0.01 to $5.00 depending on which tests you run.
- These tests are gated behind the `@pytest.mark.real_api` marker and are **NOT** run in CI.
- Always check your API usage and billing before running extensive real API tests.

## Prerequisites

### 1. API Keys

You need to set up environment variables for the services you want to test:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export ELEVENLABS_API_KEY="..."
```

Alternatively, create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
```

### 2. Install Dependencies

Make sure you have all dev dependencies installed:

```bash
pip install -e ".[dev]"
```

## Running Real API Tests

### Run All Real API Tests

```bash
pytest -m real_api
```

**Expected cost**: $1-10 depending on how many tests exist.

### Run Specific Real API Test

```bash
# Test only OpenAI ideation
pytest tests/real_api/test_llm_real.py::test_openai_ideation_real -v

# Test only ElevenLabs TTS
pytest tests/real_api/test_tts_real.py::test_elevenlabs_tts_real -v
```

### Run with Cost Tracking

Cost tracking is built into all real API tests. After each test session, you'll see:

```
💰 API COST SUMMARY
============================================================
Total Cost: $0.1234
Total Calls: 5
Budget Limit: $10.00
Remaining Budget: $9.88
Status: ✓ Within Budget

Breakdown by Service:
  openai: $0.0850 (3 calls)
  elevenlabs: $0.0384 (2 calls)
============================================================
```

## Budget Management

### Default Budget

The default budget limit is **$10.00** per test session.

### Custom Budget

You can set a custom budget limit by modifying the fixture in your test file:

```python
@pytest.fixture
def cost_tracker():
    tracker = CostTracker()
    tracker.set_budget_limit(5.0)  # Set to $5.00
    yield tracker
    # ... rest of fixture
```

### Budget Enforcement

If tests exceed the budget limit, the test session will **fail** with an error message:

```
FAILED: Test suite exceeded budget: $10.50 > $10.00
```

## Test Categories and Costs

| Test Category | Approx. Cost | Speed | Description |
|--------------|--------------|-------|-------------|
| `test_*_ideation_real` | $0.01-0.05 | Fast | LLM topic refinement |
| `test_*_scripting_real` | $0.05-0.15 | Medium | Full script generation |
| `test_*_tts_real` | $0.10-0.30 | Medium | Speech synthesis |
| `test_full_pipeline_real` | $1.00-5.00 | Slow | Complete episode production |

## Best Practices

### 1. Run Mock Tests First

Always run mock tests before real API tests to catch bugs:

```bash
# Run all tests except real_api
pytest -m "not real_api"
```

### 2. Use Real API Tests Sparingly

Only run real API tests when:
- You need to verify actual API integration
- You're testing new API features
- Mock tests pass but you suspect API behavior differences

### 3. Monitor Costs

Keep track of your API costs:

```bash
# Run with verbose cost tracking
pytest -m real_api -v --tb=short
```

### 4. Skip Expensive Tests

Use `@pytest.mark.slow` on expensive tests and skip them during development:

```bash
# Skip slow tests
pytest -m "real_api and not slow"
```

## Troubleshooting

### Missing API Keys

```
Error: OPENAI_API_KEY environment variable not set
```

**Solution**: Set the required environment variable or add it to `.env`.

### Rate Limiting

```
Error: Rate limit exceeded (429)
```

**Solution**: Wait a few minutes and try again, or reduce the number of concurrent tests.

### Budget Exceeded

```
FAILED: Test suite exceeded budget: $10.50 > $10.00
```

**Solution**: This is expected behavior. Review which tests are expensive and run fewer tests, or increase the budget limit if justified.

## Cost Tracking Details

The `CostTracker` class automatically:
- Records every API call with timestamp and cost
- Calculates running totals by service
- Warns when approaching budget limit
- Fails the test session if budget is exceeded
- Prints detailed cost breakdown after tests

Example output:

```python
{
  "total_cost_usd": 0.1234,
  "total_calls": 5,
  "by_service": {
    "openai": {
      "cost_usd": 0.0850,
      "call_count": 3
    },
    "elevenlabs": {
      "cost_usd": 0.0384,
      "call_count": 2
    }
  },
  "within_budget": true,
  "remaining_budget_usd": 9.88
}
```

## CI/CD Integration

Real API tests are **NOT** run in CI to avoid costs and secret management issues.

The CI workflow explicitly excludes them:

```yaml
- name: Run tests (mock only)
  run: pytest -m "not real_api" --cov=src
```

If you need to run real API tests in CI:
1. Add secrets to your GitHub repository settings
2. Create a separate workflow that runs only on-demand
3. Set a strict budget limit
4. Monitor costs closely

## Questions?

If you have questions about real API testing:
1. Check the cost tracking output for detailed breakdown
2. Review individual test files for expected costs
3. Consult the API provider's pricing documentation
4. Ask the team before running expensive test suites
