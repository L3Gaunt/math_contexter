import csv
import os
import time
import random
from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables
load_dotenv()

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASEURL", "https://us.cloud.langfuse.com")
)

def upload_with_backoff(dataset_name, input_data, expected_output, max_retries=5, base_delay=1):
    """Upload a dataset item with exponential backoff for rate limiting."""
    for attempt in range(max_retries):
        try:
            langfuse.create_dataset_item(
                dataset_name=dataset_name,
                input=input_data,
                expected_output=expected_output
            )
            return True
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                print(f"Error uploading item: {str(e)}")
                return False

def upload_dataset(csv_path, dataset_name):
    """
    Upload a dataset from a CSV file to Langfuse.
    
    Args:
        csv_path (str): Path to the CSV file
        dataset_name (str): Name of the dataset in Langfuse
    """
    print(f"Uploading dataset from {csv_path} to Langfuse as '{dataset_name}'...")
    
    # Create dataset in Langfuse if it doesn't exist
    try:
        dataset = langfuse.get_dataset(dataset_name)
        print(f"Dataset '{dataset_name}' already exists.")
    except Exception:
        dataset = langfuse.create_dataset(name=dataset_name)
        print(f"Created new dataset '{dataset_name}'.")
    
    # Read data from CSV
    items = []
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            items.append({
                'input': {'text': row['text'], 'word_count': int(row['word_count'])},
                'expected_output': None  # No expected output for this dataset
            })
    
    # Upload items to Langfuse one by one with rate limiting
    if items:
        success_count = 0
        for i, item in enumerate(items):
            if upload_with_backoff(
                dataset_name=dataset_name,
                input_data=item['input'],
                expected_output=item['expected_output']
            ):
                success_count += 1
                
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(items)} items. Successfully uploaded: {success_count}")
            
            # Add small delay between requests to avoid hitting rate limits
            time.sleep(0.5)
        
        print(f"Uploaded {success_count}/{len(items)} items to dataset '{dataset_name}'.")
    else:
        print("No items found in the CSV file.")

if __name__ == "__main__":
    csv_path = "ag_split_test.csv"
    dataset_name = "math_contexter_chunks"
    upload_dataset(csv_path, dataset_name) 