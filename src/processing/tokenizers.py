import re
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

class CanonicalTokenizer:
    """
    A tokenizer that splits text based on common programming and natural language
    delimiters, converts to snake_case, and stems the resulting tokens.
    """
    def __init__(self):
        self.stemmer = PorterStemmer()
        # Regex to find camelCase, snake_case, kebab-case, and space-separated words
        self.split_pattern = re.compile(r'[\s_-]+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')

    def _decamelize(self, text: str) -> str:
        """Converts a camelCase string to snake_case."""
        text = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text).lower()

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenizes and stems the input text.

        Args:
            text: The string to tokenize.

        Returns:
            A list of stemmed tokens in lowercase.
        """
        if not text:
            return []
        
        # Use humps to handle camelCase and other cases gracefully
        decamelized_text = self._decamelize(text)
        
        # Split based on snake_case and other delimiters
        tokens = self.split_pattern.split(decamelized_text)
        
        # Stem and lowercase each token
        stemmed_tokens = [self.stemmer.stem(token.lower()) for token in tokens if token]
        
        return stemmed_tokens
