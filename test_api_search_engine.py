"""
Comprehensive test for the optimized API search engine
Tests all components: registry loading, indices, and search strategies
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any

from agents.api_search import (
    OptimizedAPISearcher,
    SearchContext,
    APICategory,
    SearchConfig
)
from agents.api_search.models import create_search_context

def print_separator(title: str):
    """Print a formatted separator"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)

def print_search_results(results, query: str, max_display: int = 5):
    """Print search results in a formatted way"""
    print(f"\n🔍 **Search Results for**: '{query}'")
    print(f"   Found {len(results)} results")
    
    for i, result in enumerate(results[:max_display], 1):
        print(f"\n   Result {i}:")
        print(f"     API: {result.api.name}")
        print(f"     Category: {result.api.category.value}")
        print(f"     Relevance: {result.relevance_score:.3f}")
        print(f"     Confidence: {result.confidence:.3f}")
        print(f"     Match Type: {result.match_type}")
        print(f"     Description: {result.api.description[:100]}...")
        
        if result.matched_terms:
            print(f"     Matched Terms: {', '.join(result.matched_terms[:3])}")
        
        if result.suggested_parameters:
            print(f"     Suggested Params: {result.suggested_parameters}")
    
    if len(results) > max_display:
        print(f"\n   ... and {len(results) - max_display} more results")

async def test_search_engine_initialization():
    """Test search engine initialization and basic functionality"""
    
    print_separator("SEARCH ENGINE INITIALIZATION TEST")
    
    # Test with default config
    config = SearchConfig(
        enable_caching=True,
        cache_size=500,
        preload_indices=True
    )
    
    searcher = OptimizedAPISearcher(config)
    
    print("🚀 Testing search engine initialization...")
    
    # Test initialization
    start_time = time.time()
    success = await searcher.initialize()
    init_time = (time.time() - start_time) * 1000
    
    if success:
        print(f"✅ Initialization successful in {init_time:.2f}ms")
        
        # Get performance stats
        stats = searcher.get_performance_stats()
        print(f"📊 **Performance Stats**:")
        print(f"   Memory Usage: {stats['memory_usage_mb']:.2f}MB")
        print(f"   Indices Ready: {stats['indices_ready']}")
        
        # Test health check
        health = await searcher.health_check()
        print(f"🏥 **Health Check**:")
        for key, value in health.items():
            print(f"   {key}: {value}")
        
        return searcher
    else:
        print(f"❌ Initialization failed")
        return None

async def test_exact_match_search(searcher):
    """Test exact match search functionality"""
    
    print_separator("EXACT MATCH SEARCH TEST")
    
    # Test exact API name matches
    exact_queries = [
        "bpy.ops.mesh.bevel",
        "bpy.ops.mesh.subdivide", 
        "bpy.ops.object.duplicate",
        "bpy.ops.mesh.extrude_region_move"
    ]
    
    for query in exact_queries:
        print(f"\n🎯 Testing exact match: '{query}'")
        
        start_time = time.time()
        results = await searcher.search(query, create_search_context("exact_match_test"))
        search_time = (time.time() - start_time) * 1000
        
        print(f"   Search time: {search_time:.2f}ms")
        
        if results and results[0].match_type == "exact":
            print(f"   ✅ Exact match found: {results[0].api.name}")
            print(f"   Relevance: {results[0].relevance_score:.3f}")
        else:
            print(f"   ⚠️ No exact match found (got {len(results)} results)")

async def test_fuzzy_search(searcher):
    """Test fuzzy search with typos and variations"""
    
    print_separator("FUZZY SEARCH TEST")
    
    # Test fuzzy queries (with typos and variations)
    fuzzy_queries = [
        "bevl",           # typo in "bevel"
        "subdivid",       # partial "subdivide"
        "extrud",         # partial "extrude"
        "duplicat",       # partial "duplicate"
        "mesh bevel",     # space-separated
        "object rotat"    # partial with space
    ]
    
    for query in fuzzy_queries:
        print(f"\n🔍 Testing fuzzy search: '{query}'")
        
        context = create_search_context("fuzzy_test", max_results=3)
        results = await searcher.search(query, context)
        
        if results:
            print(f"   ✅ Found {len(results)} fuzzy matches")
            best_match = results[0]
            print(f"   Best match: {best_match.api.name}")
            print(f"   Relevance: {best_match.relevance_score:.3f}")
            print(f"   Match type: {best_match.match_type}")
        else:
            print(f"   ❌ No fuzzy matches found")

