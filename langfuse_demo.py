import asyncio
import os
from dotenv import load_dotenv
from langfuse import Langfuse
from src.context_builder import main as context_builder_main

# Load environment variables
load_dotenv()

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASEURL", "https://us.cloud.langfuse.com")
)

# Sample mathematical text
SAMPLE_TEXT = """
of order 1. But this is a contradiction to the residue theorem of complex analysis: the sum
of the residues of any rational (or meromorphic) differential form on a compact Riemann
surface is zero, but in our case we have ∑Q∈X resQ(ϕ·α) = resP(ϕ·α) 6= 0.
Step 3. We claim that
χ(D) ≥ degD+1−g
for all divisors D.
"""

async def demo_langfuse_integration():
    """Demonstrate Langfuse integration."""
    # Create a root trace for the demo
    trace = langfuse.trace(
        name="langfuse_demo",
        metadata={"demo_version": "1.0"}
    )

    try:
        # Log a simple event
        trace.event(
            name="demo_started",
            metadata={"status": "running"}
        )

        # Process text with context builder (creates its own traces)
        span = trace.span(name="run_context_builder")
        await context_builder_main(SAMPLE_TEXT, output_file="demo_output.txt", concurrency_limit=2)
        span.end()

        # Log completion event
        trace.event(
            name="demo_completed",
            metadata={"status": "success"}
        )

        # Update trace status
        trace.update(status="success")
        
        print("Demo completed successfully!")
        print("Check the Langfuse dashboard to see the traces.")
        
    except Exception as e:
        # Log error event
        trace.event(
            name="demo_error",
            metadata={"error": str(e)}
        )
        
        # Update trace status
        trace.update(status="error", metadata={"error": str(e)})
        
        print(f"Demo failed with error: {str(e)}")
        raise
    
    finally:
        # Ensure all pending requests are sent
        langfuse.flush()

if __name__ == "__main__":
    asyncio.run(demo_langfuse_integration()) 