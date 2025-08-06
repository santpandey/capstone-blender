#!/usr/bin/env python3
"""
Demo script for Hybrid Vector Database System
Showcases FAISS/Qdrant switching with cost-based fallback using Blender API data
"""

import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List

from vector_store import HybridVectorManager, VectorBackend

async def load_blender_api_data() -> List[Dict[str, Any]]:
    """Load Blender API data from the generated registry"""
    try:
        registry_path = Path("blender_api_registry.json")
        if not registry_path.exists():
            print("❌ Blender API registry not found. Please run blender_api_parser.py first.")
            return []
        
        print("📖 Loading Blender API registry...")
        with open(registry_path, 'r', encoding='utf-8') as f:
            # Try different encodings if needed
            try:
                data = json.load(f)
            except UnicodeDecodeError:
                f.seek(0)
                content = f.read().encode('utf-8').decode('utf-8', errors='ignore')
                data = json.loads(content)
        
        # Convert to list format expected by vector store
        documents = []
        
        if isinstance(data, dict):
            # Handle different possible structures
            if 'apis' in data:
                api_data = data['apis']
            else:
                api_data = data
            
            for api_id, api_info in api_data.items():
                if isinstance(api_info, dict):
                    doc = {
                        'id': api_id,
                        'full_name': api_info.get('full_name', api_id),
                        'description': api_info.get('description', ''),
                        'category': api_info.get('category', 'unknown'),
                        'module': api_info.get('module', ''),
                        'signature': api_info.get('signature', ''),
                        'parameters': api_info.get('parameters', []),
                        'tags': api_info.get('tags', []),
                        'examples': api_info.get('examples', [])
                    }
                    documents.append(doc)
        
        elif isinstance(data, list):
            documents = data
        
        print(f"✅ Loaded {len(documents)} Blender API documents")
        return documents[:100]  # Limit for demo
        
    except Exception as e:
        print(f"❌ Failed to load Blender API data: {e}")
        return []