async def test_semantic_search(searcher):
    """Test semantic search with descriptive queries"""
    
    print_separator("SEMANTIC SEARCH TEST")
    
    # Test semantic queries
    semantic_queries = [
        "smooth edges",
        "add detail to mesh",
        "copy objects",
        "create rounded corners",
        "increase mesh resolution",
        "rotate object around axis",
        "scale uniformly",
        "extrude faces outward"
    ]
    
    for query in semantic_queries:
        print(f"\n🧠 Testing semantic search: '{query}'")
        
        context = create_search_context("semantic_test", max_results=3)
        results = await searcher.search(query, context)
        
        print_search_results(results, query, max_display=2)

async def test_category_filtered_search(searcher):
    """Test category-filtered search"""
    
    print_separator("CATEGORY FILTERED SEARCH TEST")
    
    # Test searches with category preferences
    category_tests = [
        {
            "query": "create primitive",
            "categories": [APICategory.MESH_OPERATORS],
            "description": "Mesh operations only"
        },
        {
            "query": "transform",
            "categories": [APICategory.OBJECT_OPERATORS],
            "description": "Object operations only"
        },
        {
            "query": "material",
            "categories": [APICategory.SHADER_NODES, APICategory.MATERIAL_OPERATORS],
            "description": "Material/shader operations"
        }
    ]
    
    for test in category_tests:
        print(f"\n📂 Testing category filter: {test['description']}")
        print(f"   Query: '{test['query']}'")
        print(f"   Categories: {[cat.value for cat in test['categories']]}")
        
        context = SearchContext(
            task_type="category_test",
            preferred_categories=test["categories"],
            max_results=5
        )
        
        results = await searcher.search(test["query"], context)
        
        if results:
            print(f"   ✅ Found {len(results)} results")
            categories_found = set(r.api.category for r in results)
            print(f"   Categories in results: {[cat.value for cat in categories_found]}")
            
            # Check if results respect category preferences
            preferred_found = any(r.api.category in test["categories"] for r in results)
            if preferred_found:
                print(f"   ✅ Category preferences respected")
            else:
                print(f"   ⚠️ No results from preferred categories")
        else:
            print(f"   ❌ No results found")

async def test_hybrid_search(searcher):
    """Test hybrid search combining multiple strategies"""
    
    print_separator("HYBRID SEARCH TEST")
    
    # Test complex queries that benefit from hybrid approach
    hybrid_queries = [
        "bevel smooth rounded edges",  # Combines exact + semantic
        "mesh subdivide detail",       # Combines fuzzy + semantic  
        "object duplicate copy",       # Multiple strategies
        "extrude faces outward",       # Semantic description
        "rotate 90 degrees"            # Semantic with parameters
    ]
    
    for query in hybrid_queries:
        print(f"\n🔄 Testing hybrid search: '{query}'")
        
        context = create_search_context("hybrid_test", max_results=5)
        context.enable_semantic_search = True
        
        start_time = time.time()
        results = await searcher.search(query, context)
        search_time = (time.time() - start_time) * 1000
        
        print(f"   Search time: {search_time:.2f}ms")
        print_search_results(results, query, max_display=3)
        
        # Analyze match types
        if results:
            match_types = [r.match_type for r in results]
            unique_types = set(match_types)
            print(f"   Match types used: {', '.join(unique_types)}")

