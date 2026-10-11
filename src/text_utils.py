"""Small helpers for working with Arabic and English text."""
import re

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

# Arabic diacritics (tashkeel) and tatweel (the stretching character ـ)
MARKS = re.compile("[\u064B-\u065F\u0670\u0640]")
# Unify letter shapes so "الأرباح" and "الارباح" are treated as the same word.
LETTER_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي"})
ARABIC_LETTERS = re.compile("[\u0600-\u06FF]")

# Common Arabic one-letter prefixes: و (and), ب (with), ل (for), ال (the) ...
PREFIXES = ["ال", "وال", "بال", "لل", "و", "ب", "ل"]


def has_arabic(text):
    return bool(ARABIC_LETTERS.search(str(text)))


def remove_marks(text):
    return MARKS.sub("", text)


def normalize_text(text):
    """Lowercase, convert digits to 0-9, remove diacritics and unify Arabic letters."""
    text = str(text).lower().translate(ARABIC_DIGITS).translate(PERSIAN_DIGITS)
    text = remove_marks(text).translate(LETTER_MAP)
    return " ".join(text.split())


def words_of(text):
    """Split normalized text into words (Arabic or English)."""
    return re.findall(r"[\w-]+", normalize_text(text))
