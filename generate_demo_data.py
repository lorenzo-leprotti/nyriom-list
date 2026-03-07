"""
Generate pre-baked research data for the AEROCOM 2025 demo backend.

Reads aerocom_2025_delegates.csv, generates plausible research data for
all 13 expansion variables, and outputs to input/demo_research_data.json.

Data is keyed by "First|Last|Company".
"""

import csv
import json
import random
from pathlib import Path

random.seed(42)  # Reproducible results

BASE_DIR = Path(__file__).parent
INPUT_CSV = BASE_DIR / "input" / "aerocom_2025_delegates.csv"
OUTPUT_JSON = BASE_DIR / "input" / "demo_research_data.json"

# ─── Key contacts that should have COMPLETE, high-quality data ───────────────
KEY_CONTACTS = {
    ("Erik", "Lindstrom", "Airbus"),
    ("Mei", "Chen", "Safran"),
    ("Jan", "Weber", "Hexcel Corporation"),
}

# ─── Company classification helpers ─────────────────────────────────────────

OEM_PATTERNS = [
    "airbus", "boeing", "embraer", "bombardier", "dassault aviation",
    "lockheed martin", "northrop grumman", "raytheon", "bae systems",
    "leonardo", "textron aviation", "gulfstream", "cessna", "pilatus",
    "saab", "kawasaki heavy", "mitsubishi heavy", "comac",
]

TIER1_PATTERNS = [
    "safran", "collins aerospace", "raytheon technologies",
    "spirit aerosystems", "ge aerospace", "ge aviation",
    "rolls-royce", "pratt & whitney", "honeywell aerospace",
    "moog", "parker hannifin", "parker aerospace",
    "curtiss-wright", "triumph group", "howmet",
    "transdigm", "heico", "meggitt", "senior plc",
    "woodward", "ducommun",
]

TIER23_PATTERNS = [
    "albany international", "albany engineered", "kaman aerospace",
    "hexion", "teledyne", "aerojet rocketdyne", "orbital atk",
    "premium aerotec", "stelia aerospace", "daher", "latecoere",
    "figeac aero", "aernnova", "aciturri", "gkn aerospace",
    "fokker", "avio aero", "itp aero", "liebherr aerospace",
    "facc", "ruag", "composites", "composite", "aerostructures",
    "tooling", "prepreg", "autoclave", "fiber placement",
    "magellan aerospace", "orbital composites",
]

MATERIAL_SUPPLIER_PATTERNS = [
    "hexcel", "toray", "solvay", "basf", "dupont", "arkema",
    "teijin", "covestro", "huntsman", "cytec", "mitsubishi chemical",
    "sabic", "evonik", "lanxess", "dow", "3m", "henkel",
    "sgl carbon", "zoltek", "gurit", "renegade materials",
    "tencate", "park electrochemical", "isola group",
    "carbon fiber", "resin", "polymer", "chemical",
    "material supplier", "materials", "adhesive", "coating",
]

AIRLINE_MRO_PATTERNS = [
    "lufthansa technik", "air france industries", "st aerospace",
    "haeco", "aar corp", "turkish technic", "delta techops",
    "emirates engineering", "etihad engineering", "aeroplex",
    "aviall", "airline", "airlines", "airways", "mro",
    "maintenance", "overhaul", "repair station",
]

INVESTMENT_PATTERNS = [
    "carlyle", "blackstone", "brookfield", "cerberus", "kkr",
    "apollo", "capital", "investment", "investor", "private equity",
    "equity partners", "partners", "fund ", "funds", "advisors",
    "advisory", "ventures", "asset management",
]

ENGINEERING_PATTERNS = [
    "altair", "ansys", "dassault systemes", "siemens digital",
    "msc software", "engineering services", "design services",
    "simulation", "structural analysis", "consulting engineer",
    "test laboratory", "certification",
]

EXCLUDE_PATTERNS = [
    "law firm", "llp", "legal", "attorney", "consulting group",
    "consultants", "management consulting", "bank", "banking",
    "insurance", "accounting", "audit", "composites world",
    "jec group", "aviation week", "flightglobal", "flight global",
    "media", "magazine", "publishing", "news", "trade show",
    "university", "college", "school of", "institute of",
    "academic", "student", "fraunhofer", "dlr", "onera", "nasa",
    "national laboratory", "deloitte",
]

