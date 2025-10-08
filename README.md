# 🎨 3D Asset Generator - AI-Powered Blender Automation

A comprehensive web application with multi-agent system for generating 3D assets from natural language prompts using Blender automation, intelligent planning, and automated script generation.

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

1. Install uv (if not already installed):
```bash
# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Clone and install dependencies:
```bash
git clone <repository-url>
cd capstone
uv sync --extra web --extra mcp --extra vector
```

3. For development with all extras:
```bash
uv sync --extra dev --extra web --extra mcp --extra vector
```

## Quick Start

### 🚀 **Local Mode (Recommended for Development)**

**Prerequisites:**
- Blender installed on your system
- Python 3.11+
- Gemini API key

**Setup:**

1. **Configure environment:**
```bash
# Create .env file
echo "EXECUTION_MODE=local" > .env
echo "GEMINI_API_KEY=your_api_key_here" >> .env
```

2. **Update Blender path** in `blender_executor.py`:
```python
BLENDER_EXECUTABLE = r"D:\blender.exe"  # Update to your Blender path
```

3. **Start the backend:**
```bash
# Activate virtual environment
.\capstone_venc\Scripts\Activate.ps1  # Windows
source capstone_venc/bin/activate     # Linux/Mac

# Start server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

4. **Open frontend:**
```bash
# Open in browser
file:///path/to/capstone/front_end/index.html
```

5. **Generate assets!** 🎨
- Enter a prompt like "Create a red cricket ball"
- Watch the backend logs for detailed execution steps
- Download and view your 3D asset

**How it works:**
- Backend generates Python script from your prompt
- Automatically starts Blender in headless mode
- Executes script and exports GLB
- Returns model for download - all automatically!

### 🐳 **Docker Mode (Production)**

```bash
# Set environment
echo "EXECUTION_MODE=docker" > .env

# Start with Docker Compose
docker-compose up --build

# Access the web interface
open http://localhost:3000
```

### 🌐 **AWS Deployment**

```bash
# Deploy to AWS
cd aws
./deploy.sh your-domain.com

# Access via your domain or ALB DNS
```

See `docs/DEPLOYMENT.md` for detailed AWS setup instructions.

## Usage

### Web Interface
1. **Open** http://localhost:3000 in your browser
2. **Enter** a description like "Create a red cricket ball"
3. **Click** "Generate 3D Asset"
4. **Watch** real-time progress updates
5. **View** the generated 3D model in the browser
6. **Download** the GLB file for use in other applications

### Command Line (Development)

```bash
uv run python test_complete_pipeline.py
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
uv run python blender_api_parser.py
```

Extracts and processes Blender API documentation for the agent system.

## Project Structure

```
capstone/
├── agents/                     # Multi-agent system
│   ├── planner_agent.py        # Task planning and decomposition
│   ├── coordinator_agent.py    # API mapping and coordination
│   ├── coder_agent.py          # Script generation with templating
│   ├── qa_agent.py             # Quality assurance and validation
│   ├── llm_api_mapper.py       # LLM-powered API mapping
│   └── api_search/             # Intelligent API search engine
├── backend/                    # FastAPI backend
│   ├── main.py                 # Main API server
│   └── monitoring.py           # Health checks and metrics
├── front_end/                  # Web interface
│   ├── index.html              # Main UI
│   ├── app.js                  # Frontend logic
│   ├── styles.css              # Styling
│   └── viewer.html             # 3D model viewer
├── config/                     # Configuration files
│   ├── agents_config.yaml      # Agent settings
│   ├── curated_allowlist.json  # Material allowlist
│   └── vector_store_config.yaml
├── docs/                       # Documentation
│   ├── DEPLOYMENT.md           # AWS deployment guide
│   ├── LOCAL_MODE_NEW_APPROACH.md  # Local mode architecture
│   ├── IMPLEMENTATION_SUMMARY.md   # Project summary
│   ├── FRONTEND_VIEWER_ENHANCEMENT.md
│   └── USER_GUIDE_VIEWER.md
├── aws/                        # AWS infrastructure
│   ├── terraform/              # Terraform IaC
│   ├── deploy.sh               # Deployment script
│   └── destroy.sh              # Cleanup script
├── generated_scripts/          # Generated Blender scripts
├── generated_models/           # Exported GLB files
├── blender_executor.py         # Headless Blender execution engine
├── blender_api_registry.json   # Comprehensive API registry (2414 APIs)
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Production container
├── docker-compose.yml          # Multi-container setup
├── .env                        # Environment configuration
└── README.md                   # This file
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

### Run tests:
```bash
uv run pytest
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

## Features

### ✅ **Completed (Milestone 1)**
- [x] **Web Interface**: Modern responsive frontend with 3D model viewer
- [x] **FastAPI Backend**: RESTful API integrating with multi-agent pipeline
- [x] **Headless Blender**: Docker-based Blender execution environment
- [x] **GLB Export**: Automatic 3D model export in web-compatible format
- [x] **Real-time Status**: Live progress updates during generation
- [x] **Download System**: Direct GLB file download functionality

### ✅ **Core Pipeline (Previously Completed)**
- [x] Blender API HTML parser (2000+ APIs)
- [x] Multi-agent architecture implementation
- [x] Natural language → API mapping (LLM-powered)
- [x] Intelligent material and color system
- [x] Script generation with error handling
- [x] Asset validation and QA system

### 🚀 **AWS Deployment Ready**
- [x] **Infrastructure as Code**: Complete Terraform configuration
- [x] **Auto Scaling**: EC2 Auto Scaling Groups with health checks
- [x] **Load Balancing**: Application Load Balancer with SSL support
- [x] **Route 53**: DNS configuration for custom domains
- [x] **Security**: VPC with public/private subnets, security groups

### 🔮 **Future Enhancements**
- [ ] Enhanced object geometry (handles, complex shapes)
- [ ] Lighting and camera positioning
- [ ] Texture mapping and advanced materials
- [ ] Animation support
- [ ] Batch processing
- [ ] User authentication and asset galleries

## Contributing

This is a capstone project focused on dynamic 3D asset generation. The system aims to democratize 3D content creation through natural language interfaces.

## License

MIT License - See LICENSE file for details.
