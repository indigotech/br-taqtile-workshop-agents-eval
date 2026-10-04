import unicodedata


def normalize_name(text: str) -> str:
    """Case- and accent-insensitive form of a name, so "sao paulo" matches
    "São Paulo". Compared in Python because SQLite's lower() only folds ASCII."""
    decomposed = unicodedata.normalize("NFKD", " ".join(text.split()).casefold())
    return "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