# ─── Region mapping for well-known companies ────────────────────────────────

COMPANY_REGION = {
    "airbus": "Global",
    "boeing": "Americas",
    "embraer": "Americas",
    "bombardier": "Americas",
    "dassault aviation": "Europe",
    "lockheed martin": "Americas",
    "northrop grumman": "Americas",
    "raytheon": "Americas",
    "bae systems": "Europe",
    "leonardo": "Europe",
    "textron": "Americas",
    "gulfstream": "Americas",
    "cessna": "Americas",
    "pilatus": "Europe",
    "saab": "Europe",
    "kawasaki heavy": "APAC",
    "mitsubishi heavy": "APAC",
    "comac": "APAC",
    "safran": "Europe",
    "collins aerospace": "Americas",
    "spirit aerosystems": "Americas",
    "ge aerospace": "Americas",
    "ge aviation": "Americas",
    "rolls-royce": "Europe",
    "pratt & whitney": "Americas",
    "honeywell": "Americas",
    "moog": "Americas",
    "parker hannifin": "Americas",
    "curtiss-wright": "Americas",
    "triumph group": "Americas",
    "howmet": "Americas",
    "transdigm": "Americas",
    "heico": "Americas",
    "meggitt": "Europe",
    "hexcel": "Americas",
    "toray": "APAC",
    "solvay": "Europe",
    "basf": "Europe",
    "dupont": "Americas",
    "arkema": "Europe",
    "teijin": "APAC",
    "covestro": "Europe",
    "huntsman": "Americas",
    "cytec": "Americas",
    "sabic": "APAC",
    "evonik": "Europe",
    "lanxess": "Europe",
    "dow": "Americas",
    "3m": "Americas",
    "henkel": "Europe",
    "sgl carbon": "Europe",
    "zoltek": "Americas",
    "gurit": "Europe",
    "daher": "Europe",
    "latecoere": "Europe",
    "figeac aero": "Europe",
    "aernnova": "Europe",
    "aciturri": "Europe",
    "gkn aerospace": "Europe",
    "fokker": "Europe",
    "avio aero": "Europe",
    "itp aero": "Europe",
    "liebherr": "Europe",
    "facc": "Europe",
    "ruag": "Europe",
    "premium aerotec": "Europe",
    "stelia": "Europe",
    "magellan aerospace": "Americas",
    "lufthansa technik": "Europe",
    "air france": "Europe",
    "turkish technic": "Europe",
    "emirates engineering": "APAC",
    "etihad engineering": "APAC",
    "altair": "Americas",
    "ansys": "Americas",
    "dassault systemes": "Europe",
    "orbital composites": "Europe",
    "albany international": "Americas",
    "teledyne": "Americas",
    "woodward": "Americas",
    "ducommun": "Americas",
    "aeroplex": "Europe",
}


def classify_company(company_name):
    """Return (company_type_label, category_key)."""
    cn = company_name.lower()
    for p in OEM_PATTERNS:
        if p in cn:
            return ("Aerospace OEM", "OEM")
    for p in TIER1_PATTERNS:
        if p in cn:
            return ("Tier 1 Aerostructures Supplier", "TIER1")
    for p in MATERIAL_SUPPLIER_PATTERNS:
        if p in cn:
            return ("Material Supplier / Chemical Co.", "MATERIAL")
    for p in TIER23_PATTERNS:
        if p in cn:
            return ("Tier 2-3 Specialty Manufacturer", "TIER23")
    for p in AIRLINE_MRO_PATTERNS:
        if p in cn:
            return ("Airline / MRO", "MRO")
    for p in INVESTMENT_PATTERNS:
        if p in cn:
            return ("Investment / PE", "INVEST")
    for p in ENGINEERING_PATTERNS:
        if p in cn:
            return ("Engineering / Design Services", "ENG")
    for p in EXCLUDE_PATTERNS:
        if p in cn:
            return ("Other", "EXCLUDE")
    return ("Other", "EXCLUDE")


def get_region(company_name):
    cn = company_name.lower()
    for key, region in COMPANY_REGION.items():
        if key in cn:
            return region
    return random.choice(["Europe", "Americas", "APAC", "Global"])


