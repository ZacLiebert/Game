class StringMatcher:
    """
    String matching algorithms for the search system.
    Implements KMP (Knuth-Morris-Pratt) to find partial matches in item names or descriptions.
    """

    @staticmethod
    def _compute_lps(pattern):
        """
        Computes the Longest Prefix Suffix (LPS) array for the KMP algorithm.
        """
        lps = [0] * len(pattern)
        length = 0
        i = 1

        while i < len(pattern):
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps

    @staticmethod
    def kmp_search(text, pattern):
        """
        Finds if the pattern exists within the text using the KMP algorithm.
        
        Args:
            text (str): The main string to search within (e.g., item name).
            pattern (str): The substring to look for (e.g., search bar input).
            
        Returns:
            bool: True if the pattern is found within the text, False otherwise.
        """
        if not pattern:
            return True
            
        # Convert to lowercase for case-insensitive searching
        text = text.lower()
        pattern = pattern.lower()
        
        lps = StringMatcher._compute_lps(pattern)
        i = 0  # index for text
        j = 0  # index for pattern

        while i < len(text):
            if pattern[j] == text[i]:
                i += 1
                j += 1

            if j == len(pattern):
                return True
            elif i < len(text) and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        return False