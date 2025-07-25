import re
from nltk.stem import PorterStemmer

class CanonicalTokenizer:
    def __init__(self):
        self.stemmer = PorterStemmer()
        # Improved regex to split on non-alphanumeric characters and camelCase
        self.pattern = re.compile(r'[\W_]+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')

    def tokenize(self, text):
        """
        Splits text by non-alphanumeric characters and camelCase, then stems them.
        """
        tokens = self.pattern.split(text)
        return [self.stemmer.stem(token.lower()) for token in tokens if token]