def is_materials_title(title):
    tl = title.lower()
    keywords = [
        "materials", "composites", "composite", "procurement",
        "purchasing", "supply chain", "sourcing", "polymer",
    ]
    return any(k in tl for k in keywords)


def is_manufacturing_sustainability(title):
    tl = title.lower()
    keywords = [
        "manufacturing", "production", "sustainability", "esg",
        "environment", "quality", "process engineer",
    ]
    return any(k in tl for k in keywords)


def is_senior_title(title):
    tl = title.lower()
    keywords = [
        "director", "vp", "vice president", "svp", "evp",
        "head of", "chief", "ceo", "cto", "coo", "president",
        "managing director", "senior manager", "general manager",
    ]
    return any(k in tl for k in keywords)


# ─── Lightweighting programs pool ───────────────────────────────────────────

LIGHTWEIGHTING_OEM = [
    "A350 XWB composite fuselage program (53% composite by weight)",
    "A320neo wing composite optimization initiative",
    "787 Dreamliner carbon fiber fuselage and wing structures",
    "777X composite folding wingtip program",
    "F-35 composite airframe structures (35% by weight)",
    "Next-gen single-aisle composite wing demonstrator",
    "eVTOL lightweight airframe development (sub-500kg target)",
    "Advanced composite empennage for regional jet platform",
    "Thermoplastic composite fuselage panel program",
    "Composite fan containment case development",
]

LIGHTWEIGHTING_SUPPLIER = [
    "Thermoplastic composite bracket replacement program",
    "Carbon fiber reinforced polymer (CFRP) nacelle components",
    "Composite landing gear door weight reduction initiative",
    "Advanced fiber placement for wing skin panels",
    "Lightweight composite interior structures program",
    "Out-of-autoclave composite process development",
    "Recycled carbon fiber structural components R&D",
    "Hybrid metal-composite fastener elimination program",
]

LIGHTWEIGHTING_MATERIAL = [
    "Next-gen high-modulus carbon fiber development (T1100-class)",
    "Bio-based epoxy resin system for aerospace qualification",
    "Thermoplastic PAEK/PEKK tape development for AFP",
    "Low-density syntactic core materials for sandwich panels",
    "Snap-cure resin systems for high-rate composite production",
    "Recycled carbon fiber nonwoven preform technology",
]

# ─── Sustainability initiatives pool ────────────────────────────────────────

SUSTAINABILITY_OEM = [
    "Airbus ZEROe hydrogen-powered aircraft program",
    "Carbon neutral operations by 2030 commitment",
    "SAF (Sustainable Aviation Fuel) blending mandate compliance",
    "Circular economy program for composite recycling",
    "Science Based Targets initiative (SBTi) commitment",
    "30% reduction in manufacturing CO2 emissions by 2028",
    "Green factory initiative with 100% renewable energy target",
    "End-of-life aircraft composite recycling partnership",
]

SUSTAINABILITY_SUPPLIER = [
    "Scope 1-2 carbon neutrality target by 2030",
    "ISO 14001-certified manufacturing across all sites",
    "Composite waste recycling program (75% diversion rate)",
    "Bio-sourced material qualification initiative",
    "Energy efficiency program: 20% reduction target by 2027",
    "Water-based coating systems to replace solvent processes",
    "Supply chain Scope 3 emissions tracking program",
]

SUSTAINABILITY_MATERIAL = [
    "Bio-based resin portfolio development (40% bio-content target)",
    "Closed-loop carbon fiber recycling technology",
    "Solvent-free prepreg manufacturing process",
    "Green chemistry initiative for epoxy hardeners",
    "Lifecycle assessment (LCA) for all aerospace product lines",
    "Plant-derived precursor research for carbon fiber",
]

# ─── Material suppliers pool ────────────────────────────────────────────────

MATERIAL_COMPANIES = [
    "Hexcel", "Toray Composite Materials America", "Solvay",
    "Teijin Carbon", "SGL Carbon", "Mitsubishi Chemical",
    "Huntsman Advanced Materials", "Arkema / Bostik",
    "Gurit", "Park Electrochemical", "Cytec (Solvay)",
    "Henkel Adhesives", "3M Aerospace", "BASF",
]

# ─── Acquisitions pool ──────────────────────────────────────────────────────

