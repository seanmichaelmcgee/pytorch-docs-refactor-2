#!/usr/bin/env python3
"""
Environment validation script for PyTorch Documentation Search Tool.
Checks all required components and dependencies.
"""

import os
import sys
import json
import time

def check_imports():
    """Check that all required packages can be imported."""
    missing_packages = []
    
    packages = [
        "flask",
        "openai",
        "chromadb",
        "dotenv",
        "numpy",
        "tqdm",
        "werkzeug"
    ]
    
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✅ {pkg} imported successfully")
        except ImportError:
            missing_packages.append(pkg)
            print(f"❌ Failed to import {pkg}")
    
    return missing_packages

def check_openai_api():
    """Test OpenAI API connection."""
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ OPENAI_API_KEY found (starts with {api_key[:4]}...)")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Try a simple models.list call to check connectivity
        start_time = time.time()
        models = client.models.list()
        duration = time.time() - start_time
        
        print(f"✅ OpenAI API connection successful (took {duration:.2f}s)")
        
        # Check for embedding models
        embedding_models = [model.id for model in models.data if "embedding" in model.id]
        if embedding_models:
            print(f"✅ Found embedding models: {', '.join(embedding_models[:3])}...")
        else:
            print("⚠️ No embedding models found in the model list")
        
        return True
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def check_database():
    """Test ChromaDB functionality."""
    try:
        import chromadb
        
        # Create a temporary in-memory client
        client = chromadb.Client()
        
        # Create and delete a collection to test functionality
        collection = client.create_collection("test_collection")
        collections = client.list_collections()
        
        if any(c.name == "test_collection" for c in collections):
            print(f"✅ ChromaDB test successful - created collection")
            client.delete_collection("test_collection")
            print(f"✅ ChromaDB test successful - deleted collection")
            return True
        else:
            print("❌ ChromaDB test failed - collection not found after creation")
            return False
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False

def check_filesystem():
    """Check filesystem permissions for data directories."""
    directories = [
        "./data",
        "./data/chroma_db",
        "./data/embedding_cache"
    ]
    
    for directory in directories:
        # Check if directory exists
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"✅ Created directory {directory}")
            except Exception as e:
                print(f"❌ Failed to create directory {directory}: {e}")
                continue
        
        # Check if we can write to it
        try:
            test_file = os.path.join(directory, ".test_file")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print(f"✅ Directory {directory} is writable")
        except Exception as e:
            print(f"❌ Directory {directory} is not writable: {e}")

def main():
    """Run all environment checks."""
    print("=" * 60)
    print("PyTorch Documentation Search Tool - Environment Check")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print("-" * 60)
    
    print("\n1. Checking package imports...")
    missing_packages = check_imports()
    
    print("\n2. Checking OpenAI API...")
    api_ok = check_openai_api()
    
    print("\n3. Checking ChromaDB...")
    db_ok = check_database()
    
    print("\n4. Checking filesystem permissions...")
    check_filesystem()
    
    print("\n" + "=" * 60)
    print("Environment Check Summary:")
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
    else:
        print("✅ All required packages installed")
    
    print(f"{'✅' if api_ok else '❌'} OpenAI API {'connection OK' if api_ok else 'connection failed'}")
    print(f"{'✅' if db_ok else '❌'} ChromaDB {'functioning properly' if db_ok else 'test failed'}")
    
    if not missing_packages and api_ok and db_ok:
        print("\n✅ Environment check PASSED - system is ready to use!")
        return 0
    else:
        print("\n⚠️ Environment check FAILED - please fix the issues above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())