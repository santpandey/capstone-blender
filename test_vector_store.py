#!/usr/bin/env python3
"""
Simple test script to verify the hybrid vector database system works
"""

import asyncio
import json
from pathlib import Path
from vector_store import HybridVectorManager

async def quick_test():
    """Quick test of the hybrid vector system"""
    print("🧪 Quick Test: Hybrid Vector Database System")
    print("="*50)
    
    # Simple configuration for testing
    config = {
        'cost_monitor': {
            'thresholds': {
                'max_monthly_cost': 5.0,
                'warning_threshold': 0.7,
                'fallback_threshold': 0.9
            }
        },
        'faiss': {
            'backend': 'faiss',
            'index_path': 'test_faiss_index',
            'model_name': 'all-MiniLM-L6-v2'
        },
        'qdrant': {
            'backend': 'qdrant',
            'collection_name': 'test_blender_apis',
            'url': ':memory:'
        }
    }
    
    # Sample Blender API documents
    sample_docs = [
        {
            'id': 'bpy.ops.mesh.bevel',
            'full_name': 'bpy.ops.mesh.bevel',
            'description': 'Bevel selected edges or vertices',
            'category': 'mesh_operators',
            'module': 'bpy.ops.mesh',
            'parameters': [
                {'name': 'offset', 'type': 'float', 'description': 'Bevel offset'}
            ],
            'tags': ['mesh', 'bevel', 'edges', 'modeling']
        },
        {
            'id': 'bpy.ops.object.transform_apply',
            'full_name': 'bpy.ops.object.transform_apply',
            'description': 'Apply object transformations',
            'category': 'object_operators',
            'module': 'bpy.ops.object',
            'parameters': [
                {'name': 'location', 'type': 'bool', 'description': 'Apply location'}
            ],
            'tags': ['object', 'transform', 'apply']
        },
        {
            'id': 'bpy.ops.material.new',
            'full_name': 'bpy.ops.material.new',
            'description': 'Create a new material',
            'category': 'material_operators',
            'module': 'bpy.ops.material',
            'parameters': [],
            'tags': ['material', 'create', 'shader']
        }
    ]
    
    try:
        # Initialize manager
        print("\n🔧 Initializing hybrid manager...")
        manager = HybridVectorManager(config)
        
        success = await manager.initialize()
        if not success:
            print("❌ Initialization failed")
            return
        
        print("✅ Manager initialized successfully")
        
        # Add documents
        print(f"\n📥 Adding {len(sample_docs)} sample documents...")
        add_success = await manager.add_documents(sample_docs)
        
        if add_success:
            print("✅ Documents added successfully")
        else:
            print("❌ Failed to add documents")
            return
        
        # Test search
        print("\n🔍 Testing search functionality...")
        test_queries = [
            "bevel mesh edges",
            "apply transform",
            "create material"
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            results = await manager.search(query, top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"    {i}. {result.api_name} (score: {result.score:.3f})")
            else:
                print("    No results found")
        
        # Test hybrid search
        print("\n🔀 Testing hybrid search...")
        hybrid_results = await manager.hybrid_search("bpy.ops.mesh.bevel", top_k=2)
        
        if hybrid_results:
            print("  Hybrid search results:")
            for i, result in enumerate(hybrid_results, 1):
                print(f"    {i}. {result.api_name} (score: {result.score:.3f})")
        
        # Health check
        print("\n🏥 Health check...")
        health = await manager.health_check()
        print(f"  Status: {health['status']}")
        print(f"  Active Backend: {health['active_backend']}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await manager.close()
            print("🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(quick_test())
