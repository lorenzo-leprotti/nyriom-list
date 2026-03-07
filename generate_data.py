"""Generate fictional AEROCOM 2025 delegate data for the portfolio demo."""

import csv
import random

random.seed(42)

# Real aerospace/composites companies organized by bucket
COMPANIES = {
    "Aerospace OEM": [
        "Airbus", "Boeing", "Embraer", "Bombardier Aviation",
        "Dassault Aviation", "Lockheed Martin", "Northrop Grumman",
        "BAE Systems", "Leonardo S.p.A.", "Textron Aviation",
        "Gulfstream Aerospace", "Saab AB", "Pilatus Aircraft",
        "Kawasaki Heavy Industries", "Mitsubishi Heavy Industries",
    ],
    "Tier 1 Supplier": [
        "Safran", "Collins Aerospace", "Spirit AeroSystems",
        "GE Aerospace", "Rolls-Royce", "Pratt & Whitney",
        "Honeywell Aerospace", "Parker Hannifin", "Moog Inc.",
        "Curtiss-Wright", "Triumph Group", "Howmet Aerospace",
        "TransDigm Group", "HEICO Corporation", "Senior plc",
        "Woodward Inc.", "Ducommun",
    ],
    "Tier 2-3 Specialty": [
        "Albany International Composites", "Kaman Aerospace",
        "Teledyne Technologies", "Premium Aerotec",
        "Stelia Aerospace", "Daher", "Latecoere",
        "Figeac Aero", "Aernnova Aerospace", "Aciturri",
        "GKN Aerospace", "Fokker Technologies",
        "Avio Aero", "ITP Aero", "Liebherr Aerospace",
        "FACC AG", "RUAG International",
        "Magellan Aerospace", "Orbital Composites",
        "Automated Dynamics", "Electroimpact",
    ],
    "Material Supplier": [
        "Hexcel Corporation", "Toray Industries",
        "Solvay Composite Materials", "BASF SE",
        "DuPont de Nemours", "Arkema SA", "Teijin Limited",
        "Covestro AG", "Huntsman Corporation", "Evonik Industries",
        "SGL Carbon", "Zoltek Companies", "Gurit Holding",
        "Renegade Materials", "Mitsubishi Chemical",
        "Dow Inc.", "3M Aerospace", "Henkel AG",
        "SABIC", "Lanxess AG",
    ],
    "Airline / MRO": [
        "Lufthansa Technik", "Air France Industries",
        "ST Aerospace", "HAECO Group", "AAR Corp",
        "Turkish Technic", "Delta TechOps",
        "Emirates Engineering", "Etihad Engineering",
        "SIA Engineering", "Aeroplex Group",
        "Air New Zealand Engineering",
    ],
    "Research / Testing": [
        "Fraunhofer IFAM", "DLR - German Aerospace Center",
        "ONERA", "National Composites Centre",
        "Cranfield University", "TU Delft Aerospace",
        "University of Bristol Composites", "MIT AeroAstro",
        "Purdue University Composites Lab",
        "National Institute for Aviation Research",
    ],
    "Engineering / Design": [
        "Altair Engineering", "ANSYS Inc.",
        "Dassault Systemes", "Siemens Digital Industries",
        "MSC Software", "CGTech",
        "ESI Group", "Aerostructures Engineering",
    ],
    "Excludable": [
        "Baker McKenzie", "DLA Piper", "Dentons LLP",
        "McKinsey & Company", "Boston Consulting Group",
        "Deloitte Consulting", "KPMG Advisory",
        "Aviation Week Network", "Composites World Media",
        "JEC Group", "FlightGlobal",
        "Deutsche Bank", "Barclays Aerospace Finance",
        "AIG Insurance", "Marsh Aviation",
    ],
}

# Fictional first/last names (diverse international mix)
FIRST_NAMES_MALE = [
    "Erik", "Jan", "Marco", "Pierre", "Raj", "Kenji", "Hans",
    "Luca", "Thomas", "James", "Michael", "David", "Carlos",
    "Hiroshi", "Stefan", "Florian", "Andre", "Olivier", "Ravi",
    "Chen", "Yuki", "Omar", "Klaus", "Bruno", "Sergio",
    "Henrik", "Lars", "Matteo", "Antoine", "Nikolai",
    "Felix", "Tobias", "Martin", "Christian", "Robert",
    "Alexander", "Patrick", "Philippe", "Andreas", "Romain",
    "Takeshi", "Wei", "Arjun", "Sanjay", "Paolo",
    "Friedrich", "Guillaume", "Maximilian", "Sebastian", "Daniel",
    "Victor", "Leopold", "Dominik", "Christoph", "Bernhard",
    "Javier", "Rafael", "Fernando", "Miguel", "Alvaro",
    "Kazuki", "Akira", "Taro", "Shin", "Ryota",
]
FIRST_NAMES_FEMALE = [
    "Mei", "Sophie", "Anna", "Maria", "Priya", "Yuki", "Ingrid",
    "Clara", "Elena", "Sarah", "Emma", "Laura", "Ana",
    "Haruka", "Katrin", "Julia", "Celine", "Nadia", "Amira",
    "Lin", "Mika", "Fatima", "Greta", "Chiara", "Isabella",
    "Astrid", "Eva", "Francesca", "Camille", "Olga",
    "Petra", "Simone", "Helene", "Christine", "Jennifer",
    "Alexandra", "Nicole", "Monique", "Barbara", "Delphine",
    "Ayumi", "Xin", "Deepa", "Ananya", "Valentina",
    "Margot", "Beatrice", "Constance", "Dorothea", "Gabrielle",
    "Carmen", "Lucia", "Teresa", "Pilar", "Blanca",
    "Sakura", "Miho", "Rina", "Kaori", "Nanami",
]