ACQUISITIONS = [
    "Acquired Cobham Aerospace (2023, $1.1B) to expand composite aerostructure capacity",
    "Completed merger with Ducommun's structures division (2024)",
    "Acquired minority stake in bio-composites startup EcoTechniLin (2023)",
    "Purchased Triumph Group's composite wing operations (2024, $400M)",
    "Strategic acquisition of CPI Aerostructures (2023)",
    "Acquired FACC's thermoplastic welding IP portfolio (2024)",
    "Joint venture with Toray for next-gen carbon fiber production (2023)",
    "Acquired Renegade Materials for high-temp resin technology (2023)",
    "Purchased Chomarat's aerospace textiles division (2024)",
    "Acquired ATC Manufacturing for automated fiber placement (2023)",
    "Strategic investment in Aerion Supersonic composite structures (2024)",
    "Acquired Kaman Aerospace's composite bearings unit (2024, $180M)",
    "Purchased GKN Fokker's thermoplastic stiffened panel line (2023)",
    "Acquired Quickstep Holdings composite manufacturing (2024)",
]

# ─── Bio-materials interest pool ────────────────────────────────────────────

BIO_MATERIALS = [
    "Evaluating bio-based epoxy systems from Entropy Resins for secondary structures",
    "Active R&D in flax fiber reinforced polymer composites for interior panels",
    "Partnership with Bcomp for natural fiber composite seat components",
    "Funded university research on lignin-based carbon fiber precursors",
    "Testing bio-sourced PAEK thermoplastics for brackets and clips",
    "Pilot program for bio-resin infusion in non-structural fairings",
    "Internal assessment of PLA/PHA bio-polymers for cabin components",
    "Collaborating with RISE Research Institute on bio-composite testing",
    "Evaluating hemp fiber / bio-epoxy hybrid for cargo liners",
    "Joint development with Arkema on castor-oil-based polyamide composites",
    "Published sustainability roadmap calling for 25% bio-content in composites by 2030",
    "Testing mycelium-based core materials for sandwich panels",
]

# ─── Production scale templates ─────────────────────────────────────────────

PRODUCTION_OEM = [
    "~60 A320-family aircraft/month; ~6 A350/month",
    "~40 737 MAX/month; ~5 787/month; ~3 777X/month",
    "~10 commercial aircraft/month plus military platforms",
    "~14 E-Jet/month; ~3 KC-390/year",
    "~30-40 military aircraft/year across programs",
    "~8 business jets/month",
    "~120 aircraft/year across business and military lines",
]

PRODUCTION_SUPPLIER = [
    "~500,000 composite parts/year across 8 manufacturing sites",
    "~2,000+ engine nacelle assemblies/year",
    "~150,000 composite brackets and fittings/year",
    "~12,000 aerostructure assemblies/year",
    "~3,500 composite panels and fairings/month",
    "~800 wing component sets/year",
]

PRODUCTION_MATERIAL = [
    "~15,000 tonnes/year carbon fiber capacity (expanding to 20,000)",
    "~8,000 tonnes/year prepreg production across 3 facilities",
    "~25,000 tonnes/year specialty resins and adhesives",
    "~5,000 tonnes/year aerospace-grade carbon fiber",
    "~12,000 tonnes/year advanced polymer production",
    "~3,000 tonnes/year aerospace adhesives and sealants",
]

# ─── R&D budget pool ────────────────────────────────────────────────────────

RD_BUDGETS_OEM = [
    "$3.2B annual R&D (2024); ~15% allocated to composite materials",
    "$2.8B R&D spend; advanced materials division receives ~$400M",
    "$1.5B annual R&D budget; composites and lightweighting ~$200M",
    "$800M R&D annually; significant composites investment",
    "$500M R&D budget; composite structures ~$75M",
]

RD_BUDGETS_SUPPLIER = [
    "$350M annual R&D; composite aerostructures ~$50M",
    "$200M R&D spend; advanced manufacturing processes ~$40M",
    "$150M annual R&D budget; materials & processes focus",
    "$120M R&D; composite technologies ~$25M",
    "$80M annual R&D investment",
]

RD_BUDGETS_MATERIAL = [
    "$600M annual R&D; next-gen fiber and resin platforms",
    "$400M R&D; bio-based and recycled material streams ~$60M",
    "$250M annual R&D across polymer and composite lines",
    "$180M R&D spend; aerospace-specific programs ~$50M",
    "$100M R&D; sustainable chemistry focus",
]

