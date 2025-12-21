# Ultimate Kids Curiosity Club 🎓

A Python-based educational platform designed to inspire curiosity and learning in kids through interactive projects, experiments, and educational content.

## 🚀 Features

- Interactive learning modules
- Science experiments and demonstrations
- Educational games and quizzes
- Progress tracking and achievements

## 🛠️ Development Setup

This project uses [uv](https://github.com/astral-sh/uv) for Python dependency management.

### Prerequisites

- Python 3.12 or higher
- uv (fast Python package installer)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Ultimate_Kids_Curiousity_club
   ```

2. Create and activate the virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

### Running the Application

```bash
python main.py
```

Or run from the src directory:
```bash
python -m src.main
```

## 📁 Project Structure

```
Ultimate_Kids_Curiousity_club/
├── src/                    # Main source code
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── modules/           # Feature modules
│   ├── utils/             # Utility functions
│   └── data/              # Data files and resources
├── tests/                 # Test suite
├── docs/                  # Documentation
├── pyproject.toml         # Project metadata and dependencies
├── README.md              # This file
└── .gitignore            # Git ignore patterns

```

## 🧪 Testing

Run tests using pytest:
```bash
uv pip install pytest
pytest
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🌟 Acknowledgments

Built with ❤️ to inspire the next generation of learners and innovators.