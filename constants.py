GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_MODEL_BACKUP = "gemini-3.1-flash-lite-preview"

DEFAULT_PROVIDER = "exa"
DEFAULT_FALLBACK_PROVIDER = "gemini"
DEFAULT_EXA_MODEL = "auto"
DEFAULT_EXA_NUM_RESULTS = 10
DEFAULT_EXA_MAX_RETRIES = 3

REQUIRED_PROFILE_FIELDS = [
    "slug",
    "name",
    "company",
    "pricing",
    "pricingDetail",
    "description",
    "keyFeatures",
    "bestFor",
    "notIdealFor",
    "recentUpdates",
    "verdict",
    "tags",
    "lastUpdated",
]

VALID_PRICING = {"free", "freemium", "paid", "open-source"}
