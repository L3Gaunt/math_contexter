import asyncio
import os
from dotenv import load_dotenv
from src.context_builder import main as context_builder_main

# Load environment variables
load_dotenv()

# Test text
sample_text = '''
of order 1. But this is a contradiction to the residue theorem of complex analysis: the sum
of the residues of any rational (or meromorphic) differential form on a compact Riemann
surface is zero, but in our case we have ∑Q∈X resQ(ϕ·α) = resP(ϕ·α) 6= 0.
'''

async def test_context_builder():
    """Test the context builder with Langfuse integration."""
    print("Testing context builder with Langfuse integration...")
    await context_builder_main(sample_text, output_file="test_output.txt", concurrency_limit=1)
    print("Context builder test completed.")
    print("Check the Langfuse dashboard to see the traces.")

if __name__ == "__main__":
    asyncio.run(test_context_builder()) 