LAST_NAMES = [
    "Lindstrom", "Chen", "Weber", "Moreau", "Sharma", "Tanaka", "Mueller",
    "Rossi", "Schmidt", "Williams", "Johnson", "Garcia", "Santos",
    "Nakamura", "Fischer", "Bauer", "Laurent", "Dubois", "Patel",
    "Wang", "Sato", "Al-Hassan", "Richter", "Ferrari", "Conti",
    "Johansson", "Andersen", "Mancini", "Dupont", "Volkov",
    "Klein", "Hoffmann", "Lang", "Braun", "Keller",
    "Schneider", "Berger", "Wagner", "Zimmerman", "Beaumont",
    "Yamamoto", "Liu", "Krishnan", "Gupta", "De Luca",
    "Hartmann", "Lefevre", "Strauss", "Engel", "Bergmann",
    "Martinez", "Lopez", "Hernandez", "Torres", "Ruiz",
    "Watanabe", "Ito", "Kobayashi", "Suzuki", "Takahashi",
    "Stein", "Koch", "Wolf", "Neumann", "Schuster",
    "Krause", "Roth", "Seidel", "Vogt", "Hauser",
    "Park", "Kim", "Lee", "Choi", "Jung",
    "Fernandez", "Alvarez", "Romero", "Navarro", "Vega",
    "Maier", "Arnold", "Fuchs", "Kern", "Mayer",
]

# Titles by category
TITLES = {
    "materials_engineering": [
        "VP Materials & Processes", "Director Composites Engineering",
        "Head of Materials Technology", "Senior Materials Engineer",
        "Composites R&D Manager", "Materials Science Lead",
        "Chief Materials Engineer", "Polymer Engineer",
        "Advanced Materials Researcher", "Senior Composites Specialist",
        "Materials Engineering Manager", "Lead Composites Engineer",
    ],
    "procurement": [
        "VP Procurement", "Director Supply Chain",
        "Head of Procurement", "Senior Procurement Manager",
        "Materials Procurement Lead", "Supply Chain Director",
        "Chief Procurement Officer", "Sourcing Manager",
        "Strategic Procurement Director", "VP Supply Management",
        "Director Composite Procurement", "Global Sourcing Lead",
    ],
    "manufacturing": [
        "VP Manufacturing", "Director Production",
        "Plant Manager", "Manufacturing Engineering Manager",
        "Head of Composite Manufacturing", "Process Engineer Lead",
        "Production Director", "VP Operations",
        "Composites Manufacturing Manager", "Industrial Engineering Director",
    ],
    "sustainability": [
        "VP Sustainability", "Director ESG Programs",
        "Head of Sustainable Materials", "Sustainability Manager",
        "Circular Economy Lead", "Green Materials Director",
        "Chief Sustainability Officer", "Environmental Programs Manager",
    ],
    "csuite": [
        "CEO", "President", "Chairman",
        "Chief Executive Officer", "Chief Operating Officer",
        "Chief Technology Officer", "Chief Financial Officer",
        "Managing Director", "President & CEO",
    ],
    "senior_exec": [
        "SVP Engineering", "EVP Operations",
        "Senior Vice President R&D", "Executive Vice President",
        "SVP Business Development", "EVP Strategy",
    ],
    "vp": [
        "Vice President Engineering", "VP Business Development",
        "VP Quality & Certification", "VP Technology",
        "VP Program Management", "VP Strategic Partnerships",
    ],
    "director": [
        "Director Engineering", "Director Business Development",
        "Director Quality Assurance", "Director R&D",
        "Director Program Management", "Director Certification",
        "Senior Director Operations", "Director Strategic Accounts",
    ],
    "quality": [
        "Quality Manager", "Director Quality Assurance",
        "VP Quality & Certification", "Nadcap Coordinator",
        "Quality Engineering Lead", "NDT Manager",
        "Certification Manager", "AS9100 Lead Auditor",
    ],
    "junior_exclude": [
        "Research Analyst", "Junior Associate",
        "Student Intern", "Marketing Coordinator",
        "Legal Counsel", "Staff Attorney",
        "PR Assistant", "Event Coordinator",
        "Finance Analyst", "Accounting Associate",
        "Editorial Assistant", "Research Student",
    ],
}