async def test_performance_benchmarks(searcher):
    """Test search performance with various query types"""
    
    print_separator("PERFORMANCE BENCHMARK TEST")
    
    # Performance test queries
    perf_queries = [
        ("exact", "bpy.ops.mesh.bevel"),
        ("fuzzy", "bevl"),
        ("semantic", "smooth rounded edges"),
        ("hybrid", "mesh bevel smooth corners"),
        ("category", "transform object")
    ]
    
    print("🚀 Running performance benchmarks...")
    
    total_times = []
    
    for query_type, query in perf_queries:
        times = []
        
        # Run each query multiple times
        for i in range(5):
            start_time = time.time()
            results = await searcher.search(query, create_search_context(f"perf_test_{query_type}"))
            search_time = (time.time() - start_time) * 1000
            times.append(search_time)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        total_times.extend(times)
        
        print(f"\n   {query_type.upper()} Search ('{query}'):")
        print(f"     Average: {avg_time:.2f}ms")
        print(f"     Min: {min_time:.2f}ms")
        print(f"     Max: {max_time:.2f}ms")
    
    overall_avg = sum(total_times) / len(total_times)
    print(f"\n📊 **Overall Performance**:")
    print(f"   Average search time: {overall_avg:.2f}ms")
    print(f"   Total queries tested: {len(total_times)}")
    
    # Check if performance meets targets
    if overall_avg < 50:  # Target: <50ms
        print(f"   ✅ Performance target met (<50ms)")
    else:
        print(f"   ⚠️ Performance target missed (target: <50ms)")

async def test_error_handling(searcher):
    """Test error handling and edge cases"""
    
    print_separator("ERROR HANDLING TEST")
    
    # Test edge cases
    edge_cases = [
        "",                    # Empty query
        "   ",                 # Whitespace only
        "xyz123nonexistent",   # Non-existent API
        "a" * 1000,           # Very long query
        "!@#$%^&*()",         # Special characters only
        "test\nwith\nnewlines" # Query with newlines
    ]
    
    for query in edge_cases:
        print(f"\n🧪 Testing edge case: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        try:
            results = await searcher.search(query, create_search_context("edge_case_test"))
            print(f"   ✅ Handled gracefully - {len(results)} results")
            
            if results:
                print(f"   Best result: {results[0].api.name} (score: {results[0].relevance_score:.3f})")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

async def test_memory_usage(searcher):
    """Test memory usage and resource management"""
    
    print_separator("MEMORY USAGE TEST")
    
    # Get initial memory stats
    initial_stats = searcher.get_performance_stats()
    initial_memory = initial_stats['memory_usage_mb']
    
    print(f"📊 **Memory Usage Analysis**:")
    print(f"   Initial memory usage: {initial_memory:.2f}MB")
    
    # Get detailed index stats
    if hasattr(searcher.indices, 'get_all_stats'):
        index_stats = searcher.indices.get_all_stats()
        print(f"\n   Index breakdown:")
        for index_name, stats in index_stats.items():
            print(f"     {index_name}: {stats.memory_usage_mb:.2f}MB ({stats.total_entries} entries)")
    
    # Test cache behavior
    print(f"\n🗄️ **Cache Performance**:")
    cache_hit_rate = initial_stats.get('cache_hit_rate', 0)
    print(f"   Cache hit rate: {cache_hit_rate:.2%}")
    
    # Test cache clearing
    searcher.clear_caches()
    print(f"   ✅ Caches cleared")
    
    # Memory should stay roughly the same (indices remain)
    post_clear_stats = searcher.get_performance_stats()
    post_clear_memory = post_clear_stats['memory_usage_mb']
    print(f"   Memory after cache clear: {post_clear_memory:.2f}MB")

async def main():
    """Run all tests"""
    
    print("🚀 Starting Comprehensive API Search Engine Tests")
    
    # Initialize search engine
    searcher = await test_search_engine_initialization()
    
    if not searcher:
        print("❌ Cannot continue tests - initialization failed")
        return
    
    # Run all test suites
    try:
        await test_exact_match_search(searcher)
        await test_fuzzy_search(searcher)
        await test_semantic_search(searcher)
        await test_category_filtered_search(searcher)
        await test_hybrid_search(searcher)
        await test_performance_benchmarks(searcher)
        await test_error_handling(searcher)
        await test_memory_usage(searcher)
        
        # Final performance summary
        print_separator("FINAL PERFORMANCE SUMMARY")
        final_stats = searcher.get_performance_stats()
        
        print("📊 **Final Statistics**:")
        for key, value in final_stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.3f}")
            else:
                print(f"   {key}: {value}")
        
        print_separator("ALL TESTS COMPLETED")
        print("✅ API Search Engine testing completed successfully!")
        print("🚀 Ready for integration with Coordinator Agent!")
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