# ─── Hard-coded data for key contacts ───────────────────────────────────────

KEY_CONTACT_DATA = {
    "Erik|Lindstrom|Airbus": {
        "company_type": "Aerospace OEM",
        "program_count": "42 active aircraft programs including A320neo, A330neo, A350 XWB, A400M, H160, and CityAirbus NextGen eVTOL",
        "region_focus": "Global (HQ Toulouse, France; major sites in Hamburg, Broughton, Mobile AL, Tianjin)",
        "lightweighting_programs": "A350 XWB: 53% composite airframe (largest CFRP structure in commercial aviation). A320neo composite wing demonstrator (Wing of Tomorrow program). CityAirbus NextGen all-composite eVTOL airframe. ZEROe hydrogen tank composite overwrap development.",
        "sustainability_initiatives": "Airbus ZEROe program: three hydrogen-powered zero-emission aircraft concepts by 2035. Fello'fly wake energy retrieval demonstrator. Committed to 100% SAF compatibility across fleet by 2030. Composite recycling JV with Suez for end-of-life aircraft.",
        "production_scale": "~60 A320-family/month (ramping to 75 by 2026); ~6 A350/month (target 10 by 2026); ~3 A330neo/month. Total: ~830 commercial aircraft delivered in 2024.",
        "linkedin_url": "NOT_FOUND",
        "materials_adoption_role": "YES - VP Materials & Processes is the primary decision-maker for material qualification and selection across all Airbus programs. Direct authority over composite material specifications and supplier qualification.",
        "current_material_suppliers": "Hexcel (primary prepreg for A350, long-term supply agreement through 2030), Toray Industries (carbon fiber for A350 fuselage), Solvay (adhesives and specialty resins), Teijin Carbon (secondary carbon fiber supply), SGL Carbon (oxidized PAN fiber for brake discs), Arkema (PEKK thermoplastic resins for brackets)",
        "rd_budget": "$3.5B annual R&D spend (2024). Materials & Processes division receives ~$500M. Dedicated composites R&D center in Stade, Germany and Nantes, France. Active bio-materials evaluation budget of ~$15M.",
        "material_spec_influence": "YES - As VP Materials & Processes, Erik Lindstrom has direct specification authority for all structural and semi-structural composite materials across Airbus commercial and defense programs.",
        "recent_acquisitions": "Acquired remaining 50% of Premium Aerotec (2024) to bring composite aerostructure production in-house. Increased stake in Aerion bio-composites venture. Strategic partnership with Hexcel renewed through 2030 ($2.5B framework agreement).",
        "bio_materials_interest": "HIGH - Airbus Materials & Processes division actively evaluating bio-based epoxy systems for secondary structures. Internal 'Green Composites' working group led by Lindstrom's team. Testing Bcomp flax fiber reinforcements for interior panels. Funded PhD programs at TU Munich and ONERA on lignin-derived carbon fiber precursors. Published target: 10% bio-sourced content in non-primary composite structures by 2030.",
    },
    "Mei|Chen|Safran": {
        "company_type": "Tier 1 Aerostructures Supplier",
        "program_count": "28 active programs including LEAP engine nacelles, A320neo thrust reversers, 787 engine components, Rafale structures, and Ariane 6 composite fairings",
        "region_focus": "Global (HQ Paris, France; major composite sites in Le Havre, Casablanca, Suzhou, and San Diego)",
        "lightweighting_programs": "LEAP engine fan blades: 3D-woven RTM carbon composite (500g lighter per blade vs titanium). A320neo composite thrust reverser program. Next-gen open-fan engine composite fan case. Composite propeller blades for Ardiden helicopter engines.",
        "sustainability_initiatives": "Safran carbon neutrality roadmap by 2030 for Scope 1-2. Sustainable Aviation Fuel compatibility across all engine programs. Composite waste reduction program: 40% scrap rate improvement at Le Havre site. Member of IAEG (International Aerospace Environmental Group).",
        "production_scale": "~2,000 LEAP engine nacelle sets/year (ramping). ~400 thrust reverser units/year. ~6,000 composite structural parts/month across all programs.",
        "linkedin_url": "NOT_FOUND",
        "materials_adoption_role": "YES - Director of Composite Procurement with direct purchasing authority for all composite raw materials (prepregs, fibers, resins, adhesives) across Safran Nacelles and Safran Composites. Budget authority: ~$180M annual composite material spend.",
        "current_material_suppliers": "Hexcel (primary prepreg supplier for nacelle structures, LTA through 2028), Toray Industries (T700/T800 carbon fiber for LEAP fan blades), Solvay (RTM6 resin for 3D-woven parts), Albany International (3D-woven preforms for LEAP), Henkel (structural adhesives), Gurit (core materials)",
        "rd_budget": "$1.8B annual R&D (Safran group). Nacelles division ~$200M. Composite materials R&D ~$45M dedicated budget. Active qualification programs for 3 new resin systems.",
        "material_spec_influence": "YES - As Director Composite Procurement, Mei Chen controls the supplier selection and qualification process for all composite materials. Works directly with Safran's Materials & Processes engineers to define material specifications.",
        "recent_acquisitions": "Safran acquired Collins Aerospace's actuation business (2023). Expanded Le Havre composite center of excellence ($120M investment, 2024). New composite manufacturing JV with Aubert & Duval for titanium-composite hybrid parts.",
        "bio_materials_interest": "MEDIUM-HIGH - Safran evaluating bio-sourced epoxy alternatives for secondary nacelle structures (acoustic panels, fairings). Funded Arkema partnership on bio-based PEKK development. Internal target: qualify first bio-resin system for production by 2027. Chen's team managing evaluation of 4 bio-resin candidates.",
    },
    "Jan|Weber|Hexcel Corporation": {
        "company_type": "Material Supplier / Chemical Co.",
        "program_count": "15+ product families serving 50+ aerospace programs including A350, 787, F-35, A400M, NH90, Rafale, and business jet platforms",
        "region_focus": "Global (HQ Stamford, CT; manufacturing in Salt Lake City, Decatur AL, Dagneux France, Stade Germany, Tianjin China)",
        "lightweighting_programs": "HexPly M56 snap-cure prepreg system for high-rate production. HexMC-i molding compound for complex 3D parts (replacing machined aluminum). HexTow IM9 intermediate modulus carbon fiber. HiTape dry fiber and HiMax multiaxial reinforcements for liquid resin infusion.",
        "sustainability_initiatives": "As Head of Sustainable Materials, Jan Weber leads Hexcel's sustainability strategy. Carbon neutral operations target by 2035. Launched recycled carbon fiber product line (HexCycle). Developed bio-based epoxy hardener system. 30% energy reduction program across manufacturing sites. Published ESG report with Science Based Targets.",
        "production_scale": "~12,000 tonnes/year carbon fiber capacity (Salt Lake City + Decatur). ~8,000 tonnes/year prepreg production (Dagneux + Salt Lake City). ~4,000 tonnes/year adhesive films and surfacing materials.",
        "linkedin_url": "NOT_FOUND",
        "materials_adoption_role": "YES - Head of Sustainable Materials at Hexcel, directly responsible for bio-based and recycled material product development. Drives material innovation roadmap and sustainable product portfolio strategy.",
        "current_material_suppliers": "N/A - Hexcel IS a primary material supplier to the aerospace industry. Key raw material inputs: PAN precursor from Mitsubishi Chemical and Dralon, epoxy resins from Olin and Huntsman, specialty additives from Evonik.",
        "rd_budget": "$75M annual R&D budget. Sustainable materials R&D receives ~$18M dedicated funding. Three active bio-resin qualification programs. Partnership with University of Bristol on natural fiber composites.",
        "material_spec_influence": "YES - As Head of Sustainable Materials, Weber defines product specifications for Hexcel's next-generation sustainable composite materials. Works directly with OEM materials engineers on qualification requirements.",
        "recent_acquisitions": "Acquired ARC Technologies (radar-absorbing composites, 2023, $200M). Strategic investment in Boston Materials (aligned discontinuous fiber technology). Partnership with Bcomp for natural fiber thermoplastic composites. Expanded Casablanca, Morocco facility for A350 prepreg supply.",
        "bio_materials_interest": "VERY HIGH - Jan Weber's primary responsibility. Hexcel developing bio-based epoxy systems targeting 35-50% bio-content. HexBio product line in qualification with two major OEMs. Partnership with Entropy Resins (now Gougeon) for plant-derived epoxy. Active evaluation of lignin-based CF precursors. Published roadmap: 20% of product portfolio bio-sourced by 2030. Presented at JEC 2024 on bio-composite adoption barriers.",
    },
}


