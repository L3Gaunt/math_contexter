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

# System prompt for the LLM
SYSTEM_PROMPT = """
You are an assistant that converts mathematical text into a structured JSON format. Identify theorems, definitions, references, and other mathematical concepts, and represent them as:

{
  "context": {
    "type": "theorem",  // e.g., "theorem", "definition", "lemma"
    "name": "theorem 3.3.",
    "content": [
      {"type": "text", "value": "Theorem 3.3. "},
      {
        "type": "concept_definition",
        "name": "X",
        "symbol_type": "symbol",
        "id": "def_x",
        "content": [
          {"type": "text", "value": "Let X be a "},
          {"type": "reference", "to": "unknown", "value": "locally free"},
          {"type": "text", "value": " "},
          {"type": "reference", "to": "unknown", "value": "sheaf"}
        ]
      },
      {"type": "text", "value": ". Then "},
      {"type": "reference", "to": "def_x", "value": "X"},
      {"type": "text", "value": " is xyz..."}
    ]
  }
}

Guidelines:
- Assign unique IDs to definitions (e.g., "def_x") and reference them.
- Use "to": "unknown" for undefined terms.
- Ensure the "content" list reconstructs the original text when "value" fields are concatenated.
- Escape all strings properly in JSON.
"""

def split_text_into_chunks(text: str, chunk_size: int = 100, overlap: int = 70) -> List[tuple[str, int, int]]:
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

async def call_llm_async(chunk: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> Dict | None:
    """Call the LLM asynchronously to convert chunk to JSON."""
    async with semaphore:
        prompt = f"Convert the following mathematical text into the specified JSON format:\n\n{chunk}"
        data = {
            "model": "qwen/qwen-2.5-7b-instruct",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers) as resp:
                response_json = await resp.json()
                content = response_json['choices'][0]['message']['content']
                return json.loads(content)
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return None

async def call_llm_with_retry(chunk: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, max_retries: int = 3) -> Dict | None:
    """Call LLM with retries if validation fails."""
    for attempt in range(max_retries):
        json_obj = await call_llm_async(chunk, session, semaphore)
        if json_obj and validate_json(json_obj, chunk):
            return json_obj
        print(f"Validation failed for chunk: {chunk[:50]}... Retrying ({attempt+1}/{max_retries})")
    print(f"Failed to process chunk after {max_retries} attempts: {chunk[:50]}...")
    return None

def split_content_at(content: List[Dict], skip_length: int) -> tuple[List[Dict], List[Dict]]:
    """Split content list at a character position, returning before and after parts."""
    accumulated = 0
    for i, obj in enumerate(content):
        if "value" in obj:
            val_len = len(obj["value"])
            if accumulated + val_len <= skip_length:
                accumulated += val_len
            else:
                if obj["type"] == "text" and skip_length - accumulated < val_len:
                    split_pos = skip_length - accumulated
                    remaining_obj = obj.copy()
                    remaining_obj["value"] = obj["value"][split_pos:]
                    return content[:i], [remaining_obj] + content[i+1:]
                return content[:i], content[i:]
    return content, []

async def main(text: str, output_file: str = "output.json", concurrency_limit: int = 5):
    """Process mathematical text and write structured JSON to file."""
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
    
    # Unify overlapping content
    overall_content = []
    for i, (json_obj, (_, start_idx, end_idx)) in enumerate(zip(valid_results, chunks)):
        content = json_obj["context"]["content"]
        if i == 0:
            overall_content.extend(content)
        else:
            skip_length = chunks[i-1][2] - start_idx
            if skip_length > 0:
                _, remaining = split_content_at(content, skip_length)
                overall_content.extend(remaining)
            else:
                overall_content.extend(content)
    
    # Write to file
    with open(output_file, "w") as f:
        json.dump({"content": overall_content}, f, indent=2)

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