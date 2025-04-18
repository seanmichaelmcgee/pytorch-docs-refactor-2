"""
Document processing module for PyTorch Documentation Search Tool.
Handles parsing and chunking of documents with code-aware processing.
"""

import os
import re
import uuid
import glob
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Using tree-sitter for code parsing
from tree_sitter_languages import get_parser

from ptsearch.config import CHUNK_SIZE, OVERLAP_SIZE, DEFAULT_CHUNKS_PATH, logger

class DocumentProcessor:
    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP_SIZE):
        """Initialize document processor with Tree-sitter parsers and chunking parameters."""
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Initialize parsers for markdown and Python
        try:
            self.markdown_parser = get_parser('markdown')
            self.python_parser = get_parser('python')
            logger.info("Document processor initialized with Tree-sitter parsers")
        except Exception as e:
            logger.error(f"Error initializing parsers: {e}")
            raise
    
    def process_directory(self, directory: str, output_file: Optional[str] = DEFAULT_CHUNKS_PATH) -> List[Dict[str, Any]]:
        """Process all documentation files in a directory and save chunks."""
        # Find all markdown and Python files
        file_patterns = ['**/*.md', '**/*.markdown', '**/*.py']
        all_files = []
        
        for pattern in file_patterns:
            matched_files = glob.glob(os.path.join(directory, pattern), recursive=True)
            all_files.extend(matched_files)
        
        logger.info(f"Found {len(all_files)} files to process")
        print(f"Found {len(all_files)} files to process")
        
        # Process each file
        all_chunks = []
        for filepath in all_files:
            try:
                chunks = self.process_file(filepath)
                all_chunks.extend(chunks)
                logger.debug(f"Processed {filepath}: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Error processing file {filepath}: {e}")
        
        logger.info(f"Generated {len(all_chunks)} chunks from {len(all_files)} files")
        print(f"Generated {len(all_chunks)} chunks from {len(all_files)} files")
        
        # Save chunks if output file is specified
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_chunks, f, indent=2)
            logger.info(f"Saved chunks to {output_file}")
            print(f"Saved chunks to {output_file}")
        
        return all_chunks
    
    def process_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Process a single file into chunks with metadata."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.basename(filepath)
            
            # Process markdown files
            if filepath.endswith(('.md', '.markdown')):
                sections = self._parse_markdown(content, filename)
            else:
                # For non-markdown files, treat as code
                extension = Path(filepath).suffix.lstrip('.')
                sections = [{
                    'text': content,
                    'metadata': {
                        'title': filename,
                        'source': filename,
                        'chunk_type': 'code',
                        'language': extension
                    }
                }]
            
            # Chunk sections
            chunks = self._chunk_sections(sections)
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")
            return []
    
    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        # Look for the first heading
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled Document"
    
    def _parse_markdown(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Parse markdown content into sections."""
        sections = []
        tree = self.markdown_parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node
        
        # Extract title and initialize heading context
        title = self._extract_title(content)
        current_heading = title
        
        # Process each node
        for child in root_node.children:
            # Check if it's a heading
            if child.type == 'atx_heading':
                heading_text_node = child.child_by_field_name('heading_content')
                if heading_text_node:
                    heading_text = content[heading_text_node.start_byte:heading_text_node.end_byte]
                    current_heading = heading_text
            
            # Check if it's a code block
            elif child.type == 'fenced_code_block':
                # Extract language info
                info_string = ''
                info_node = child.child_by_field_name('info_string')
                if info_node:
                    info_string = content[info_node.start_byte:info_node.end_byte]
                
                # Extract code content
                code_text = ''
                for code_node in child.children:
                    if code_node.type == 'code_fence_content':
                        code_text = content[code_node.start_byte:code_node.end_byte]
                
                # Add as a section
                if code_text.strip():
                    sections.append({
                        'text': code_text,
                        'metadata': {
                            'title': current_heading,
                            'source': filename,
                            'chunk_type': 'code',
                            'language': info_string
                        }
                    })
            
            # Check if it's a paragraph or other text content
            elif child.type in ('paragraph', 'block_quote', 'list'):
                text = content[child.start_byte:child.end_byte]
                if text.strip():
                    sections.append({
                        'text': text,
                        'metadata': {
                            'title': current_heading,
                            'source': filename,
                            'chunk_type': 'text'
                        }
                    })
        
        return sections
    
    def _chunk_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk sections with code-aware boundaries."""
        all_chunks = []
        
        for section in sections:
            text = section['text']
            metadata = section['metadata']
            
            # For code blocks, keep them intact if possible
            if metadata.get('chunk_type') == 'code':
                # If small enough, keep as one chunk
                if len(text) <= self.chunk_size * 1.5:
                    all_chunks.append({
                        'id': str(uuid.uuid4()),
                        'text': text,
                        'metadata': metadata
                    })
                else:
                    # For larger code blocks, split at logical boundaries
                    chunks = self._chunk_code(text, metadata)
                    all_chunks.extend(chunks)
            else:
                # For text, use paragraph boundaries
                chunks = self._chunk_text(text, metadata)
                all_chunks.extend(chunks)
        
        return all_chunks
    
    def _find_code_chunk_points(self, code: str) -> List[int]:
        """Find good splitting points in code (class/function definitions)."""
        chunk_points = []
        
        # Simple patterns to detect Python structures
        patterns = [
            r'^\s*def\s+\w+\s*\(',  # Function definitions
            r'^\s*class\s+\w+\s*[:\(]',  # Class definitions
            r'^\s*if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:',  # Main block
            r'^\s*@\w+',  # Decorators
            r'^\s*#\s*\w+',  # Section comments
        ]
        
        # Find line start positions
        line_start_positions = [0]
        for i, char in enumerate(code):
            if char == '\n':
                line_start_positions.append(i + 1)
        
        # Check each line against patterns
        for i, line_start in enumerate(line_start_positions):
            line_end = code.find('\n', line_start)
            if line_end == -1:
                line_end = len(code)
            
            line = code[line_start:line_end]
            
            # Check line against all patterns
            for pattern in patterns:
                if re.match(pattern, line):
                    chunk_points.append(line_start)
                    break
        
        # Remove points that are too close together (at least 5 lines apart)
        if chunk_points:
            filtered_points = [chunk_points[0]]
            
            for point in chunk_points[1:]:
                prev_point = filtered_points[-1]
                
                # Convert to line numbers for distance check
                prev_line = line_start_positions.index(prev_point)
                current_line = line_start_positions.index(point)
                
                # Ensure points are at least 5 lines apart
                if current_line - prev_line >= 5:
                    filtered_points.append(point)
            
            return filtered_points
        
        return chunk_points
    
    def _chunk_code(self, code: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk code with logical boundaries."""
        chunks = []
        
        # Find good splitting points
        chunk_points = self._find_code_chunk_points(code)
        
        if chunk_points:
            # Use the identified chunk points
            start_idx = 0
            chunk_num = 1
            
            for point in chunk_points:
                # Ensure minimum chunk size
                if point - start_idx >= self.chunk_size / 2:
                    chunks.append({
                        'id': str(uuid.uuid4()),
                        'text': code[start_idx:point],
                        'metadata': {**metadata, 'chunk': chunk_num}
                    })
                    start_idx = max(0, point - self.overlap)
                    chunk_num += 1
            
            # Add the final chunk
            if start_idx < len(code):
                chunks.append({
                    'id': str(uuid.uuid4()),
                    'text': code[start_idx:],
                    'metadata': {**metadata, 'chunk': chunk_num}
                })
        else:
            # Fall back to character-based chunking
            chunks.extend(self._character_chunk(code, metadata))
        
        return chunks
    
    def _chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text using paragraph boundaries."""
        chunks = []
        
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        chunk_num = 1
        
        for para in paragraphs:
            # If adding this paragraph exceeds the chunk size
            if len(current_chunk) + len(para) > self.chunk_size:
                # If we have content to save
                if current_chunk:
                    chunks.append({
                        'id': str(uuid.uuid4()),
                        'text': current_chunk.strip(),
                        'metadata': {**metadata, 'chunk': chunk_num}
                    })
                    chunk_num += 1
                
                # Start a new chunk
                if len(para) > self.chunk_size:
                    # If paragraph itself is too large, fall back to sentence splitting
                    for sub_chunk in self._split_large_paragraph(para, metadata, chunk_num):
                        chunks.append(sub_chunk)
                        chunk_num += 1
                else:
                    current_chunk = para + "\n\n"
            else:
                current_chunk += para + "\n\n"
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append({
                'id': str(uuid.uuid4()),
                'text': current_chunk.strip(),
                'metadata': {**metadata, 'chunk': chunk_num}
            })
        
        return chunks
    
    def _split_large_paragraph(self, para: str, metadata: Dict[str, Any], start_chunk_num: int) -> List[Dict[str, Any]]:
        """Split a large paragraph into sentence-based chunks."""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', para)
        
        current_chunk = ""
        chunk_num = start_chunk_num
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        'id': str(uuid.uuid4()),
                        'text': current_chunk.strip(),
                        'metadata': {**metadata, 'chunk': chunk_num}
                    })
                    chunk_num += 1
                    current_chunk = sentence + " "
                else:
                    # If a single sentence is too long, split it
                    chunks.extend(self._character_chunk(sentence, metadata))
            else:
                current_chunk += sentence + " "
        
        # Add the last chunk if needed
        if current_chunk.strip():
            chunks.append({
                'id': str(uuid.uuid4()),
                'text': current_chunk.strip(),
                'metadata': {**metadata, 'chunk': chunk_num}
            })
        
        return chunks
    
    def _character_chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fall back to character-based chunking with overlap."""
        chunks = []
        
        start = 0
        chunk_num = 1
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # If not at the end, look for a better split point
            if end < len(text):
                # Try to find sentence boundary
                sentence_boundary = text.rfind('.', start, end)
                if sentence_boundary > start + self.chunk_size / 2:
                    end = sentence_boundary + 1
                else:
                    # Try to find word boundary
                    space = text.rfind(' ', start, end)
                    if space > start + self.chunk_size / 2:
                        end = space
            
            chunks.append({
                'id': str(uuid.uuid4()),
                'text': text[start:end].strip(),
                'metadata': {**metadata, 'chunk': chunk_num}
            })
            
            # Move to next chunk with overlap
            start = end - self.overlap if end - self.overlap > start else end
            chunk_num += 1
            
            # Avoid infinite loop
            if start >= len(text) or (end == len(text) and chunk_num > 1):
                break
        
        return chunks