def generate_delegates():
    rows = []
    used_names = set()

    def pick_unique_name():
        for _ in range(100):
            if random.random() < 0.5:
                first = random.choice(FIRST_NAMES_MALE)
            else:
                first = random.choice(FIRST_NAMES_FEMALE)
            last = random.choice(LAST_NAMES)
            key = f"{first}|{last}"
            if key not in used_names:
                used_names.add(key)
                return first, last
        # Fallback: add suffix
        first = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
        last = random.choice(LAST_NAMES)
        return first, last

    # --- Aerospace OEM: ~100 people ---
    for company in COMPANIES["Aerospace OEM"]:
        n = random.randint(5, 9)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["materials_engineering", "procurement", "manufacturing",
                 "sustainability", "csuite", "senior_exec", "vp", "director"],
                weights=[20, 15, 15, 10, 5, 8, 12, 15],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))
        if len(rows) >= 100:
            break

    # --- Tier 1 Supplier: ~80 people ---
    for company in COMPANIES["Tier 1 Supplier"]:
        n = random.randint(3, 6)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["materials_engineering", "procurement", "manufacturing",
                 "csuite", "senior_exec", "vp", "director", "quality"],
                weights=[20, 15, 15, 5, 8, 12, 15, 10],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))
        if len(rows) >= 180:
            break

    # --- Tier 2-3: ~80 people ---
    for company in COMPANIES["Tier 2-3 Specialty"]:
        n = random.randint(3, 5)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["materials_engineering", "manufacturing", "procurement",
                 "csuite", "vp", "director", "quality"],
                weights=[25, 20, 10, 8, 10, 15, 12],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))
        if len(rows) >= 260:
            break

    # --- Material Supplier: ~60 people ---
    for company in COMPANIES["Material Supplier"]:
        n = random.randint(2, 4)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["materials_engineering", "csuite", "senior_exec",
                 "vp", "director", "sustainability"],
                weights=[25, 10, 8, 15, 20, 22],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))
        if len(rows) >= 320:
            break

    # --- Airline / MRO: ~50 people ---
    for company in COMPANIES["Airline / MRO"]:
        n = random.randint(3, 5)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["manufacturing", "procurement", "director",
                 "vp", "quality"],
                weights=[25, 20, 20, 15, 20],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))
        if len(rows) >= 370:
            break

    # --- Research / Testing (EXCLUDE): ~30 people ---
    for company in COMPANIES["Research / Testing"]:
        n = random.randint(2, 4)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["materials_engineering", "director", "csuite", "junior_exclude"],
                weights=[30, 25, 15, 30],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))
        if len(rows) >= 400:
            break

    # --- Engineering / Design: ~20 people ---
    for company in COMPANIES["Engineering / Design"]:
        n = random.randint(2, 3)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["director", "vp", "csuite", "senior_exec"],
                weights=[30, 30, 20, 20],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))

    # --- Excludable: ~100 people ---
    for company in COMPANIES["Excludable"]:
        n = random.randint(4, 8)
        for _ in range(n):
            first, last = pick_unique_name()
            title_cat = random.choices(
                ["junior_exclude", "director", "vp", "csuite"],
                weights=[50, 25, 15, 10],
            )[0]
            title = random.choice(TITLES[title_cat])
            rows.append((first, last, title, company))

    # Make sure we have the 3 key contacts
    key_contacts = [
        ("Erik", "Lindstrom", "VP Materials & Processes", "Airbus"),
        ("Mei", "Chen", "Director Composite Procurement", "Safran"),
        ("Jan", "Weber", "Head of Sustainable Materials", "Hexcel Corporation"),
    ]
    # Remove any existing with these names
    rows = [(f, l, t, c) for f, l, t, c in rows
            if not ((f.lower(), l.lower()) in {("erik", "lindstrom"), ("mei", "chen"), ("jan", "weber")})]
    rows.extend(key_contacts)

    random.shuffle(rows)

    # Write CSV
    output_path = "input/aerocom_2025_delegates.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["First Name", "Last Name", "Job Title", "Company Name"])
        for first, last, title, company in rows:
            writer.writerow([first, last, title, company])

    print(f"Generated {len(rows)} delegates to {output_path}")

    # Quick stats
    from collections import Counter
    company_cats = Counter()
    for _, _, _, c in rows:
        for cat, companies in COMPANIES.items():
            if c in companies:
                company_cats[cat] += 1
                break
    for cat, count in company_cats.most_common():
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    generate_delegates()
