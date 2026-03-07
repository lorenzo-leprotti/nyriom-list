"""
AEROCOM 2025 Delegate Prioritization - Configuration
=====================================================

All scoring rules, bucket definitions, API settings, and file paths
for the Nyriom Technologies / NyrionPlex materials sales pipeline.

Nyriom Technologies is a Berlin-based bio-polymer composites startup.
NyrionPlex is their flagship advanced composite material system.
AEROCOM 2025 is a fictional aerospace composites conference in Toulouse.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# API Keys
# =============================================================================
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# =============================================================================
# File Paths
# =============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

INPUT_CSV = DATA_DIR / "aerocom_2025_delegates.csv"

# Checkpoint files
CHECKPOINT1_FILE = OUTPUT_DIR / "checkpoint1_filtered.xlsx"
CHECKPOINT2_RESEARCHED = OUTPUT_DIR / "checkpoint2_researched.xlsx"
CHECKPOINT2_SCORED = OUTPUT_DIR / "checkpoint2_scored.xlsx"
CHECKPOINT3_ENHANCED = OUTPUT_DIR / "checkpoint3_enhanced.xlsx"
FINAL_OUTPUT = OUTPUT_DIR / "AEROCOM_2025_FINAL_TOP50.xlsx"

# Log files
RESEARCH_LOG = LOGS_DIR / "research_log.json"
ENHANCE_LOG = LOGS_DIR / "enhance_log.json"

# =============================================================================
# Perplexity API Configuration
# =============================================================================
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
RESEARCHER_MODEL = "sonar"
ENHANCER_MODEL = "sonar-pro"
RESEARCH_RATE_LIMIT = 2   # seconds between calls (sonar)
ENHANCE_RATE_LIMIT = 3    # seconds between calls (sonar-pro)

# =============================================================================
# Research Mode
# =============================================================================
# Single-pass (default for demo): one research call per prospect
# Dual-pass: gather + verify (doubles API calls but improves accuracy)
DUAL_PASS = False

# =============================================================================
# Enhancement Configuration
# =============================================================================
ENHANCE_TOP_N = 60  # Number of top prospects to enhance with Sonar Pro

# =============================================================================
# Column Mappings
# =============================================================================
COL_FIRST_NAME = "First Name"
COL_LAST_NAME = "Last Name"
COL_JOB_TITLE = "Job Title"
COL_COMPANY = "Company Name"

# =============================================================================
# COMPANY-TYPE BUCKETS (for step1_buckets.py)
# =============================================================================
# Each bucket: label, relevance level, and keyword patterns to match
# Matching is case-insensitive against Company Name

COMPANY_BUCKETS = {
    "A": {
        "label": "Aerospace OEM",
        "relevance": "HIGH",
        "patterns": [
            "airbus", "boeing", "embraer", "bombardier",
            "dassault aviation", "lockheed martin", "northrop grumman",
            "raytheon", "bae systems", "leonardo",
            "textron aviation", "gulfstream", "cessna",
            "pilatus", "saab", "kawasaki heavy",
            "mitsubishi heavy", "comac",
        ],
    },
    "B": {
        "label": "Tier 1 Supplier",
        "relevance": "HIGH",
        "patterns": [
            "safran", "collins aerospace", "raytheon technologies",
            "spirit aerosystems", "ge aerospace", "ge aviation",
            "rolls-royce", "pratt & whitney", "honeywell aerospace",
            "moog", "parker hannifin", "parker aerospace",
            "curtiss-wright", "triumph group", "howmet",
            "transdigm", "heico", "meggitt", "senior plc",
            "woodward", "ducommun",
        ],
    },
    "C": {
        "label": "Tier 2-3 Specialty Manufacturer",
        "relevance": "HIGH",
        "patterns": [
            # Named composites/specialty manufacturers
            "albany international", "albany engineered",
            "kaman aerospace", "hexion", "teledyne",
            "aerojet rocketdyne", "orbital atk",
            "premium aerotec", "stelia aerospace",
            "daher", "latecoere", "figeac aero",
            "aernnova", "aciturri", "gkn aerospace",
            "fokker", "avio aero", "itp aero",
            "liebherr aerospace", "facc", "ruag",
            # Broad catch-alls
            "composites", "composite", "aerospace",
            "aerostructures", "tooling", "prepreg",
            "autoclave", "fiber placement",
            "aerospace manufacturing",
        ],
    },
    "D": {
        "label": "Material Supplier / Chemical Co.",
        "relevance": "CRITICAL",
        "patterns": [
            "hexcel", "toray", "solvay", "basf",
            "dupont", "arkema", "teijin", "covestro",
            "huntsman", "cytec", "mitsubishi chemical",
            "sabic", "evonik", "lanxess", "dow",
            "3m", "henkel", "sgl carbon", "zoltek",
            "gurit", "renegade materials", "tencate",
            "park electrochemical", "isola group",
            "advanced composites", "carbon fiber",
            "resin", "polymer", "chemical",
            "material supplier", "materials",
            "adhesive", "coating",
        ],
    },
    "E": {
        "label": "Airline / MRO",
        "relevance": "MEDIUM-HIGH",
        "patterns": [
            "lufthansa technik", "air france industries",
            "st aerospace", "haeco", "aar corp",
            "turkish technic", "delta techops",
            "emirates engineering", "etihad engineering",
            "aeroplex", "aviall",
            "airline", "airlines", "airways",
            "mro", "maintenance", "overhaul",
            "repair station", "fleet management",
        ],
    },
    "F": {
        "label": "Investment / PE",
        "relevance": "MEDIUM",
        "patterns": [
            "carlyle", "blackstone", "brookfield",
            "cerberus", "kkr", "apollo",
            "capital", "investment", "investor",
            "private equity", "equity partners",
            "partners", "fund ", "funds",
            "advisors", "advisory", "ventures",
            "asset management",
        ],
    },
    "G": {
        "label": "Engineering / Design Services",
        "relevance": "MEDIUM",
        "patterns": [
            "altair", "ansys", "dassault systemes",
            "siemens digital", "msc software",
            "engineering services", "design services",
            "simulation", "cae ", "fea ",
            "structural analysis", "consulting engineer",
            "test laboratory", "certification",
        ],
    },
    "H": {
        "label": "Legal / Consulting / Finance",
        "relevance": "EXCLUDE",
        "patterns": [
            "law firm", "llp", "legal", "attorney",
            "pllc", "law office", "law group",
            "consulting group", "consultants",
            "management consulting", "strategy consulting",
            "bank", "banking", "insurance",
            "accounting", "audit",
        ],
    },
    "I": {
        "label": "Media / Trade / Other",
        "relevance": "EXCLUDE",
        "patterns": [
            "composites world", "jec group",
            "aviation week", "flight global",
            "media", "magazine", "publishing", "news",
            "trade show", "event management",
            "technology", "software", "saas",
            "it services",
        ],
    },
    "J": {
        "label": "Academic / Research Institute",
        "relevance": "EXCLUDE",
        "patterns": [
            "university", "college", "school of",
            "institute of", "academic", "student",
            "fraunhofer", "dlr", "onera", "nasa",
            "national laboratory",
        ],
    },
}

# =============================================================================
# JOB-FUNCTION BUCKETS (for step1_buckets.py)
# =============================================================================

FUNCTION_BUCKETS = {
    "1": {
        "label": "Materials Engineering / R&D",
        "relevance": "CRITICAL",
        "patterns": [
            "materials engineer", "composites engineer",
            "materials science", "r&d", "research and development",
            "polymer engineer", "composite",
            "materials technology",
        ],
    },
    "2": {
        "label": "Procurement / Supply Chain",
        "relevance": "CRITICAL",
        "patterns": [
            "procurement", "purchasing", "supply chain",
            "sourcing", "supply management",
            "vendor", "supplier",
        ],
    },
    "3": {
        "label": "Manufacturing / Production",
        "relevance": "HIGH",
        "patterns": [
            "manufacturing", "production",
            "plant manager", "factory",
            "process engineer", "industrial engineer",
        ],
    },
    "4": {
        "label": "Sustainability / ESG",
        "relevance": "HIGH",
        "patterns": [
            "sustainability", "esg", "environment",
            "circular economy", "green", "carbon",
            "climate", "lifecycle",
        ],
    },
    "5": {
        "label": "C-Suite",
        "relevance": "HIGH",
        "patterns": [
            "ceo", "president", "chairman", "chairwoman",
            "founder", "owner", "principal",
            "proprietor", "chief executive",
            "chief operating", "chief financial",
            "chief commercial", "chief marketing",
            "chief revenue", "chief technology",
        ],
    },
    "6": {
        "label": "SVP / EVP / MD",
        "relevance": "HIGH",
        "patterns": [
            "svp", "evp", "senior vice president",
            "executive vice president",
            "managing director",
        ],
    },
    "7": {
        "label": "VP",
        "relevance": "MEDIUM-HIGH",
        "patterns": [
            "vice president", "vp",
        ],
    },
    "8": {
        "label": "Director",
        "relevance": "MEDIUM",
        "patterns": [
            "director", "senior director",
        ],
    },
    "9": {
        "label": "Quality / Certification",
        "relevance": "MEDIUM",
        "patterns": [
            "quality", "certification",
            "nadcap", "as9100", "compliance",
            "inspection", "ndt",
        ],
    },
    "10": {
        "label": "Other / Junior / Student",
        "relevance": "EXCLUDE",
        "patterns": [
            "student", "analyst", "associate",
            "attorney", "lawyer", "counsel",
            "editor", "reporter", "journalist",
            "intern", "ambassador", "coordinator",
            "assistant", "receptionist",
            "accountant", "paralegal",
        ],
    },
}

# =============================================================================
# Company bucket base scores (used in step3_score.py too)
# =============================================================================
COMPANY_BUCKET_SCORES = {
    "D": 40,   # Material Supplier / Chemical Co. — CRITICAL
    "A": 35,   # Aerospace OEM
    "B": 30,   # Tier 1 Supplier
    "C": 30,   # Tier 2-3 Specialty Manufacturer
    "E": 20,   # Airline / MRO
    "F": 5,    # Investment / PE
    "G": 10,   # Engineering / Design Services
}

# Function bucket base scores
FUNCTION_BUCKET_SCORES = {
    "1": 25,   # Materials Engineering / R&D — CRITICAL
    "2": 25,   # Procurement / Supply Chain — CRITICAL
    "3": 12,   # Manufacturing / Production
    "4": 12,   # Sustainability / ESG
    "5": 10,   # C-Suite (high, but need company match)
    "6": 8,    # SVP / EVP / MD
    "7": 6,    # VP
    "8": 4,    # Director
    "9": 5,    # Quality / Certification
}

# =============================================================================
# TITLE SCORING (0-30 points)
# =============================================================================

TITLE_SCORES = {
    # C-Suite (30 points)
    "ceo": 30, "president": 30, "chairman": 30, "chairwoman": 30,
    "founder": 30, "owner": 30, "principal": 30, "proprietor": 30,

    # C-Suite Other (28 points)
    "coo": 28, "cmo": 28, "cfo": 28, "cto": 28, "chief": 28,
    "chief technology officer": 30,  # CTO gets top score in materials

    # Materials-specific titles (28 points)
    "chief technology": 30,
    "head of materials": 28,
    "head of procurement": 28,
    "head of supply chain": 28,
    "head of r&d": 28,

    # Senior Executive (25 points)
    "svp": 25, "evp": 25, "managing director": 25,
    "senior vice president": 25, "executive vice president": 25,

    # VP Level (22 points)
    "vp": 22, "vice president": 22, "regional vp": 22,

    # Director Level Multi-Scope (20 points)
    "global director": 20, "group director": 20,
    "corporate director": 20,

    # General Manager (15 points)
    "general manager": 15, "gm": 15,

    # Director Level (12 points)
    "director": 12,

    # Senior Manager (10 points)
    "senior manager": 10,

    # Manager Level (8 points)
    "manager": 8, "assistant director": 8,

    # Senior Engineer / Lead (7 points)
    "senior engineer": 7, "lead engineer": 7, "principal engineer": 7,

    # Junior (5 points)
    "coordinator": 5, "supervisor": 5, "specialist": 5,
    "engineer": 5,

    # Entry Level (3 points)
    "assistant": 3, "associate": 3,
}

# =============================================================================
# MATERIALS ADOPTION PROXIMITY SCORING (0-25 points)
# The key differentiator for composites/bio-polymer sales pipeline
# =============================================================================

# Applied based on job title patterns
MATERIALS_ADOPTION_TITLE_SCORES = {
    "materials engineer": 25,
    "composites engineer": 25,
    "materials science": 25,
    "materials technology": 25,
    "procurement": 25,
    "purchasing": 25,
    "supply chain": 25,
    "sourcing": 25,
    "supply management": 25,
    "r&d": 20,
    "research and development": 20,
    "manufacturing": 15,
    "production": 15,
    "process engineer": 15,
    "sustainability": 12,
    "quality": 12,
    "certification": 12,
    "structural engineer": 12,
    "design engineer": 12,
}

# Applied based on company being a material supplier (bucket D)
MATERIALS_SUPPLIER_ORG_BONUS = 20

# From research data
MATERIAL_SPEC_INFLUENCE_BONUS = 10
MATERIALS_ADOPTION_ROLE_BONUS = 10

# =============================================================================
# RESEARCH BOOSTS (scored in step3_score.py and step5_final_rank.py)
# =============================================================================

LIGHTWEIGHTING_BOOST = 15      # Active lightweighting programs
SUSTAINABILITY_BOOST = 10      # Sustainability / green materials programs
CAPEX_BOOST = 10               # Announced CapEx / R&D budget
ACQUISITION_BOOST = 5          # Recent acquisitions
MULTI_PROGRAM_BOOST = 5        # Works on 5+ aircraft programs
LARGE_PRODUCTION_BOOST = 5     # High-volume production (1,000+ units/yr)
BIO_MATERIALS_BOOST = 5        # Bio-based materials interest

# =============================================================================
# TIER THRESHOLDS
# =============================================================================

TIER_THRESHOLDS = {
    1: 75,   # Must Meet: score >= 75 OR Key Contact
    2: 55,   # High Priority: 55-74
    3: 35,   # Strategic: 35-54
    4: 0,    # General: < 35
}

TIER_NAMES = {
    1: "Must Meet",
    2: "High Priority",
    3: "Strategic",
    4: "General",
}

# =============================================================================
# KEY CONTACTS — Pre-identified Nyriom/NyrionPlex targets
# Format: (first_name_lower, last_name_lower)
# =============================================================================

KEY_CONTACTS = [
    # Fictional key contacts
    ("erik", "lindstrom"),      # VP Materials & Processes, Airbus
    ("mei", "chen"),            # Director Composite Procurement, Safran
    ("jan", "weber"),           # Head of Sustainable Materials, Hexcel
]

KEY_CONTACT_BONUS = 30

# =============================================================================
# EXPANSION VARIABLES — 13 fields researched by Perplexity
# =============================================================================

EXPANSION_VARIABLES = [
    "company_type",
    "program_count",
    "region_focus",
    "lightweighting_programs",
    "sustainability_initiatives",
    "production_scale",
    "linkedin_url",
    # Specific to materials adoption
    "materials_adoption_role",
    "current_material_suppliers",
    "rd_budget",
    "material_spec_influence",
    "recent_acquisitions",
    "bio_materials_interest",
]

# Fields to prioritize for Sonar Pro gap-filling
ENHANCEMENT_PRIORITY_FIELDS = [
    "materials_adoption_role",
    "current_material_suppliers",
    "lightweighting_programs",
    "rd_budget",
    "bio_materials_interest",
    "linkedin_url",
]

# =============================================================================
# Utility Functions
# =============================================================================

def validate_config():
    """Validate that all required configuration is present."""
    errors = []

    if not PERPLEXITY_API_KEY:
        errors.append("PERPLEXITY_API_KEY is not set. Create a .env file with your key.")

    if not INPUT_CSV.exists():
        errors.append(f"Input CSV file not found: {INPUT_CSV}")

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    return errors


def print_config_status():
    """Print configuration status for debugging."""
    print("=" * 60)
    print("AEROCOM 2025 Pipeline - Configuration Status")
    print("=" * 60)
    print(f"Perplexity API Key: {'Set' if PERPLEXITY_API_KEY else 'NOT SET'}")
    print(f"Input CSV: {INPUT_CSV}")
    print(f"  Exists: {INPUT_CSV.exists()}")
    print(f"Output Dir: {OUTPUT_DIR}")
    print(f"Logs Dir: {LOGS_DIR}")
    print(f"Company Buckets: {len(COMPANY_BUCKETS)} defined")
    print(f"Function Buckets: {len(FUNCTION_BUCKETS)} defined")
    print(f"Key Contacts: {len(KEY_CONTACTS)} pre-identified")
    print(f"Expansion Variables: {len(EXPANSION_VARIABLES)}")
    print(f"Dual-Pass Research: {'Enabled' if DUAL_PASS else 'Disabled (single-pass)'}")
    print(f"Enhancement Top-N: {ENHANCE_TOP_N}")
    print("=" * 60)


if __name__ == "__main__":
    print_config_status()
    errors = validate_config()
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nConfiguration is valid!")
