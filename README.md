# Blender API Extractor & Dynamic 3D Asset Generation

A comprehensive system for dynamic 3D asset generation using natural language prompts, Blender Python API extraction, and MCP server integration.

## Project Overview

This project enables dynamic 3D asset creation through:

1. **Natural Language Processing**: Convert user prompts like "Create a 3D asset of an old man sitting on a chair at his room. Ensure that the lighting is positioned at 30 degrees from the person's head" into actionable Blender operations.

2. **Blender API Extraction**: Parse and centralize all Blender Python API methods from HTML documentation for intelligent discovery and execution.

3. **MCP Server Integration**: Expose Blender APIs through a Model Context Protocol server for seamless client integration.

4. **Asset Pipeline**: Generate, validate, and export 3D assets in GLTF format for three.js rendering.

## Architecture

```
Frontend (React/Vue) → Backend API → Blender Headless → GLTF Export → Three.js Rendering
                                ↓
                        MCP Server (API Discovery)
                                ↓
                        Blender API Registry
```

## Key Components

### 1. Blender API Parser (`blender_api_parser.py`)
- Extracts ~2,000+ API methods from Blender HTML documentation
- Parses method signatures, parameters, types, and descriptions
- Categorizes APIs for intelligent discovery
- Generates semantic tags for natural language mapping

### 2. API Registry
- Centralized database of all Blender Python APIs
- Searchable by natural language queries
- Parameter validation and type checking
- Usage examples and cross-references

### 3. MCP Server (Planned)
- Exposes Blender APIs for client discovery
- Handles API execution on headless Blender instances
- Provides intelligent parameter validation
- Supports batch operations and asset pipelines

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

### Parse Blender API Documentation

```bash
python blender_api_parser.py
```

This will:
- Parse all HTML files in the Blender documentation directory
- Extract API signatures and documentation
- Generate a comprehensive API registry JSON file
- Display parsing statistics

### Example Output

```
Starting Blender API parsing...
Found 2000+ HTML files
Extracted 1500+ API methods

=== PARSING STATISTICS ===
Total APIs extracted: 1547
Top categories:
  mesh_operators: 234
  object_operators: 189
  geometry_nodes: 156
  shader_nodes: 143
```

## Project Structure

```
capstone/
├── blender_api_parser.py      # Main API extraction script
├── blender_python_reference_4_4/  # Blender HTML docs
├── blender_api_registry.json  # Generated API registry
├── pyproject.toml             # Project configuration
├── README.md                  # This file
└── .venv/                     # Virtual environment
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

## Roadmap

- [x] Blender API HTML parser
- [x] API registry generation
- [ ] MCP server implementation
- [ ] Natural language → API mapping
- [ ] Headless Blender integration
- [ ] Asset validation system
- [ ] GLTF export pipeline
- [ ] Three.js integration
- [ ] Frontend interface

## Contributing

This is a capstone project focused on dynamic 3D asset generation. The system aims to democratize 3D content creation through natural language interfaces.

## License

MIT License - See LICENSE file for details.