def load_config() -> Dict[str, Any]:
    """Load vector store configuration"""
    try:
        config_path = Path("config/vector_store_config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print("✅ Loaded configuration from config/vector_store_config.yaml")
            return config
        else:
            # Default configuration
            print("⚠️ Config file not found, using defaults")
            return {
                'cost_monitor': {
                    'thresholds': {
                        'max_monthly_cost': 10.0,  # Low threshold for demo
                        'warning_threshold': 0.6,
                        'fallback_threshold': 0.8
                    }
                },
                'faiss': {
                    'backend': 'faiss',
                    'index_path': 'demo_faiss_index',
                    'model_name': 'all-MiniLM-L6-v2'
                },
                'qdrant': {
                    'backend': 'qdrant',
                    'collection_name': 'demo_blender_apis',
                    'url': ':memory:'
                },
                'auto_sync': True
            }
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return {}

async def demo_basic_operations(manager: HybridVectorManager, documents: List[Dict[str, Any]]):
    """Demonstrate basic vector store operations"""
    print("\n" + "="*60)
    print("🔧 BASIC OPERATIONS DEMO")
    print("="*60)
    
    # Add documents
    print(f"\n📥 Adding {len(documents)} Blender API documents...")
    success = await manager.add_documents(documents)
    if success:
        print("✅ Documents added successfully")
    else:
        print("❌ Failed to add documents")
        return
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    test_queries = [
        "create mesh bevel smooth edges",
        "add material shader nodes",
        "transform object rotation",
        "geometry nodes modifier",
        "lighting setup scene"
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = await manager.search(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"    {i}. {result.api_name} (score: {result.score:.3f})")
                print(f"       Category: {result.category}")
                print(f"       Description: {result.content[:80]}...")
        else:
            print("    No results found")

async def demo_hybrid_search(manager: HybridVectorManager):
    """Demonstrate hybrid search capabilities"""
    print("\n" + "="*60)
    print("🔀 HYBRID SEARCH DEMO")
    print("="*60)
    
    test_cases = [
        {
            'query': 'bpy.ops.mesh.bevel',
            'description': 'Exact API name search (should favor fuzzy matching)'
        },
        {
            'query': 'smooth mesh edges',
            'description': 'Semantic search (should favor semantic matching)'
        },
        {
            'query': 'mesh bevel',
            'description': 'Mixed search (should combine both approaches)'
        }
    ]
    
    for case in test_cases:
        query = case['query']
        description = case['description']
        
        print(f"\n🔍 {description}")
        print(f"  Query: '{query}'")
        
        # Compare different search approaches
        semantic_results = await manager.search(query, top_k=3)
        hybrid_results = await manager.hybrid_search(
            query, semantic_weight=0.7, fuzzy_weight=0.3, top_k=3
        )
        
        print("  Semantic Search Results:")
        for i, result in enumerate(semantic_results[:2], 1):
            print(f"    {i}. {result.api_name} (score: {result.score:.3f})")
        
        print("  Hybrid Search Results:")
        for i, result in enumerate(hybrid_results[:2], 1):
            print(f"    {i}. {result.api_name} (score: {result.score:.3f})")

async def demo_cost_monitoring(manager: HybridVectorManager):
    """Demonstrate cost monitoring and fallback"""
    print("\n" + "="*60)
    print("💰 COST MONITORING DEMO")
    print("="*60)
    
    # Show current cost status
    stats = await manager.get_comprehensive_stats()
    cost_summary = stats['cost_summary']
    
    print(f"\n📊 Current Cost Status:")
    print(f"  Status: {cost_summary['status']}")
    print(f"  Estimated Monthly Cost: ${cost_summary['current_metrics']['estimated_monthly_cost']:.2f}")
    print(f"  Cost Ratio: {cost_summary['cost_ratio']:.1%}")
    print(f"  Active Backend: {stats['active_backend']}")
    
    # Simulate high usage to trigger fallback
    print(f"\n🚀 Simulating high search volume to trigger cost fallback...")
    
    # Perform many searches to increase cost
    search_queries = [
        "mesh operations", "material nodes", "object transform",
        "geometry modifier", "lighting setup", "animation keyframe",
        "texture mapping", "particle system", "physics simulation",
        "camera settings", "render engine", "compositor nodes"
    ]
    
    for i, query in enumerate(search_queries, 1):
        await manager.search(query, top_k=2)
        
        if i % 4 == 0:  # Check status every 4 searches
            current_stats = await manager.get_comprehensive_stats()
            current_cost = current_stats['cost_summary']['current_metrics']['estimated_monthly_cost']
            print(f"  After {i} searches - Cost: ${current_cost:.2f}, Backend: {current_stats['active_backend']}")
            
            # Check if fallback occurred
            if current_stats['active_backend'] != stats['active_backend']:
                print(f"  🚨 Fallback triggered! Switched to {current_stats['active_backend']}")
                break

async def demo_backend_switching(manager: HybridVectorManager):
    """Demonstrate manual backend switching"""
    print("\n" + "="*60)
    print("🔄 BACKEND SWITCHING DEMO")
    print("="*60)
    
    # Show current backend
    stats = await manager.get_comprehensive_stats()
    print(f"\n📍 Current backend: {stats['active_backend']}")
    
    # Test search performance on current backend
    query = "create mesh primitive"
    print(f"\n⏱️ Testing search performance...")
    
    import time
    start_time = time.time()
    results = await manager.search(query, top_k=5)
    search_time = time.time() - start_time
    
    print(f"  Search time on {stats['active_backend']}: {search_time:.3f}s")
    print(f"  Results found: {len(results)}")
    
    # Try switching backends if both are available
    current_backend = VectorBackend(stats['active_backend'])
    target_backend = VectorBackend.FAISS if current_backend == VectorBackend.QDRANT else VectorBackend.QDRANT
    
    print(f"\n🔄 Attempting to switch to {target_backend.value}...")
    switch_success = await manager.force_backend(target_backend, "demo_test")
    
    if switch_success:
        # Test search on new backend
        start_time = time.time()
        results = await manager.search(query, top_k=5)
        search_time = time.time() - start_time
        
        print(f"  Search time on {target_backend.value}: {search_time:.3f}s")
        print(f"  Results found: {len(results)}")
        
        # Switch back
        await manager.force_backend(current_backend, "demo_restore")
        print(f"  ✅ Switched back to {current_backend.value}")
    else:
        print(f"  ❌ Could not switch to {target_backend.value}")

async def demo_health_monitoring(manager: HybridVectorManager):
    """Demonstrate health monitoring"""
    print("\n" + "="*60)
    print("🏥 HEALTH MONITORING DEMO")
    print("="*60)
    
    health = await manager.health_check()
    
    print(f"\n📊 System Health Report:")
    print(f"  Overall Status: {health['status']}")
    print(f"  Active Backend: {health['active_backend']}")
    print(f"  Fallback Available: {health['fallback_available']}")
    
    # Detailed stats
    details = health['details']
    
    print(f"\n📈 Performance Metrics:")
    for backend, metrics in details['performance_metrics'].items():
        if metrics['search_count'] > 0:
            print(f"  {backend.upper()}:")
            print(f"    Average search time: {metrics['avg_search_time']:.3f}s")
            print(f"    Total searches: {metrics['search_count']}")
    
    print(f"\n🏪 Store Health:")
    if 'faiss_health' in details:
        faiss_health = details['faiss_health']
        print(f"  FAISS: {faiss_health['status']}")
        if faiss_health['status'] == 'healthy':
            print(f"    Vectors: {faiss_health.get('total_vectors', 0)}")
    
    if 'qdrant_health' in details:
        qdrant_health = details['qdrant_health']
        print(f"  Qdrant: {qdrant_health['status']}")
        if qdrant_health['status'] == 'healthy':
            print(f"    Vectors: {qdrant_health.get('total_vectors', 0)}")

async def main():
    """Main demo function"""
    print("🚀 HYBRID VECTOR DATABASE DEMO")
    print("Showcasing FAISS/Qdrant with Cost-Based Fallback")
    print("="*60)
    
    # Load configuration and data
    config = load_config()
    documents = await load_blender_api_data()
    
    if not documents:
        print("❌ No Blender API data available. Please run blender_api_parser.py first.")
        return
    
    # Initialize hybrid manager
    print("\n🔧 Initializing Hybrid Vector Manager...")
    manager = HybridVectorManager(config)
    
    try:
        success = await manager.initialize()
        if not success:
            print("❌ Failed to initialize hybrid manager")
            return
        
        # Run demos
        await demo_basic_operations(manager, documents)
        await demo_hybrid_search(manager)
        await demo_cost_monitoring(manager)
        await demo_backend_switching(manager)
        await demo_health_monitoring(manager)
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Final summary
        final_stats = await manager.get_comprehensive_stats()
        print(f"\n📊 Final Summary:")
        print(f"  Active Backend: {final_stats['active_backend']}")
        print(f"  Total Cost: ${final_stats['cost_summary']['current_metrics']['estimated_monthly_cost']:.2f}")
        print(f"  System Status: {final_stats['cost_summary']['status']}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
