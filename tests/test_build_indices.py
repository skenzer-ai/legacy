import os
import subprocess
import unittest
import pickle
from pyroaring import BitMap as Roaring

class TestBuildIndices(unittest.TestCase):
    """
    Tests for the offline index building script.
    """
    def setUp(self):
        """
        Set up the test environment by running the build script.
        """
        self.output_dir = "dist_test"
        self.api_spec_path = "user_docs/infraon-api.json"
        self.synonyms_path = "src/retrieval/synonyms.json"

        # Ensure the output directory is clean before running
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                os.remove(os.path.join(self.output_dir, f))
        else:
            os.makedirs(self.output_dir)

        # Run the build script with the correct PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        subprocess.run([
            "python", "src/scripts/build_indices.py",
            "--api_spec_path", self.api_spec_path,
            "--synonyms_path", self.synonyms_path,
            "--output_dir", self.output_dir
        ], check=True, env=env)

    def test_output_files_exist(self):
        """
        Test if all the expected output files are created.
        """
        expected_files = [
            "bitmap_index.bin",
            "tfidf_vectorizer.pkl",
            "tfidf_matrix.pkl",
            "full_text_cache.pkl"
        ]
        for f in expected_files:
            self.assertTrue(os.path.exists(os.path.join(self.output_dir, f)))

    def test_bitmap_index_integrity(self):
        """
        Perform a basic integrity check on the bitmap index.
        """
        bitmap_path = os.path.join(self.output_dir, "bitmap_index.bin")
        with open(bitmap_path, 'rb') as f:
            # Load the entire index
            inverted_index = pickle.load(f)
            self.assertIsInstance(inverted_index, dict)
            # Check the first item
            first_token = next(iter(inverted_index))
            self.assertIsInstance(inverted_index[first_token], Roaring)

    def test_pickle_files_loadable(self):
        """
        Test if the pickle files can be loaded without errors.
        """
        pickle_files = [
            "tfidf_vectorizer.pkl",
            "tfidf_matrix.pkl",
            "full_text_cache.pkl"
        ]
        for f_name in pickle_files:
            path = os.path.join(self.output_dir, f_name)
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.assertIsNotNone(data)

if __name__ == '__main__':
    unittest.main()