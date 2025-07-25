import json
import sys
sys.path.append(".")
from src.retrieval.retriever import KnowledgeRetriever

def main():
    """
    An interactive script to test the retrieval system.
    """
    # First, ensure the indices are built
    print("Building retrieval indices...")
    import subprocess
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    # Fix: Remove cwd argument so path is correct
    subprocess.run(["python", "src/scripts/build_indices.py"], check=True, env=env)
    print("Indices built successfully.")

    retriever = KnowledgeRetriever()
    print("KnowledgeRetriever initialized. You can now start querying.")
    print("Type 'exit' to quit.")

    while True:
        query = input("\nEnter your query: ")
        if query.lower() == 'exit':
            break

        results = retriever.search(query)

        if not results:
            print("No results found.")
            continue

        print("\n--- Top 5 Results ---")
        for i, doc in enumerate(results):
            print(f"\nResult {i+1}:")
            if isinstance(doc, dict):
                # API result
                print(f"  Path: {doc.get('path', 'N/A')}")
                print(f"  Method: {doc.get('method', 'N/A')}")
                print(f"  Operation ID: {doc.get('operationId', 'N/A')}")
                print(f"  Tags: {doc.get('tags', 'N/A')}")
            else:
                # Document result
                print(doc.page_content)

        print("\n----------------------")
        accuracy = input("Was this result accurate? (yes/no/skip): ")
        # Here you could add logic to log the accuracy feedback
        print("Thank you for your feedback!")


if __name__ == "__main__":
    main()