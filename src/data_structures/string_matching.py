"""Custom KMP string search."""

class StringMatcher:
    """String matching algorithms for search systems."""

    @staticmethod
    def _compute_lps(pattern):
        """Build the KMP longest-prefix-suffix table."""
        lps = [0] * len(pattern)
        length = 0
        i = 1

        while i < len(pattern):
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            elif length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1

        return lps

    @staticmethod
    def prepare_pattern(pattern):
        """Prepare a search pattern and its KMP table."""
        normalized = str(pattern).lower()
        return normalized, StringMatcher._compute_lps(normalized)

    @staticmethod
    def kmp_search_prepared(text, pattern, lps):
        """Run KMP search with a prepared pattern."""
        if not pattern:
            return True

        text = str(text).lower()
        i = 0
        j = 0

        while i < len(text):
            if pattern[j] == text[i]:
                i += 1
                j += 1

                if j == len(pattern):
                    return True
            elif j != 0:
                j = lps[j - 1]
            else:
                i += 1

        return False

    @staticmethod
    def kmp_search(text, pattern):
        """Return whether text contains the pattern."""
        normalized_pattern, lps = StringMatcher.prepare_pattern(pattern)
        return StringMatcher.kmp_search_prepared(text, normalized_pattern, lps)
