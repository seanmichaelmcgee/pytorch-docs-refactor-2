#!/usr/bin/env python3
"""
Command-line interface for PyTorch Documentation Search Tool.
"""

import sys
import os
import argparse

from ptsearch.search import SearchEngine
from ptsearch.database import DatabaseManager
from ptsearch.embedding import EmbeddingGenerator
from ptsearch.config import MAX_RESULTS


def main():
    """Main CLI entry point for PyTorch Documentation Search Tool."""
    parser = argparse.ArgumentParser(description="PyTorch Documentation Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process documents into chunks")
    process_parser.add_argument("--docs-dir", required=True, help="Directory containing documentation files")
    process_parser.add_argument("--output-file", help="Output JSON file to save chunks")
    
    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Generate embeddings for chunks")
    embed_parser.add_argument("--input-file", help="Input JSON file with document chunks")
    embed_parser.add_argument("--output-file", help="Output JSON file to save chunks with embeddings")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index chunks into database")
    index_parser.add_argument("--input-file", help="Input JSON file with chunks and embeddings")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search documentation")
    search_parser.add_argument("query", nargs="?", help="The search query")
    search_parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    search_parser.add_argument("--results", "-n", type=int, default=MAX_RESULTS, help="Number of results to return")
    search_parser.add_argument("--filter", "-f", choices=["code", "text"], help="Filter results by type")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start MCP-compatible server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", "-p", type=int, default=5000, help="Server port")
    
    # Stdio command
    stdio_parser = subparsers.add_parser("stdio", help="Start MCP-compatible stdio server")
    
    args = parser.parse_args()
    
    if args.command == "process":
        from ptsearch.document import DocumentProcessor
        processor = DocumentProcessor()
        processor.process_directory(args.docs_dir, args.output_file)
    
    elif args.command == "embed":
        from ptsearch.embedding import EmbeddingGenerator
        generator = EmbeddingGenerator()
        generator.process_file(args.input_file, args.output_file)
    
    elif args.command == "index":
        from ptsearch.database import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.load_from_file(args.input_file)
    
    elif args.command == "search":
        # Initialize components
        db_manager = DatabaseManager()
        embedding_generator = EmbeddingGenerator()
        search_engine = SearchEngine(db_manager, embedding_generator)
        
        if args.interactive:
            # Interactive search mode
            print("PyTorch Documentation Search (type 'exit' to quit)")
            while True:
                query = input("\nEnter search query: ")
                if query.lower() in ('exit', 'quit'):
                    break
                
                results = search_engine.search(query, args.results, args.filter)
                
                if "error" in results:
                    print(f"Error: {results['error']}")
                else:
                    print(f"\nFound {len(results['results'])} results for '{query}':")
                    
                    for i, res in enumerate(results["results"]):
                        print(f"\n--- Result {i+1} ({res['chunk_type']}) ---")
                        print(f"Title: {res['title']}")
                        print(f"Source: {res['source']}")
                        print(f"Score: {res['score']:.4f}")
                        print(f"Snippet: {res['snippet']}")
        
        elif args.query:
            # Direct query mode
            results = search_engine.search(args.query, args.results, args.filter)
            
            print(f"\nFound {len(results['results'])} results for '{args.query}':")
            
            for i, res in enumerate(results["results"]):
                print(f"\n--- Result {i+1} ({res['chunk_type']}) ---")
                print(f"Title: {res['title']}")
                print(f"Source: {res['source']}")
                print(f"Score: {res['score']:.4f}")
                print(f"Snippet: {res['snippet']}")
    
    elif args.command == "server":
        from ptsearch.mcp import run_server
        run_server(host=args.host, port=args.port)
    
    elif args.command == "stdio":
        from ptsearch.stdio import main as stdio_main
        stdio_main()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()