def generate_data_for_delegate(first, last, title, company):
    """Generate plausible research data for a single delegate."""
    key = f"{first}|{last}|{company}"

    # Key contacts get hard-coded complete data
    if key in KEY_CONTACT_DATA:
        return KEY_CONTACT_DATA[key]

    company_type_label, category = classify_company(company)
    region = get_region(company)
    tl = title.lower()

    data = {}

    # ── company_type ─────────────────────────────────────────────────────
    data["company_type"] = company_type_label

    # ── program_count ────────────────────────────────────────────────────
    if category == "OEM":
        data["program_count"] = str(random.randint(10, 50))
    elif category in ("TIER1", "TIER23"):
        data["program_count"] = str(random.randint(5, 25))
    elif category == "MATERIAL":
        data["program_count"] = f"Supplies to {random.randint(15, 60)}+ programs"
    elif category == "MRO":
        data["program_count"] = f"Services {random.randint(5, 20)} fleet types"
    else:
        data["program_count"] = "NOT_FOUND"

    # ── region_focus ─────────────────────────────────────────────────────
    data["region_focus"] = region

    # ── lightweighting_programs (~60% have one) ──────────────────────────
    if random.random() < 0.60 and category in ("OEM", "TIER1", "TIER23", "MATERIAL"):
        if category == "OEM":
            pool = LIGHTWEIGHTING_OEM
        elif category == "MATERIAL":
            pool = LIGHTWEIGHTING_MATERIAL
        else:
            pool = LIGHTWEIGHTING_SUPPLIER
        data["lightweighting_programs"] = random.choice(pool)
    else:
        data["lightweighting_programs"] = "NOT_FOUND"

    # ── sustainability_initiatives (~50%) ────────────────────────────────
    if random.random() < 0.50 and category in ("OEM", "TIER1", "TIER23", "MATERIAL"):
        if category == "OEM":
            pool = SUSTAINABILITY_OEM
        elif category == "MATERIAL":
            pool = SUSTAINABILITY_MATERIAL
        else:
            pool = SUSTAINABILITY_SUPPLIER
        data["sustainability_initiatives"] = random.choice(pool)
    else:
        data["sustainability_initiatives"] = "NOT_FOUND"

    # ── production_scale ─────────────────────────────────────────────────
    if category == "OEM":
        data["production_scale"] = random.choice(PRODUCTION_OEM)
    elif category in ("TIER1", "TIER23"):
        data["production_scale"] = random.choice(PRODUCTION_SUPPLIER)
    elif category == "MATERIAL":
        data["production_scale"] = random.choice(PRODUCTION_MATERIAL)
    else:
        data["production_scale"] = "NOT_FOUND"

    # ── linkedin_url (always NOT_FOUND) ──────────────────────────────────
    data["linkedin_url"] = "NOT_FOUND"

    # ── materials_adoption_role ──────────────────────────────────────────
    if is_materials_title(tl):
        data["materials_adoption_role"] = "YES"
    elif is_manufacturing_sustainability(tl):
        data["materials_adoption_role"] = "INDIRECT"
    else:
        data["materials_adoption_role"] = "NO"

    # ── current_material_suppliers ───────────────────────────────────────
    if category == "MATERIAL":
        data["current_material_suppliers"] = "N/A - is a material supplier"
    elif category in ("OEM", "TIER1", "TIER23"):
        suppliers = random.sample(MATERIAL_COMPANIES, k=random.randint(2, 4))
        data["current_material_suppliers"] = ", ".join(suppliers)
    else:
        data["current_material_suppliers"] = "NOT_FOUND"

    # ── rd_budget (~40%) ─────────────────────────────────────────────────
    if random.random() < 0.40 and category in ("OEM", "TIER1", "TIER23", "MATERIAL"):
        if category == "OEM":
            pool = RD_BUDGETS_OEM
        elif category == "MATERIAL":
            pool = RD_BUDGETS_MATERIAL
        else:
            pool = RD_BUDGETS_SUPPLIER
        data["rd_budget"] = random.choice(pool)
    else:
        data["rd_budget"] = "NOT_FOUND"

    # ── material_spec_influence ──────────────────────────────────────────
    if is_materials_title(tl) and is_senior_title(tl):
        data["material_spec_influence"] = "YES"
    elif is_materials_title(tl):
        data["material_spec_influence"] = "YES"
    elif is_senior_title(tl) and category in ("OEM", "TIER1", "TIER23", "MATERIAL"):
        data["material_spec_influence"] = "YES"
    else:
        data["material_spec_influence"] = "NO"

    # ── recent_acquisitions (~30%) ───────────────────────────────────────
    if random.random() < 0.30 and category in ("OEM", "TIER1", "TIER23", "MATERIAL"):
        data["recent_acquisitions"] = random.choice(ACQUISITIONS)
    else:
        data["recent_acquisitions"] = "NOT_FOUND"

    # ── bio_materials_interest (~35%) ────────────────────────────────────
    if random.random() < 0.35 and category in ("OEM", "TIER1", "TIER23", "MATERIAL"):
        data["bio_materials_interest"] = random.choice(BIO_MATERIALS)
    else:
        data["bio_materials_interest"] = "NOT_FOUND"

    # ── Apply ~30% random NOT_FOUND gaps ─────────────────────────────────
    # Fields eligible for random gaps (not company_type, linkedin_url, materials_adoption_role)
    gappable = [
        "program_count", "region_focus", "lightweighting_programs",
        "sustainability_initiatives", "production_scale",
        "current_material_suppliers", "rd_budget", "material_spec_influence",
        "recent_acquisitions", "bio_materials_interest",
    ]
    # Target ~30% NOT_FOUND across all 13 fields. Some are already NOT_FOUND,
    # so we only gap a subset of the ones that currently have data.
    fields_with_data = [f for f in gappable if data.get(f, "NOT_FOUND") != "NOT_FOUND"]

    # Count current NOT_FOUND fields across all 13
    current_nf = sum(1 for v in data.values() if v == "NOT_FOUND")
    target_nf = int(13 * 0.30)  # ~4 fields should be NOT_FOUND

    additional_gaps = max(0, target_nf - current_nf)
    if additional_gaps > 0 and fields_with_data:
        gap_fields = random.sample(fields_with_data, min(additional_gaps, len(fields_with_data)))
        for f in gap_fields:
            data[f] = "NOT_FOUND"

    return data


