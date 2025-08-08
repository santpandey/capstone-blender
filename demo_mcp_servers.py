#!/usr/bin/env python3
"""
Demo script for Blender API MCP Servers
Showcases multiple specialized servers with intelligent API discovery
"""

import asyncio
import yaml
from pathlib import Path
from typing import Dict, Any

from mcp_servers import BlenderMeshServer
from mcp_servers.models import (
    DiscoverMeshAPIsInput, MeshOperationType,
    ValidateParametersInput, GenerateCodeInput,
    HealthCheckOutput
)

def load_mcp_config() -> Dict[str, Any]:
    """Load MCP servers configuration"""
    try:
        config_path = Path("config/mcp_servers_config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print("✅ Loaded MCP servers configuration")
            return config
        else:
            # Default configuration
            print("⚠️ Config file not found, using defaults")
            return {
                'vector_store': {
                    'faiss': {'index_path': 'demo_mcp_faiss'},
                    'qdrant': {'collection_name': 'demo_mcp_apis', 'url': ':memory:'}
                },
                'servers': {
                    'blender-mesh': {
                        'enabled': True,
                        'category': 'mesh_operators'
                    }
                }
            }
    except Exception as e:
        print(f"❌ Failed to load MCP config: {e}")
        return {}

async def demo_mesh_server_initialization(config: Dict[str, Any]):
    """Demonstrate mesh server initialization"""
    print("\n" + "="*60)
    print("🔧 MESH MCP SERVER INITIALIZATION")
    print("="*60)
    
    try:
        # Create mesh server
        print("\n🏗️ Creating Blender Mesh MCP Server...")
        mesh_server = BlenderMeshServer(config)
        
        # Initialize server
        print("⚡ Initializing server...")
        success = await mesh_server.initialize()
        
        if success:
            print("✅ Mesh MCP server initialized successfully!")
            print(f"   Server Name: {mesh_server.server_name}")
            print(f"   Category: {mesh_server.category}")
            print(f"   API Count: {len(mesh_server.api_registry)}")
            print(f"   Vector Backend: {mesh_server.vector_manager.active_backend.value}")
            return mesh_server
        else:
            print("❌ Failed to initialize mesh server")
            return None
            
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return None

async def demo_api_discovery(server: BlenderMeshServer):
    """Demonstrate intelligent API discovery"""
    print("\n" + "="*60)
    print("🔍 INTELLIGENT API DISCOVERY")
    print("="*60)
    
    test_cases = [
        {
            'intent': 'create smooth rounded edges on selected faces',
            'operation_type': MeshOperationType.MODELING,
            'description': 'Modeling operation with specific intent'
        },
        {
            'intent': 'subdivide mesh for more detail',
            'operation_type': MeshOperationType.SUBDIVISION,
            'description': 'Subdivision operation'
        },
        {
            'intent': 'clean up duplicate vertices',
            'operation_type': MeshOperationType.CLEANUP,
            'description': 'Cleanup operation'
        },
        {
            'intent': 'select all faces with similar area',
            'operation_type': MeshOperationType.ANALYSIS,
            'description': 'Analysis/selection operation'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {case['description']}")
        print(f"   Intent: '{case['intent']}'")
        print(f"   Operation Type: {case['operation_type'].value}")
        
        try:
            # Create discovery input
            discovery_input = DiscoverMeshAPIsInput(
                intent=case['intent'],
                operation_type=case['operation_type'],
                top_k=3,
                include_examples=True
            )
            
            # Discover APIs
            result = await server._discover_mesh_apis_impl(discovery_input)
            
            print(f"   📊 Results: {result.total_found} APIs found")
            print(f"   ⚡ Backend: {result.backend_used}")
            
            # Show top results
            for j, api in enumerate(result.apis[:2], 1):
                print(f"      {j}. {api.full_name} (score: {api.score:.3f})")
                print(f"         Description: {api.description[:60]}...")
                print(f"         Parameters: {len(api.parameters)}")
            
            # Show suggestions
            if result.suggestions:
                print(f"   💡 Suggestions: {', '.join(result.suggestions[:2])}")
                
        except Exception as e:
            print(f"   ❌ Discovery failed: {e}")

async def demo_parameter_validation(server: BlenderMeshServer):
    """Demonstrate parameter validation"""
    print("\n" + "="*60)
    print("✅ PARAMETER VALIDATION")
    print("="*60)
    
    # Test cases with different parameter scenarios
    test_cases = [
        {
            'api_name': 'bpy.ops.mesh.bevel',
            'parameters': {
                'offset': 0.1,
                'segments': 3,
                'profile': 0.5
            },
            'description': 'Valid bevel parameters'
        },
        {
            'api_name': 'bpy.ops.mesh.subdivide',
            'parameters': {
                'number_cuts': 'invalid',  # Should be int
                'smoothness': 1.5
            },
            'description': 'Invalid parameter type'
        },
        {
            'api_name': 'bpy.ops.mesh.extrude_region_move',
            'parameters': {
                # Missing required parameters
            },
            'description': 'Missing required parameters'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n✅ Test Case {i}: {case['description']}")
        print(f"   API: {case['api_name']}")
        print(f"   Parameters: {case['parameters']}")
        
        try:
            # Create validation input
            validation_input = ValidateParametersInput(
                api_name=case['api_name'],
                parameters=case['parameters']
            )
            
            # Validate parameters
            result = await server._validate_parameters_impl(validation_input)
            
            print(f"   📊 Valid: {result.valid}")
            
            if result.validation_errors:
                print(f"   ❌ Errors:")
                for error in result.validation_errors[:2]:
                    print(f"      - {error}")
            
            if result.corrected_parameters:
                print(f"   🔧 Corrected Parameters: {len(result.corrected_parameters)}")
            
            # Show parameter results
            for param_result in result.parameter_results[:3]:
                status = "✅" if param_result.valid else "❌"
                print(f"      {status} {param_result.name} ({param_result.type_info})")
                if param_result.error_message:
                    print(f"         Error: {param_result.error_message}")
                    
        except Exception as e:
            print(f"   ❌ Validation failed: {e}")

async def demo_code_generation(server: BlenderMeshServer):
    """Demonstrate code generation"""
    print("\n" + "="*60)
    print("🐍 CODE GENERATION")
    print("="*60)
    
    test_cases = [
        {
            'apis': ['bpy.ops.mesh.primitive_cube_add', 'bpy.ops.mesh.bevel'],
            'parameters': {
                'bpy.ops.mesh.primitive_cube_add': {'size': 2.0, 'location': (0, 0, 0)},
                'bpy.ops.mesh.bevel': {'offset': 0.1, 'segments': 3}
            },
            'context': 'Create a beveled cube for architectural modeling',
            'description': 'Basic modeling workflow'
        },
        {
            'apis': ['bpy.ops.mesh.subdivide', 'bpy.ops.mesh.vertices_smooth'],
            'parameters': {
                'bpy.ops.mesh.subdivide': {'number_cuts': 2},
                'bpy.ops.mesh.vertices_smooth': {'factor': 0.5}
            },
            'context': 'Smooth selected mesh for organic modeling',
            'description': 'Subdivision and smoothing'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🐍 Test Case {i}: {case['description']}")
        print(f"   Context: {case['context']}")
        print(f"   APIs: {len(case['apis'])}")
        
        try:
            # Create code generation input
            code_input = GenerateCodeInput(
                apis=case['apis'],
                parameters=case['parameters'],
                context=case['context'],
                include_error_handling=True,
                include_comments=True
            )
            
            # Generate code
            result = await server._generate_code_impl(code_input)
            
            print(f"   📊 Generated Code:")
            print("   " + "-" * 40)
            # Show first few lines of generated code
            code_lines = result.code.split('\n')
            for line in code_lines[:8]:
                print(f"   {line}")
            if len(code_lines) > 8:
                print(f"   ... ({len(code_lines) - 8} more lines)")
            print("   " + "-" * 40)
            
            print(f"   📦 Imports: {', '.join(result.imports)}")
            if result.warnings:
                print(f"   ⚠️ Warnings: {len(result.warnings)}")
            if result.estimated_execution_time:
                print(f"   ⏱️ Estimated Time: {result.estimated_execution_time:.1f}s")
                
        except Exception as e:
            print(f"   ❌ Code generation failed: {e}")

async def demo_mesh_workflows(server: BlenderMeshServer):
    """Demonstrate mesh-specific workflow features"""
    print("\n" + "="*60)
    print("🔄 MESH WORKFLOW FEATURES")
    print("="*60)
    
    # Test workflow generation
    print("\n🔄 Workflow Generation:")
    workflow_intents = [
        "create a character head",
        "model a simple building",
        "make organic tree trunk"
    ]
    
    for intent in workflow_intents:
        print(f"\n   Intent: '{intent}'")
        try:
            result = await server._get_modeling_workflow_impl(intent)
            
            print(f"   📋 Workflow: {result.get('workflow_name', 'unknown')}")
            print(f"   🔧 Operations: {len(result.get('operations', []))}")
            print(f"   ⏱️ Estimated Time: {result.get('estimated_time', 0)} minutes")
            print(f"   📈 Difficulty: {result.get('difficulty', 'unknown')}")
            
            # Show first few operations
            operations = result.get('operations', [])
            for i, op in enumerate(operations[:3], 1):
                print(f"      {i}. {op}")
            if len(operations) > 3:
                print(f"      ... ({len(operations) - 3} more operations)")
                
        except Exception as e:
            print(f"   ❌ Workflow generation failed: {e}")
    
    # Test operation suggestions
    print("\n💡 Operation Suggestions:")
    suggestion_cases = [
        ("selected faces", "add more detail"),
        ("cube primitive", "make it rounded"),
        ("subdivided mesh", "smooth the surface")
    ]
    
    for current_selection, goal in suggestion_cases:
        print(f"\n   Current: {current_selection} → Goal: {goal}")
        try:
            result = await server._suggest_mesh_operations_impl(current_selection, goal)
            
            suggestions = result.get('suggestions', [])
            print(f"   📊 Suggestions: {len(suggestions)}")
            
            for i, suggestion in enumerate(suggestions[:2], 1):
                print(f"      {i}. {suggestion.get('operation', 'unknown')}")
                print(f"         Confidence: {suggestion.get('confidence', 0):.3f}")
                
        except Exception as e:
            print(f"   ❌ Suggestion failed: {e}")

async def demo_health_monitoring(server: BlenderMeshServer):
    """Demonstrate health monitoring"""
    print("\n" + "="*60)
    print("🏥 HEALTH MONITORING")
    print("="*60)
    
    try:
        # Get health check
        health = await server._health_check_impl()
        
        print(f"\n📊 Server Health Report:")
        print(f"   Status: {health.status}")
        print(f"   Server: {health.server_name}")
        print(f"   API Count: {health.api_count}")
        print(f"   Vector Store: {health.vector_store_status}")
        print(f"   Blender Connection: {health.blender_connection_status}")
        
        # Performance metrics
        metrics = health.performance_metrics
        print(f"\n📈 Performance Metrics:")
        print(f"   Total Requests: {metrics.get('total_requests', 0)}")
        print(f"   Successful Requests: {metrics.get('successful_requests', 0)}")
        print(f"   Average Response Time: {metrics.get('avg_response_time', 0):.2f}ms")
        
        # Vector store detailed health
        vector_health = await server.vector_manager.health_check()
        print(f"\n🏪 Vector Store Details:")
        print(f"   Overall Status: {vector_health.get('status', 'unknown')}")
        print(f"   Active Backend: {vector_health.get('active_backend', 'unknown')}")
        print(f"   Fallback Available: {vector_health.get('fallback_available', False)}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")

async def main():
    """Main demo function"""
    print("🚀 BLENDER API MCP SERVERS DEMO")
    print("Multiple Specialized Servers with Intelligent API Discovery")
    print("="*60)
    
    # Load configuration
    config = load_mcp_config()
    if not config:
        print("❌ No configuration available")
        return
    
    # Use vector store config
    server_config = config.get('vector_store', {})
    
    try:
        # Initialize mesh server
        mesh_server = await demo_mesh_server_initialization(server_config)
        if not mesh_server:
            print("❌ Cannot proceed without mesh server")
            return
        
        # Run demos
        await demo_api_discovery(mesh_server)
        await demo_parameter_validation(mesh_server)
        await demo_code_generation(mesh_server)
        await demo_mesh_workflows(mesh_server)
        await demo_health_monitoring(mesh_server)
        
        print("\n" + "="*60)
        print("✅ MCP SERVERS DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Final summary
        print(f"\n📊 Demo Summary:")
        print(f"   Server Type: {mesh_server.server_name}")
        print(f"   APIs Available: {len(mesh_server.api_registry)}")
        print(f"   Vector Backend: {mesh_server.vector_manager.active_backend.value}")
        print(f"   Total Requests: {mesh_server.metrics['total_requests']}")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Start MCP server: python -m mcp_servers.mesh_server")
        print(f"   2. Connect client applications to discover and use Blender APIs")
        print(f"   3. Implement additional servers for objects, geometry, and shaders")
        print(f"   4. Integrate with multi-agent pipeline for complete 3D asset generation")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if 'mesh_server' in locals() and mesh_server:
            print("\n🧹 Cleaning up...")
            await mesh_server.vector_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
