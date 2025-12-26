# Ultimate Kids Curiosity Club

An educational platform designed to inspire curiosity and learning in kids.

## Installation

### Requirements
- Python 3.12 or higher
- pip package manager

### Setup

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/sitzikbs/Ultimate_Kids_Curiousity_club.git
   cd Ultimate_Kids_Curiousity_club
   ```

2. **Install the package with all dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```
   
   This will:
   - Install the package in editable mode
   - Install Pydantic for data models
   - Install pytest for testing
   - Install ruff for linting

   **Note:** The `-e` flag installs in "editable" mode, which means changes to the source code are immediately reflected without reinstalling.

### Troubleshooting

If you encounter import errors:

1. Make sure you've installed the package:
   ```bash
   pip install -e ".[dev]"
   ```

2. Verify the installation:
   ```bash
   pip show ultimate-kids-curiousity-club
   ```

3. If using a virtual environment, make sure it's activated before installing and running tests.

## Running Tests

After installing the development dependencies, run tests using pytest:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_models.py::TestShowModels::test_show_creation
```

**Note:** Do not run test files directly with `python tests/test_models.py`. Test files are designed to be executed through pytest.

## Linting

Run the linter to check code style:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

## Project Structure

```
src/
├── models/
│   ├── __init__.py
│   ├── show.py           # Show Blueprint models
│   ├── episode.py        # Episode and Pipeline models
│   └── story.py          # Story generation models
├── modules/
│   └── prompts/          # Prompt Enhancement Service (WP0)
│       ├── enhancer.py   # PromptEnhancer class
│       ├── filters.py    # Custom Jinja2 filters
│       ├── templates/    # Jinja2 prompt templates
│       └── README.md     # Module documentation
├── utils/
└── main.py

tests/
├── test_basic.py
├── test_models.py        # Model tests
└── unit/
    ├── test_prompt_enhancer.py  # Prompt enhancer tests
    └── test_prompt_filters.py   # Filter tests

examples/
└── prompt_enhancer_demo.py      # Working demo
```

## Example Usage

After installing the package, you can use the models and prompt enhancement:

### Using Data Models

```python
from models import Show, Episode, PipelineStage, ShowBlueprint

show = Show(
    show_id='science_club',
    title='Science Adventure Club',
    theme='STEM and Discovery',
    narrator_voice_config={'provider': 'elevenlabs', 'voice_id': 'narrator_01'},
    description='Educational science for curious kids'
)

episode = Episode(
    episode_id='ep001_gravity',
    show_id='science_club',
    topic='How gravity works',
    title='The Force That Pulls Us Down',
    current_stage=PipelineStage.PENDING
)

# Serialize for storage
data = episode.model_dump()

# Stage transitions
episode.current_stage = PipelineStage.IDEATION
episode.current_stage = PipelineStage.OUTLINING
```

### Using Prompt Enhancement Service

```python
from modules.prompts import PromptEnhancer
from models import ShowBlueprint

# Create a show blueprint with protagonist, world, etc.
show_blueprint = ShowBlueprint(...)

# Initialize the enhancer
enhancer = PromptEnhancer(version="1.0.0")

# Enhance prompts for each generation stage
ideation_prompt = enhancer.enhance_ideation_prompt(
    topic="How do plants make food?",
    show_blueprint=show_blueprint
)

# Run the demo
# python examples/prompt_enhancer_demo.py
```

For more details on the Prompt Enhancement Service, see:
- `src/modules/prompts/README.md` - Full module documentation
- `examples/prompt_enhancer_demo.py` - Working demonstration
