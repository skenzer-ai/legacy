import unittest
import os
import shutil
import sys
import subprocess
from src.retrieval.retriever import KnowledgeRetriever
from src.scripts.build_indices import main as build_indices
from langchain_core.documents import Document

class TestRetrievalV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary directory for test indices
        cls.test_index_dir = "test_dist"
        os.makedirs(cls.test_index_dir, exist_ok=True)

        # Build the indices in the test directory
        # Run the build script with the correct PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        subprocess.run([
            "python", "src/scripts/build_indices.py",
            "--output_dir", cls.test_index_dir
        ], check=True, env=env)

        # Initialize the retriever with the test indices
        cls.retriever = KnowledgeRetriever(index_dir=cls.test_index_dir)

    @classmethod
    def tearDownClass(cls):
        # Clean up the temporary directory
        shutil.rmtree(cls.test_index_dir)

    def test_create_incident_retrieval(self):
        """
        Tests that the system can retrieve the 'create incident' endpoint.
        """
        query = "create incident"
        results = self.retriever.search(query)

        self.assertGreater(len(results), 0, "Should retrieve at least one result")

        # Check if the top result is the correct one
        top_result_content = results[0]
        self.assertIn("create_incident", str(top_result_content))

    def test_fused_results(self):
        """
        Tests that the system returns a mix of API and document results.
        """
        query = "how to create an incident"
        results = self.retriever.search(query)

        self.assertGreater(len(results), 0, "Should retrieve at least one result")

        # Print the types of the results
        for doc in results:
            print(type(doc))

        # Check for a mix of results
        has_api_result = any(isinstance(doc, dict) and "path" in doc for doc in results)
        has_doc_result = any(isinstance(doc, Document) for doc in results)

        self.assertTrue(has_api_result, "Should have at least one API result")
        self.assertTrue(has_doc_result, "Should have at least one document result")

if __name__ == '__main__':
    unittest.main()