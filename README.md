# Dynamic 3D Asset Generation Pipeline

A comprehensive multi-agent system for generating 3D assets from natural language prompts using Blender Python API, intelligent planning, and automated script generation.

## Project Overview

This project enables dynamic 3D asset creation through a sophisticated multi-agent pipeline:

1. **Natural Language Processing**: Convert user prompts like "Create a red cricket ball" or "Design a blue coffee mug" into structured task plans and executable Blender scripts.

2. **Multi-Agent Architecture**: Four specialized AI agents work together:
   - **Planner Agent**: Breaks down prompts into structured subtasks
   - **Coordinator Agent**: Maps subtasks to specific Blender API operations
   - **Coder Agent**: Generates complete, executable Blender Python scripts
   - **QA Agent**: Validates script quality and provides feedback

3. **Intelligent API Mapping**: Advanced LLM-powered system maps natural language to valid Blender operations with comprehensive API validation.

4. **Robust Material System**: Automatic color detection, object creation, and material application with crash prevention and error handling.

## Architecture

```
User Prompt → Planner Agent → Coordinator Agent → Coder Agent → QA Agent → Generated Script
     ↓             ↓               ↓                ↓            ↓
Task Planning → API Mapping → Script Generation → Validation → Blender Execution
                     ↓
              Blender API Registry (2000+ APIs)
                     ↓
              LLM-Powered Mapping & Validation
```

## Key Components

### 1. Multi-Agent System (`agents/`)
- **Planner Agent**: Converts natural language to structured task plans with dependency management
- **Coordinator Agent**: Maps subtasks to specific Blender API operations using LLM-powered intelligence
- **Coder Agent**: Generates complete, executable Blender Python scripts with error handling
- **QA Agent**: Validates script quality, checks for issues, and provides improvement suggestions

### 2. Blender API Parser (`blender_api_parser.py`)
- Extracts ~2,000+ API methods from Blender HTML documentation
- Parses method signatures, parameters, types, and descriptions
- Categorizes APIs for intelligent discovery (mesh_ops, material_ops, object_ops, etc.)
- Generates comprehensive API registry for validation and mapping

### 3. Intelligent Material System
- **Automatic Color Detection**: Extracts colors from text ("red ball" → RGBA(1.0, 0.0, 0.0, 1.0))
- **Smart Object Creation**: Maps objects to appropriate Blender primitives (ball → sphere, mug → cylinder)
- **Crash Prevention**: Ensures objects exist before material application
- **Safe Material Application**: Uses validated Blender APIs with proper error handling

### 4. LLM API Mapping (`agents/llm_api_mapper.py`)
- Advanced JSON parsing with multiple fallback mechanisms
- Validates API calls against comprehensive Blender API registry
- Maps invalid operations to valid alternatives
- Handles complex API parameter conversion and validation

## Installation

1. Create and activate virtual environment:
```bash
uv venv
.venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
uv sync
```

3. Install development dependencies:
```bash
uv sync --extra dev
```

## Usage

### Run the 3D Asset Generation Pipeline

```bash
python test_complete_pipeline.py
```

This launches the interactive pipeline where you can:
- Enter natural language prompts (e.g., "Create a red cricket ball")
- Watch the multi-agent system process your request
- Get a complete, executable Blender Python script
- View detailed timing and validation results

### Example Session

```
🎨 Dynamic 3D Asset Generation Pipeline
Enter your 3D asset description below:
🎯 Your prompt: Create a red cricket ball

🚀 Starting Pipeline for: 'Create a red cricket ball'
🧠 Step 1: Planner Agent - Planning subtasks...
🔗 Step 2: Coordinator Agent - Mapping APIs...
💻 Step 3: Coder Agent - Generating script...
🔍 Step 4: QA Agent - Validating quality...

✅ Generated script saved to: generated_script.py
📊 Pipeline Summary:
   ├─ Subtasks planned: 2
   ├─ API calls mapped: 3
   ├─ Script lines generated: 301
   └─ Overall success: ✅ YES
```

### Parse Blender API Documentation (Development)

```bash
python blender_api_parser.py
```

Extracts and processes Blender API documentation for the agent system.

## Project Structure

```
capstone/
├── agents/                     # Multi-agent system
│   ├── __init__.py            # Agent exports and models
│   ├── base_agent.py          # Base agent class
│   ├── planner_agent.py       # Task planning and decomposition
│   ├── coordinator_agent.py   # API mapping and coordination
│   ├── coder_agent.py         # Script generation
│   ├── qa_agent.py            # Quality assurance
│   └── llm_api_mapper.py      # LLM-powered API mapping
├── prompts/                   # LLM prompts and templates
│   ├── api_mapper_prompts.py  # API mapping prompts
│   └── __init__.py
├── vector_store/              # Vector storage for API search
│   ├── faiss_store.py         # FAISS-based vector store
│   └── base.py                # Base vector store interface
├── config/                    # Configuration files
│   ├── agents_config.yaml     # Agent configuration
│   └── vector_store_config.yaml # Vector store settings
├── test_complete_pipeline.py  # Main entry point
├── blender_api_parser.py      # API extraction script
├── blender_api_registry.json  # Generated API registry (2000+ APIs)
├── generated_script.py        # Latest generated Blender script
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## Development

### Code Quality
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing framework

### Run formatting:
```bash
uv run black .
uv run isort .
```

### Run type checking:
```bash
uv run mypy blender_api_parser.py
```

## Recent Achievements

✅ **Multi-Agent Pipeline Complete** (January 2025)
- Four specialized AI agents working in harmony
- End-to-end natural language to Blender script generation
- Robust error handling and validation systems

✅ **Intelligent Material System** (January 2025)
- Automatic color detection from natural language
- Smart object type mapping (ball→sphere, mug→cylinder)
- Crash prevention with proper execution order
- Successfully generates colored 3D assets (red cricket ball, etc.)

✅ **Advanced API Mapping** (January 2025)
- LLM-powered API validation against 2000+ Blender APIs
- Multiple JSON parsing fallback mechanisms
- Comprehensive API registry integration
- Invalid operation replacement with valid alternatives

## Roadmap

- [x] Blender API HTML parser
- [x] API registry generation (2000+ APIs)
- [x] Multi-agent architecture implementation
- [x] Natural language → API mapping (LLM-powered)
- [x] Intelligent material and color system
- [x] Script generation with error handling
- [x] Asset validation and QA system
- [ ] Enhanced object geometry (handles, complex shapes)
- [ ] Lighting and camera positioning
- [ ] GLTF export pipeline
- [ ] Headless Blender integration
- [ ] Three.js integration
- [ ] Web frontend interface

## Contributing

This is a capstone project focused on dynamic 3D asset generation. The system aims to democratize 3D content creation through natural language interfaces.

## License

MIT License - See LICENSE file for details.
