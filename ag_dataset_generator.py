import random
import csv
import os
import numpy as np

def read_text_file(file_path):
    """Read the content of a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_chunk_sizes():
    """Generate a list of reasonably different chunk sizes between 50 and 400 words."""
    # We'll create a range of sizes distributed across the range
    min_size = 50
    max_size = 400
    
    # Generate reasonably different sizes using np.linspace
    sizes = np.linspace(min_size, max_size, 10, dtype=int)
    return list(sizes)

def extract_chunks(text, chunk_sizes, chunks_per_size=10):
    """Extract random chunks of specified sizes from the text."""
    words = text.split()
    total_words = len(words)
    
    chunks = []
    for size in chunk_sizes:
        for _ in range(chunks_per_size):
            # Ensure we can extract a chunk of this size
            if size > total_words:
                print(f"Warning: Text has fewer words ({total_words}) than requested chunk size ({size})")
                continue
                
            # Choose a random starting position
            max_start_pos = total_words - size
            start_pos = random.randint(0, max_start_pos)
            
            # Extract the chunk
            chunk_words = words[start_pos:start_pos + size]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append((chunk_text, size))
    
    return chunks

def save_to_csv(chunks, output_file):
    """Save chunks to a CSV file."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['text', 'word_count'])
        # Write data
        for chunk_text, chunk_size in chunks:
            writer.writerow([chunk_text, chunk_size])

def main():
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'src', 'ag_script.txt')
    output_file = os.path.join(script_dir, 'ag_split_test.csv')
    
    # Read the input file
    text = read_text_file(input_file)
    
    # Generate chunk sizes
    chunk_sizes = generate_chunk_sizes()
    print(f"Generated chunk sizes: {chunk_sizes}")
    
    # Extract chunks
    chunks = extract_chunks(text, chunk_sizes)
    
    # Save to CSV
    save_to_csv(chunks, output_file)
    
    print(f"Generated {len(chunks)} chunks and saved to {output_file}")

if __name__ == "__main__":
    main() 