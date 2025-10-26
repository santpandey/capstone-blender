# 🎨 3D Asset Generator - AI-Powered Blender Automation

A comprehensive web application with multi-agent system for generating 3D assets from natural language prompts using Blender automation, intelligent planning, and automated script generation.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Blender](https://img.shields.io/badge/Blender-4.0+-orange.svg)](https://www.blender.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Key Components](#key-components)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
- [📦 Installation](#-installation)
  - [Step 1: Clone the Repository](#step-1-clone-the-repository)
  - [Step 2: Set Up Virtual Environment](#step-2-set-up-virtual-environment)
  - [Step 3: Configure Environment Variables](#step-3-configure-environment-variables)
  - [Step 4: Configure Blender Path](#step-4-configure-blender-path)
  - [Step 5: Verify Installation](#step-5-verify-installation)
- [🎯 Running the Application](#-running-the-application)
- [🐛 Troubleshooting](#-troubleshooting)
- [📚 Additional Setup Options](#-additional-setup-options)
  - [Docker Mode](#-docker-mode-production)
  - [AWS Deployment](#-aws-deployment)
- [⚡ Quick Start Summary](#-quick-start-summary)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development](#development)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

---

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

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** ([Download](https://www.python.org/downloads/))
- **Blender 4.0+** ([Download](https://www.blender.org/download/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Gemini API Key** ([Get one free](https://makersuite.google.com/app/apikey))

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/capstone-blender.git
cd capstone-blender
```

### Step 2: Set Up Virtual Environment

You have **two options** for managing dependencies: **uv** (modern, faster) or **pip** (traditional).

<details>
<summary><b>Option A: Using uv (Recommended - Faster & Modern)</b></summary>

#### Install uv

```bash
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Create Virtual Environment and Install Dependencies

```bash
# uv automatically creates a virtual environment and installs dependencies
uv sync --extra web --extra mcp --extra vector

# For development (includes testing and linting tools)
uv sync --extra dev --extra web --extra mcp --extra vector
```

#### Activate Virtual Environment

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux
source .venv/bin/activate
```

</details>

<details>
<summary><b>Option B: Using pip (Traditional Method)</b></summary>

#### Create Virtual Environment

```bash
# Windows PowerShell
python -m venv capstone_venv
.\capstone_venv\Scripts\Activate.ps1

# Linux
python3 -m venv capstone_venv
source capstone_venv/bin/activate
```

#### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# For development (optional)
pip install -r requirements-dev.txt
```

</details>

---

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Windows PowerShell
@"
EXECUTION_MODE=local
GEMINI_API_KEY=your_gemini_api_key_here
BLENDER_PATH=D:\blender.exe
LOG_LEVEL=INFO
"@ | Out-File -FilePath .env -Encoding utf8

# Linux
cat > .env << EOF
EXECUTION_MODE=local
GEMINI_API_KEY=your_gemini_api_key_here
BLENDER_PATH=/usr/local/bin/blender
LOG_LEVEL=INFO
EOF
```

**⚠️ Important:** Replace `your_gemini_api_key_here` with your actual Gemini API key!

---

### Step 4: Configure Blender Path

The application automatically detects Blender based on your OS, but you can override it:

**Option 1: Environment Variable (Recommended)**
- Already set in `.env` file above

**Option 2: Update `blender_executor.py`**
```python
# Windows
BLENDER_EXECUTABLE = r"D:\blender.exe"

# Linux
BLENDER_EXECUTABLE = "/usr/local/bin/blender"

```

**Find your Blender installation:**
```bash
# Windows PowerShell
where blender
# Common location: C:\Program Files\Blender Foundation\Blender 4.0\blender.exe

# Linux
which blender
# Common locations: /usr/bin/blender, /usr/local/bin/blender
```

---

### Step 5: Verify Installation

Test that everything is set up correctly:

```bash
# Check Python version
python --version
# Should output: Python 3.11.x or higher

# Check Blender is accessible
blender --version
# Should output: Blender 4.0.x or higher

# Test the pipeline (optional)
python test_complete_pipeline.py
```

---

## 🎯 Running the Application

### Local Development Mode

#### Start the Backend Server

**Using uv:**
```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Using pip:**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

#### Open the Frontend

**Option 1: Direct File (Simple)**
```bash
# Windows
start front_end/index.html

# Linux
xdg-open front_end/index.html

```

**Option 2: Local Web Server (Better for CORS)**
```bash
# Python 3
python -m http.server 3000

# Then open: http://localhost:3000/front_end/index.html
```

#### Test the Application

1. Open http://localhost:3000/front_end/index.html in your browser
2. Enter a prompt: "Create a red cricket ball"
3. Click "Generate 3D Asset"
4. Watch the progress in real-time
5. View and download your 3D model!

---

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><b>❌ "Blender executable not found"</b></summary>

**Solution:**
1. Verify Blender is installed: `blender --version`
2. Update `BLENDER_PATH` in `.env` file
3. Or update `BLENDER_EXECUTABLE` in `blender_executor.py`

</details>

<details>
<summary><b>❌ "ModuleNotFoundError: No module named 'fastapi'"</b></summary>

**Solution:**
```bash
# Using uv
uv sync --extra web

# Using pip
pip install -r requirements.txt
```

</details>

<details>
<summary><b>❌ "GEMINI_API_KEY not found"</b></summary>

**Solution:**
1. Create `.env` file in project root
2. Add: `GEMINI_API_KEY=your_key_here`
3. Get API key from: https://makersuite.google.com/app/apikey

</details>

<details>
<summary><b>❌ "Port 8000 already in use"</b></summary>

**Solution:**
```bash
# Use a different port
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# Or kill the existing process
# Windows: taskkill /F /IM python.exe
# Linux: lsof -ti:8000 | xargs kill -9
```

</details>

<details>
<summary><b>❌ Frontend can't connect to backend</b></summary>

**Solution:**
1. Verify backend is running: http://localhost:8000/health
2. Check `API_URL` in `front_end/app.js`:
   ```javascript
   const API_URL = 'http://localhost:8000';
   ```
3. Open browser console (F12) for error details

</details>

---

## 📚 Additional Setup Options

### 🐳 Docker Mode (Production)

**Prerequisites:**
- Docker installed ([Download](https://www.docker.com/get-started))
- Docker Compose installed (included with Docker Desktop)

**Setup:**

1. **Create .env file:**
```bash
cat > .env << EOF
EXECUTION_MODE=docker
GEMINI_API_KEY=your_gemini_api_key_here
BLENDER_DOCKER=true
EOF
```

2. **Build and start containers:**
```bash
docker-compose up --build
```

3. **Access the application:**
```
http://localhost:3000
```

4. **Stop containers:**
```bash
docker-compose down
```

**Container Architecture:**
- **Backend**: FastAPI server with all agents
- **Blender**: Headless Blender in isolated container
- **Frontend**: Static web interface

---

### 🌐 AWS EC2 Deployment

**Complete step-by-step guide for deploying on Amazon Linux EC2:**

#### Prerequisites
- AWS EC2 instance (Amazon Linux 2 or newer)
- Security group with ports 22 (SSH), 80 (HTTP), 3000 (Frontend), 8000 (API) open
- At least 4GB RAM and 20GB storage recommended

#### Step 1: Initial System Setup
```bash
# Update system packages
sudo yum update -y

# Install Git
sudo yum install git -y

# Clone the repository
git clone https://github.com/santpandey/capstone-blender.git
cd capstone-blender/
```

#### Step 2: Python Environment Setup
```bash
# Install Python 3.12 and development tools
sudo yum groupinstall "Development Tools" -y
sudo yum install -y python3-devel libxml2-devel libxslt-devel zlib-devel

# Install pip and uv (Python package manager)
sudo yum install pip3 -y
pip install uv

# Set up virtual environment and install dependencies
uv sync
source .venv/bin/activate
```

#### Step 3: Blender Installation
```bash
# Enable EPEL repository for additional packages
sudo amazon-linux-extras enable epel
sudo yum install epel-release -y

# Install Blender dependencies
sudo yum install mesa-libGLU-devel mesa-libGL-devel libXi-devel libXrender-devel bzip2 bzip2-devel -y

# Download and install Blender
wget https://download.blender.org/release/Blender3.6/blender-3.6.1-linux-x64.tar.xz
tar -xf blender-3.6.1-linux-x64.tar.xz
sudo mv blender-3.6.1-linux-x64 /opt/blender

# Add Blender to PATH
echo 'export PATH=/opt/blender:$PATH' >> ~/.bashrc
source ~/.bashrc

# Verify Blender installation
blender --version
```

#### Step 4: Environment Configuration
```bash
# Create .env file with your API keys
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
BLENDER_EXECUTABLE_PATH=/opt/blender/blender
EOF
```

#### Step 5: Systemd Service Setup
```bash
# Create backend service
sudo tee /etc/systemd/system/capstone-backend.service > /dev/null << EOF
[Unit]
Description=Capstone Blender Backend API
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/capstone-blender
Environment=PATH=/home/ec2-user/capstone-blender/.venv/bin
ExecStart=/home/ec2-user/capstone-blender/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create frontend service
sudo tee /etc/systemd/system/capstone-frontend.service > /dev/null << EOF
[Unit]
Description=Capstone Blender Frontend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/capstone-blender/front_end
ExecStart=/usr/bin/python3.12 -m http.server 3000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable capstone-backend
sudo systemctl enable capstone-frontend
sudo systemctl start capstone-backend
sudo systemctl start capstone-frontend
```

#### Step 6: Verify Installation
```bash
# Check service status
sudo systemctl status capstone-backend
sudo systemctl status capstone-frontend

# Check if services are listening on correct ports
sudo netstat -tlnp | grep -E ':(3000|8000)'

# Test API endpoint
curl -X POST http://localhost:8000/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Create a simple cube"}'
```

#### Step 7: Access Your Application
- **Frontend**: `http://your-ec2-public-ip:3000`
- **API**: `http://your-ec2-public-ip:8000`
- **API Documentation**: `http://your-ec2-public-ip:8000/docs`

#### Troubleshooting Commands
```bash
# View service logs
sudo journalctl -u capstone-backend -f
sudo journalctl -u capstone-frontend -f

# Restart services
sudo systemctl restart capstone-backend
sudo systemctl restart capstone-frontend

# Check disk space
df -h

# Check memory usage
free -h

# Test Blender directly
/opt/blender/blender --version
```

#### Security Considerations
- Ensure your security group only allows necessary ports
- Consider using HTTPS with a reverse proxy (nginx)
- Regularly update system packages: `sudo yum update -y`
- Monitor service logs for any issues

#### Optional: Nginx Reverse Proxy Setup
```bash
# Install nginx
sudo yum install nginx -y

# Configure nginx (optional - for production)
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo systemctl start nginx
sudo systemctl enable nginx
```

**Complete AWS guides:**
- `AWS_DEPLOYMENT_STRATEGY.md` - Complete deployment strategy
- `AWS_DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- `SHUTDOWN_GUIDE.md` - Safe resource cleanup

---

## ⚡ Quick Start Summary

**TL;DR - Get running in 5 minutes:**

```bash
# 1. Clone repo
git clone https://github.com/your-username/capstone-blender.git
cd capstone-blender

# 2. Create virtual environment
python -m venv venv && source venv/bin/activate  # Linux
python -m venv venv && .\venv\Scripts\Activate.ps1  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
echo "EXECUTION_MODE=local" > .env
echo "GEMINI_API_KEY=your_key_here" >> .env
echo "BLENDER_PATH=/path/to/blender" >> .env

# 5. Start backend
python -m uvicorn backend.main:app --reload

# 6. Open frontend
open front_end/index.html  # or start http://localhost:8000 in browser
```

Done! 🎉

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

## 🛠️ Development

### Development Setup

**For contributors and developers:**

1. **Fork and clone the repository:**
```bash
git clone https://github.com/your-username/capstone-blender.git
cd capstone-blender
```

2. **Install development dependencies:**

**Using uv:**
```bash
uv sync --extra dev --extra web --extra mcp --extra vector
```

**Using pip:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Install pre-commit hooks (optional but recommended):**
```bash
pip install pre-commit
pre-commit install
```

---

### Code Quality Tools

This project uses several tools to maintain code quality:

| Tool | Purpose | Command |
|------|---------|---------|
| **Black** | Code formatting | `black .` |
| **isort** | Import sorting | `isort .` |
| **mypy** | Type checking | `mypy .` |
| **pylint** | Linting | `pylint agents backend` |
| **pytest** | Testing | `pytest` |

---

### Running Code Quality Checks

**Format code:**
```bash
# Using uv
uv run black .
uv run isort .

# Using pip
black .
isort .
```

**Type checking:**
```bash
# Check specific files
uv run mypy blender_api_parser.py agents/

# Check entire project
uv run mypy .
```

**Linting:**
```bash
uv run pylint agents/ backend/ --disable=C0111,R0903
```

**Run all quality checks:**
```bash
# Format
black . && isort .

# Type check
mypy .

# Lint
pylint agents backend

# Test
pytest
```

---

### Running Tests

**Run all tests:**
```bash
# Using uv
uv run pytest

# Using pip
pytest
```

**Run specific test file:**
```bash
pytest test_complete_pipeline.py -v
```

**Run with coverage:**
```bash
pytest --cov=agents --cov=backend --cov-report=html
```

**Run integration tests only:**
```bash
pytest -m integration
```

---

### Development Workflow

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes and test:**
```bash
# Run tests
pytest

# Check code quality
black . && isort . && mypy .
```

3. **Commit your changes:**
```bash
git add .
git commit -m "feat: add your feature description"
```

4. **Push and create pull request:**
```bash
git push origin feature/your-feature-name
```

---

### Project Development Commands

**Test pipeline end-to-end:**
```bash
python test_complete_pipeline.py
```

**Test local mode execution:**
```bash
python test_local_mode.py
```

**Parse Blender API documentation:**
```bash
python blender_api_parser.py
```

**Start development server with hot reload:**
```bash
uvicorn backend.main:app --reload --log-level debug
```

**Run MCP server (Blender integration):**
```bash
python mcp_servers/base_server.py
```

---

### Debugging

**Enable debug logging:**
```bash
# In .env file
LOG_LEVEL=DEBUG
```

**Debug specific agent:**
```python
# In your test file
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check Blender execution:**
```bash
# Test Blender directly
blender --background --python your_script.py
```

---

### Environment Variables for Development

Create a `.env` file for local development:

```bash
# Execution mode
EXECUTION_MODE=local

# API Keys
GEMINI_API_KEY=your_key_here

# Blender configuration
BLENDER_PATH=D:\blender.exe  # Windows
BLENDER_PATH=/usr/local/bin/blender  # Linux
BLENDER_DOCKER=false

# Logging
LOG_LEVEL=DEBUG

# Rate limiting (for Gemini API)
GEMINI_RPM=15
GEMINI_RPM_WINDOW_SEC=60

# Development settings
RELOAD_ON_CHANGE=true
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

### 🚀 **AWS Deployment Ready (Next Phase)**
- [ ] **Infrastructure as Code**: Complete Terraform configuration
- [ ] **Auto Scaling**: EC2 Auto Scaling Groups with health checks
- [ ] **Load Balancing**: Application Load Balancer with SSL support
- [ ] **Route 53**: DNS configuration for custom domains
- [ ] **Security**: VPC with public/private subnets, security groups

### 🔮 **Future Enhancements**
- [ ] Enhanced object geometry (handles, complex shapes)
- [ ] Lighting and camera positioning
- [ ] Texture mapping and advanced materials
- [ ] Animation support
- [ ] Batch processing
- [ ] User authentication and asset galleries

## 📝 Common Development Tasks

### Adding a New Agent

1. Create agent file in `agents/`:
```python
# agents/my_agent.py
from typing import Dict, Any

class MyAgent:
    def __init__(self):
        pass
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Your logic here
        return {"result": "success"}
```

2. Update agent configuration in `config/agents_config.yaml`
3. Add tests in `tests/test_my_agent.py`
4. Update documentation

### Adding New Blender APIs

1. Update `blender_api_registry.json` (or re-parse Blender docs)
2. Add to `config/curated_allowlist.json` if needed for materials
3. Update `agents/simple_validator.py` if new validation rules needed
4. Test with sample prompts

### Updating Dependencies

**Using uv:**
```bash
# Add new dependency
uv add package-name

# Update all dependencies
uv sync

# Update specific package
uv pip install --upgrade package-name
```

**Using pip:**
```bash
# Add to requirements.txt, then:
pip install -r requirements.txt

# Update all
pip install --upgrade -r requirements.txt
```

### Database/Vector Store Changes

```bash
# Rebuild vector store
python demo_hybrid_vector_store.py

# Update vector store config
nano config/vector_store_config.yaml
```

---

## 🤝 Contributing

We welcome contributions to improve the 3D Asset Generator!

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest`
5. **Format code**: `black . && isort .`
6. **Commit changes**: `git commit -m 'feat: add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure all tests pass
- Use meaningful commit messages (follow [Conventional Commits](https://www.conventionalcommits.org/))

### Areas for Contribution

- 🎨 **3D Modeling**: Improve geometry generation
- 🤖 **AI Agents**: Enhance LLM prompts and logic
- 🎨 **Materials**: Add more material types and textures
- 📚 **Documentation**: Improve guides and examples
- 🐛 **Bug Fixes**: Report and fix issues
- ✨ **New Features**: Lighting, cameras, animations

---

## 📞 Support & Resources

### Documentation
- **Setup Guide**: This README
- **AWS Deployment**: `AWS_DEPLOYMENT_STRATEGY.md`
- **Local Mode**: `docs/LOCAL_MODE_NEW_APPROACH.md`
- **Frontend**: `docs/USER_GUIDE_VIEWER.md`
- **API Documentation**: `http://localhost:8000/docs` (when running)

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/your-username/capstone-blender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/capstone-blender/discussions)
- **Email**: your-email@example.com

### Useful Links

- [Blender Python API Documentation](https://docs.blender.org/api/current/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [uv Documentation](https://github.com/astral-sh/uv)

---

## 🙏 Acknowledgments

- **Blender Foundation** - For the amazing open-source 3D creation suite
- **Google AI** - For Gemini API enabling LLM-powered generation
- **FastAPI** - For the modern, fast web framework
- **Python Community** - For excellent tools and libraries

---

## 📄 License

MIT License

Copyright (c) 2025 3D Asset Generator Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## ⭐ Star History

If you find this project helpful, please consider giving it a star on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/capstone-blender&type=Date)](https://star-history.com/#your-username/capstone-blender&Date)

---

**Made with ❤️ by the 3D Asset Generator Team**

*Last Updated: Oct 26, 2025*
