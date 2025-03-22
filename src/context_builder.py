import asyncio
import aiohttp
from dotenv import load_dotenv
import os
import json
from typing import List, Dict
import re

# Load API key from .env
load_dotenv()
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
if not OPENROUTER_KEY:
    raise ValueError("OPENROUTER_KEY not found in .env")

# something like https://arxiv.org/pdf/2304.10428
# System prompt for the LLM
SYSTEM_PROMPT = """You are a specialized mathematical text analyzer. Your task is to process mathematical text and annotate specialized mathematical elements with markers.

For each chunk of mathematical text you receive:
1. Identify all specialized mathematical elements including:
   - Mathematical terms (e.g., "residue theorem", "meromorphic", "divisor")
   - Mathematical symbols (e.g., "χ(D)", "∑", "∈")
   - Variable references (e.g., "D", "P", "X", "α")
   - References to theorems, definitions, lemmas, examples (e.g., "example 7.7.2")

2. Add the marker "@@@ " before each identified element and " &&&" after it.

3. Do NOT annotate common English words or general descriptive terms unless they have a specific mathematical meaning in context.

4. Preserve all original text, spacing, and formatting - only add the markers.

5. Return the annotated text directly as plain text.

Example input:
"of order 1. But this is a contradiction to the residue theorem of complex analysis: the sum of the residues"

Example output:
"of @@@ order &&& 1. But this is a contradiction to the @@@ residue theorem &&& of @@@ complex analysis &&&: the @@@ sum &&& of the @@@ residues &&&"
"""

alt_sysprompt = """You are a mathematical reference detector that identifies usage of previously defined concepts. Process the input as follows:

1. Find ALL references to numbered items (Definitions, Theorems, etc.) and specialized notation
2. Wrap each reference with @@@ before and &&& after, including:
   - Cross-references like "lemma 2.1.8"
   - Symbol reuses (OX, Rp when used post-definition)
   - Theorem/Proposition numbers in proofs
   - Nested references within other definitions
3. Handle multiple reference types:
   - Explicit: "by Proposition 5.1.12(i)"
   - Implicit: "the sheaf OX (see definition 2.1.5)"
   - Symbolic: "ϕp ∈ Rp"
4. Do NOT annotate definitions when they are introduced for the first time.
5. Example wrapping:
...we expect from @@@affine varieties (see definition 2.1.5)&&&, @@@remark 2.1.6&&&, and @@@proposition 2.1.10)&&&..."""

def split_text_into_chunks(text: str, chunk_size: int = 300, overlap: int = 150) -> List[tuple[str, int, int]]:
    """Split text into chunks with specified size and overlap, preserving whitespace."""
    tokens = re.split(r'(\s+)', text)
    pairs = [(tokens[i], tokens[i+1] if i+1 < len(tokens) else '') for i in range(0, len(tokens), 2) if tokens[i].strip()]
    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(pairs), step):
        end = min(start + chunk_size, len(pairs))
        chunk_pairs = pairs[start:end]
        chunk_text = ''.join(word + ws for word, ws in chunk_pairs)
        start_idx = text.find(chunk_text)
        end_idx = start_idx + len(chunk_text)
        chunks.append((chunk_text, start_idx, end_idx))
    return chunks

async def call_llm_async(chunk: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> str | None:
    """Call the LLM asynchronously to annotate the chunk with math references."""
    async with semaphore:
        prompt = f'''
{chunk}'''
        data = {
            "model": "qwen/qwen-2.5-7b-instruct",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        }
        headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers) as resp:
                response_json = await resp.json()
                content = response_json['choices'][0]['message']['content']
                return content
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return None

async def call_llm_with_retry(chunk: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, max_retries: int = 3) -> str | None:
    """Call LLM with retries if validation fails."""
    for attempt in range(max_retries):
        result = await call_llm_async(chunk, session, semaphore)
        if result:
            return result
        print(f"Failed to process chunk: {chunk[:50]}... Retrying ({attempt+1}/{max_retries})")
    print(f"Failed to process chunk after {max_retries} attempts: {chunk[:50]}...")
    return None

async def main(text: str, output_file: str = "output.txt", concurrency_limit: int = 5):
    """Process mathematical text and write annotated output to file."""
    # Split text into chunks
    chunks = split_text_into_chunks(text)
    
    # Process chunks in parallel
    semaphore = asyncio.Semaphore(concurrency_limit)
    async with aiohttp.ClientSession() as session:
        tasks = [call_llm_with_retry(chunk, session, semaphore) for chunk, _, _ in chunks]
        results = await asyncio.gather(*tasks)
    
    # Filter and report failed chunks
    valid_results = [r for r in results if r is not None]
    if len(valid_results) < len(chunks):
        print(f"Warning: {len(chunks) - len(valid_results)} chunks failed to process.")
    
    # Combine results in order
    processed_text = ""
    last_end_idx = 0
    
    for i, (result, (_, start_idx, end_idx)) in enumerate(zip(valid_results, chunks)):
        # If there's a gap, use original text
        if start_idx > last_end_idx:
            processed_text += text[last_end_idx:start_idx]
        
        # If there's overlap with previous chunk, skip the overlapping part
        if i > 0 and start_idx < last_end_idx:
            overlap_size = last_end_idx - start_idx
            if overlap_size < len(result):
                processed_text += result[overlap_size:]
        else:
            processed_text += result
        
        last_end_idx = end_idx
    
    # Add any remaining text
    if last_end_idx < len(text):
        processed_text += text[last_end_idx:]
    
    # Write to file
    with open(output_file, "w") as f:
        f.write(processed_text)

# Example usage
if __name__ == "__main__":
    # Replace with your mathematical text (e.g., from OCR or LaTeX)
    sample_text = '''
of order 1. But this is a contradiction to the residue theorem of complex analysis: the sum
of the residues of any rational (or meromorphic) differential form on a compact Riemann
surface is zero, but in our case we have ∑Q∈X resQ(ϕ·α) = resP(ϕ·α) 6= 0.
Step 3. We claim that
χ(D) ≥ degD+1−g
for all divisors D. Note that we can choose points P1,...,Pr such that D+P1 +···+Pr
is
precisely the intersection divisor of X with a certain number n of hyperplanes: for every
point in D we just choose a hyperplane through that point and add all other intersection
points with X to the Pi
. This then means that O(D + P1 + ··· + Pr) = O(n). By possibly
adding more intersection points of X with hyperplanes we can make n arbitrarily large. So
by example 7.7.2 we find that
'''
    asyncio.run(main(sample_text))