def main():
    print("Reading delegates from CSV...")
    delegates = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            delegates.append(row)

    print(f"  Found {len(delegates)} delegates")

    research_data = {}
    key_contact_keys = set()

    for d in delegates:
        first = d["First Name"].strip()
        last = d["Last Name"].strip()
        company = d["Company Name"].strip()
        title = d["Job Title"].strip()

        key = f"{first}|{last}|{company}"
        data = generate_data_for_delegate(first, last, title, company)
        research_data[key] = data

        # Track key contacts
        if (first, last, company) in KEY_CONTACTS:
            key_contact_keys.add(key)

    # Write output
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(research_data, f, indent=2, ensure_ascii=False)

    print(f"\nGenerated research data for {len(research_data)} delegates")
    print(f"Output written to: {OUTPUT_JSON}")

    # Stats
    total_fields = 0
    not_found_fields = 0
    for key, data in research_data.items():
        for v in data.values():
            total_fields += 1
            if v == "NOT_FOUND":
                not_found_fields += 1

    pct_nf = (not_found_fields / total_fields * 100) if total_fields else 0
    print(f"\nField stats:")
    print(f"  Total fields: {total_fields}")
    print(f"  NOT_FOUND: {not_found_fields} ({pct_nf:.1f}%)")

    # Verify key contacts have complete data
    print(f"\nKey contact verification:")
    for kc_key in sorted(key_contact_keys):
        kc_data = research_data[kc_key]
        nf_count = sum(1 for v in kc_data.values() if v == "NOT_FOUND")
        status = "COMPLETE" if nf_count <= 1 else f"INCOMPLETE ({nf_count} NOT_FOUND)"
        print(f"  {kc_key}: {status}")

    # Category breakdown
    categories = {}
    for key, data in research_data.items():
        ct = data.get("company_type", "Unknown")
        categories[ct] = categories.get(ct, 0) + 1

    print(f"\nCompany type distribution:")
    for ct, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {ct}: {count}")


if __name__ == "__main__":
    main()
