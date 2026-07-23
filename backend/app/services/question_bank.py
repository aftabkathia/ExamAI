"""Topic-keyed competitive MCQ bank for Pakistani exams.

Keys are normalized topic names. Questions stay strictly on-topic —
never cross-label (e.g. no GK under Everyday Science).
"""

from __future__ import annotations

import random
import re
from typing import Any


def _n(topic: str) -> str:
    t = topic.lower().strip()
    t = t.replace("&", "and").replace("/", " ")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # aliases → canonical keys
    aliases = {
        "everyday science": "everyday science",
        "general science and ability": "everyday science",
        "general science": "everyday science",
        "general knowledge": "general knowledge",
        "gk": "general knowledge",
        "mathematics": "mathematics",
        "maths": "mathematics",
        "computer science": "computer science",
        "computer literacy": "computer science",
        "english": "english",
        "english precis and composition": "english",
        "essay writing": "english",
        "biology": "biology",
        "chemistry": "chemistry",
        "physics": "physics",
        "pakistan affairs": "pakistan studies",
        "pakistan studies": "pakistan studies",
        "islamic studies": "islamic studies",
        "islamiat": "islamic studies",
        "current affairs": "current affairs",
        "iq analytical reasoning": "analytical reasoning",
        "analytical reasoning": "analytical reasoning",
        "logical reasoning": "analytical reasoning",
        "history": "history",
        "urdu": "urdu",
    }
    return aliases.get(t, t)


def _q(
    text: str,
    a: str,
    b: str,
    c: str,
    d: str,
    correct: str,
    explanation: str,
    difficulty: str = "medium",
    source: str = "bank",
) -> dict[str, Any]:
    return {
        "text": text,
        "option_a": a,
        "option_b": b,
        "option_c": c,
        "option_d": d,
        "correct_option": correct.upper(),
        "explanation": explanation,
        "difficulty": difficulty,
        "source": source,
    }


# ── Everyday Science (biology/physics/chem of daily life — NOT GK/politics) ──
EVERYDAY_SCIENCE = [
    _q("Photosynthesis primarily occurs in which organelle of a plant cell?",
       "Mitochondria", "Nucleus", "Chloroplast", "Ribosome", "C",
       "Chloroplasts contain chlorophyll and are the site of photosynthesis.", "easy"),
    _q("The chemical formula of ozone is:",
       "O₂", "O₃", "CO₂", "H₂O₂", "B",
       "Ozone is a triatomic molecule of oxygen, O₃, found in the stratosphere.", "easy"),
    _q("Which vitamin is produced in human skin on exposure to sunlight?",
       "Vitamin A", "Vitamin B12", "Vitamin C", "Vitamin D", "D",
       "UV rays convert 7-dehydrocholesterol in skin to Vitamin D.", "easy"),
    _q("The SI unit of force is:",
       "Joule", "Newton", "Watt", "Pascal", "B",
       "Force is measured in newtons (N); 1 N = 1 kg·m/s².", "easy"),
    _q("Blood is purified (filtered) mainly by which organ?",
       "Liver", "Lungs", "Kidneys", "Spleen", "C",
       "Kidneys filter blood, remove urea and regulate water–salt balance.", "easy"),
    _q("Which gas is most abundant in Earth's atmosphere?",
       "Oxygen", "Carbon dioxide", "Nitrogen", "Argon", "C",
       "Nitrogen makes up about 78% of dry air by volume.", "easy"),
    _q("DNA stands for:",
       "Deoxyribonucleic Acid", "Dinucleic Acid", "Deoxyribose Nitric Acid", "Dual Nucleic Acid", "A",
       "DNA (Deoxyribonucleic Acid) carries genetic information.", "easy"),
    _q("The boiling point of water at standard atmospheric pressure is:",
       "90°C", "100°C", "110°C", "120°C", "B",
       "At 1 atm, pure water boils at 100°C (212°F).", "easy"),
    _q("Which part of the eye controls the amount of light entering?",
       "Retina", "Cornea", "Iris", "Lens", "C",
       "The iris adjusts pupil size to regulate light reaching the retina.", "medium"),
    _q("pH of a neutral solution at 25°C is:",
       "0", "5", "7", "14", "C",
       "Neutral solutions have pH 7; acids < 7 and bases > 7.", "easy"),
    _q("Sound cannot travel through:",
       "Air", "Water", "Steel", "Vacuum", "D",
       "Sound needs a material medium; vacuum has none.", "easy"),
    _q("Which blood group is called the universal donor?",
       "A+", "B+", "AB+", "O−", "D",
       "O negative red cells lack A/B and Rh antigens, so can be given to most recipients in emergencies.", "medium"),
    _q("The hardest natural substance known is:",
       "Gold", "Iron", "Diamond", "Quartz", "C",
       "Diamond (pure carbon in a tetrahedral lattice) ranks 10 on Mohs hardness scale.", "easy"),
    _q("Which planet is known as the Red Planet?",
       "Venus", "Mars", "Jupiter", "Mercury", "B",
       "Mars appears reddish due to iron oxide (rust) on its surface.", "easy"),
    _q("Antibiotics are effective against:",
       "Viruses only", "Bacteria", "All pathogens equally", "Prions only", "B",
       "Antibiotics target bacterial structures/processes; they do not cure viral infections.", "medium"),
]

# ── General Knowledge ────────────────────────────────────────────────────────
GENERAL_KNOWLEDGE = [
    _q("The Indus Waters Treaty between Pakistan and India was signed in:",
       "1947", "1960", "1965", "1972", "B",
       "Signed in 1960 with World Bank mediation, allocating Indus basin rivers.", "easy", "past_paper"),
    _q("Who was the first Prime Minister of Pakistan?",
       "Liaquat Ali Khan", "Khawaja Nazimuddin", "Muhammad Ali Bogra", "Chaudhry Muhammad Ali", "A",
       "Liaquat Ali Khan served as first PM from 1947 until 1951.", "easy", "past_paper"),
    _q("The United Nations was founded in the year:",
       "1919", "1945", "1947", "1950", "B",
       "The UN Charter came into force on 24 October 1945.", "easy"),
    _q("Which is the longest river in the world?",
       "Amazon", "Nile", "Yangtze", "Mississippi", "B",
       "By conventional length rankings, the Nile is the longest (~6,650 km).", "medium"),
    _q("The currency of Japan is:",
       "Yuan", "Won", "Yen", "Ringgit", "C",
       "Japan's official currency is the yen (JPY).", "easy"),
    _q("SAARC headquarters are located in:",
       "New Delhi", "Islamabad", "Kathmandu", "Dhaka", "C",
       "SAARC Secretariat is in Kathmandu, Nepal.", "medium", "past_paper"),
    _q("Which country gifted the Statue of Liberty to the USA?",
       "Britain", "France", "Spain", "Italy", "B",
       "France presented the Statue of Liberty in 1886.", "easy"),
    _q("The Headquarters of the International Court of Justice is in:",
       "Geneva", "New York", "The Hague", "Vienna", "C",
       "ICJ sits in the Peace Palace at The Hague, Netherlands.", "medium", "past_paper"),
    _q("Olympic Games are held after every:",
       "2 years", "3 years", "4 years", "5 years", "C",
       "Summer Olympics are held every four years.", "easy"),
    _q("Which is the largest desert in the world?",
       "Gobi", "Sahara", "Arabian", "Antarctic (polar desert)", "D",
       "Antarctica is the largest desert by area; Sahara is the largest hot desert.", "hard"),
    _q("WTO stands for:",
       "World Trade Organization", "World Tourism Organization", "World Transport Office", "Wide Trade Order", "A",
       "The World Trade Organization deals with global trade rules.", "easy"),
    _q("The capital of Australia is:",
       "Sydney", "Melbourne", "Canberra", "Perth", "C",
       "Canberra was purpose-built as the federal capital.", "easy"),
]

# ── Mathematics ──────────────────────────────────────────────────────────────
MATHEMATICS = [
    _q("If 15% of a number is 45, then 40% of that number is:",
       "90", "100", "120", "150", "C",
       "Number = 45×100/15 = 300; 40% of 300 = 120.", "easy", "past_paper"),
    _q("The average of 5, 10, 15, 20 and 25 is:",
       "12", "15", "18", "20", "B",
       "Sum = 75; average = 75/5 = 15.", "easy"),
    _q("Solve: 2x + 5 = 17. Value of x is:",
       "4", "5", "6", "7", "C",
       "2x = 12 ⇒ x = 6.", "easy"),
    _q("A train covers 120 km in 2 hours. Its average speed is:",
       "40 km/h", "50 km/h", "60 km/h", "80 km/h", "C",
       "Speed = distance/time = 120/2 = 60 km/h.", "easy"),
    _q("Simple interest on Rs. 2000 at 5% per annum for 2 years is:",
       "Rs. 100", "Rs. 150", "Rs. 200", "Rs. 250", "C",
       "SI = PRT/100 = 2000×5×2/100 = 200.", "easy", "past_paper"),
    _q("The HCF of 12 and 18 is:",
       "2", "3", "6", "9", "C",
       "Common factors: 1, 2, 3, 6 — highest is 6.", "easy"),
    _q("If the ratio of two numbers is 3:5 and their sum is 40, the larger number is:",
       "15", "20", "25", "30", "C",
       "3x+5x=40 ⇒ x=5; larger = 25.", "medium"),
    _q("Area of a circle with radius 7 cm is (π = 22/7):",
       "144 cm²", "154 cm²", "164 cm²", "174 cm²", "B",
       "A = πr² = 22/7 × 49 = 154 cm².", "easy", "past_paper"),
    _q("(−3)² equals:",
       "−6", "−9", "6", "9", "D",
       "(−3)×(−3) = +9.", "easy"),
    _q("A shopkeeper buys an article for Rs. 80 and sells for Rs. 100. Profit % is:",
       "20%", "25%", "15%", "30%", "B",
       "Profit = 20; profit% = 20/80 × 100 = 25%.", "medium"),
    _q("The next number in the series 2, 6, 12, 20, 30, … is:",
       "40", "42", "44", "48", "B",
       "Differences increase by 2: +4,+6,+8,+10,+12 ⇒ 30+12=42.", "medium", "past_paper"),
    _q("√144 + √81 = ?",
       "21", "23", "25", "27", "A",
       "12 + 9 = 21.", "easy"),
    _q("If 3 workers finish a job in 8 days, 6 workers will finish it in:",
       "2 days", "3 days", "4 days", "6 days", "C",
       "Work ∝ workers × days; double workers ⇒ half time = 4 days.", "medium"),
    _q("The probability of getting a head in a fair coin toss is:",
       "0", "1/4", "1/2", "1", "C",
       "Two equally likely outcomes; P(head) = 1/2.", "easy"),
    _q("log₁₀ 1000 equals:",
       "2", "3", "4", "10", "B",
       "10³ = 1000, so log₁₀ 1000 = 3.", "medium"),
]

# ── Computer Science ─────────────────────────────────────────────────────────
COMPUTER_SCIENCE = [
    _q("Which data structure follows FIFO (First In, First Out)?",
       "Stack", "Queue", "Tree", "Graph", "B",
       "A queue processes elements in arrival order — FIFO.", "easy", "past_paper"),
    _q("CPU stands for:",
       "Central Processing Unit", "Computer Personal Unit", "Central Program Utility", "Control Processing Unit", "A",
       "The CPU is the primary processor of a computer.", "easy"),
    _q("Which of the following is volatile memory?",
       "ROM", "Hard disk", "RAM", "Flash drive", "C",
       "RAM loses contents when power is removed; it is volatile.", "easy", "past_paper"),
    _q("HTML is used to:",
       "Style web pages only", "Structure web content", "Query databases", "Compile programs", "B",
       "HTML (HyperText Markup Language) marks up structure of web documents.", "easy"),
    _q("Binary number 1010 in decimal is:",
       "8", "9", "10", "12", "C",
       "1×8 + 0×4 + 1×2 + 0×1 = 10.", "medium", "past_paper"),
    _q("Which protocol is used to send email?",
       "HTTP", "FTP", "SMTP", "SSH", "C",
       "SMTP (Simple Mail Transfer Protocol) transfers outbound email.", "medium"),
    _q("An operating system is:",
       "Application software", "System software", "Utility only", "Firmware only", "B",
       "OS manages hardware and provides services to applications.", "easy"),
    _q("1 Kilobyte equals:",
       "1000 bits", "1024 bytes", "1024 bits", "1000 bytes (always)", "B",
       "In binary computing, 1 KB = 1024 bytes.", "easy", "past_paper"),
    _q("Which language is primarily used for Android app development (officially recommended)?",
       "Swift", "Kotlin", "Ruby", "PHP", "B",
       "Google recommends Kotlin as the preferred language for Android.", "medium"),
    _q("IP address IPv4 typically consists of how many bits?",
       "16", "32", "64", "128", "B",
       "IPv4 addresses are 32-bit; IPv6 uses 128-bit.", "medium", "past_paper"),
    _q("Which is NOT an input device?",
       "Keyboard", "Mouse", "Scanner", "Monitor", "D",
       "A monitor is an output device.", "easy"),
    _q("SQL is mainly used for:",
       "Styling pages", "Managing relational databases", "Drawing graphics", "Compiling C++", "B",
       "Structured Query Language queries and manages RDBMS data.", "easy"),
    _q("In networking, LAN stands for:",
       "Large Area Network", "Local Area Network", "Long Access Node", "Logical Area Net", "B",
       "LAN connects devices in a limited geographic area.", "easy"),
    _q("The brain of the computer is often referred to as the:",
       "Monitor", "CPU", "Keyboard", "UPS", "B",
       "The CPU executes instructions and controls processing.", "easy"),
    _q("Which sorting algorithm has average time complexity O(n log n)?",
       "Bubble sort", "Insertion sort", "Merge sort", "Selection sort", "C",
       "Merge sort divides and conquers with O(n log n) average/worst case.", "hard"),
]

# ── English ──────────────────────────────────────────────────────────────────
ENGLISH = [
    _q("Choose the correctly spelled word:",
       "Accomodate", "Acommodate", "Accommodate", "Acomodate", "C",
       "'Accommodate' has double c and double m.", "easy", "past_paper"),
    _q("The synonym of 'Benevolent' is:",
       "Hostile", "Kind", "Greedy", "Ignorant", "B",
       "Benevolent means well-meaning and kindly.", "medium"),
    _q("Antonym of 'Scarce' is:",
       "Rare", "Abundant", "Limited", "Sparse", "B",
       "Scarce means insufficient; abundant means plentiful.", "easy"),
    _q("Identify the correct sentence:",
       "He don't know the answer.", "He doesn't knows the answer.", "He doesn't know the answer.", "He not know the answer.", "C",
       "Third-person singular uses doesn't + base verb.", "easy"),
    _q("'A blessing in disguise' means:",
       "A curse", "Something good that seemed bad at first", "An open gift", "A religious ritual", "B",
       "The idiom refers to an apparent misfortune that brings benefit.", "medium", "past_paper"),
    _q("Fill in: She has been working here _____ 2019.",
       "for", "since", "from", "by", "B",
       "'Since' is used with a starting point in time.", "easy"),
    _q("The plural of 'Crisis' is:",
       "Crisises", "Crisi", "Crises", "Crisis's", "C",
       "Greek-origin nouns: crisis → crises.", "medium"),
    _q("Choose the passive form: 'They built the bridge.'",
       "The bridge was built by them.", "The bridge is build by them.", "The bridge built them.", "The bridge has build.", "A",
       "Past simple active → was/were + past participle.", "easy", "past_paper"),
    _q("Which is a conjunction?",
       "Quickly", "Although", "Beautiful", "Under", "B",
       "'Although' joins clauses; it is a subordinating conjunction.", "easy"),
    _q("One who writes dictionaries is called a:",
       "Calligrapher", "Lexicographer", "Bibliographer", "Cartographer", "B",
       "A lexicographer compiles dictionaries.", "medium", "past_paper"),
    _q("'To hit the nail on the head' means:",
       "To injure someone", "To say exactly the right thing", "To carpentry well", "To argue loudly", "B",
       "The idiom means to be precisely correct.", "medium"),
    _q("Choose the correct article: ___ honest man.",
       "A", "An", "The only", "No article", "B",
       "'Honest' begins with a vowel sound /ɒ/, so 'an' is used.", "easy"),
]

# ── Biology (MDCAT) ──────────────────────────────────────────────────────────
BIOLOGY = [
    _q("The powerhouse of the cell is the:",
       "Nucleus", "Ribosome", "Mitochondrion", "Golgi apparatus", "C",
       "Mitochondria produce ATP via cellular respiration.", "easy", "past_paper"),
    _q("Which blood cells help in clotting?",
       "RBCs", "WBCs", "Platelets", "Plasma proteins only", "C",
       "Platelets (thrombocytes) initiate clot formation.", "easy"),
    _q("Insulin is secreted by:",
       "Thyroid", "Adrenal cortex", "Pancreas (β-cells)", "Pituitary", "C",
       "β-cells of islets of Langerhans secrete insulin.", "medium", "past_paper"),
    _q("The basic unit of heredity is the:",
       "Chromosome", "Gene", "Nucleus", "Protein", "B",
       "Genes are DNA segments that code for traits.", "easy"),
    _q("Nephrons are the functional units of the:",
       "Liver", "Lung", "Kidney", "Heart", "C",
       "Each kidney contains about a million nephrons for filtration.", "easy"),
    _q("Which vitamin deficiency causes scurvy?",
       "Vitamin A", "Vitamin B1", "Vitamin C", "Vitamin K", "C",
       "Lack of ascorbic acid (Vitamin C) causes scurvy.", "medium", "past_paper"),
    _q("Double fertilization is characteristic of:",
       "Algae", "Gymnosperms", "Angiosperms", "Bryophytes", "C",
       "Angiosperms show syngamy + triple fusion (double fertilization).", "hard"),
    _q("Human heart has how many chambers?",
       "Two", "Three", "Four", "Five", "C",
       "Two atria and two ventricles.", "easy"),
]

# ── Chemistry ────────────────────────────────────────────────────────────────
CHEMISTRY = [
    _q("Atomic number of Carbon is:",
       "4", "6", "8", "12", "B",
       "Carbon has 6 protons; atomic number = 6.", "easy", "past_paper"),
    _q("pH of pure water at 25°C is approximately:",
       "5", "6", "7", "8", "C",
       "Pure water is neutral with pH ≈ 7.", "easy"),
    _q("Which is an alkali metal?",
       "Calcium", "Sodium", "Aluminium", "Iron", "B",
       "Sodium (Group 1) is an alkali metal.", "easy"),
    _q("The chemical formula of sulphuric acid is:",
       "HCl", "HNO₃", "H₂SO₄", "H₃PO₄", "C",
       "Sulphuric acid is H₂SO₄.", "easy", "past_paper"),
    _q("Avogadro's number is approximately:",
       "6.02 × 10²³", "3.14 × 10⁸", "9.8 × 10⁹", "1.6 × 10⁻¹⁹", "A",
       "One mole contains ~6.022×10²³ particles.", "medium"),
    _q("Oxidation involves:",
       "Gain of electrons", "Loss of electrons", "Gain of protons only", "Loss of neutrons", "B",
       "Oxidation is loss of electrons (OIL RIG).", "medium", "past_paper"),
    _q("Which gas is produced when zinc reacts with dilute HCl?",
       "Oxygen", "Hydrogen", "Chlorine", "Nitrogen", "B",
       "Zn + 2HCl → ZnCl₂ + H₂.", "medium"),
]

# ── Physics ──────────────────────────────────────────────────────────────────
PHYSICS = [
    _q("The SI unit of electric current is:",
       "Volt", "Ohm", "Ampere", "Watt", "C",
       "Current is measured in amperes (A).", "easy", "past_paper"),
    _q("Speed of light in vacuum is approximately:",
       "3 × 10⁶ m/s", "3 × 10⁸ m/s", "3 × 10¹⁰ m/s", "3 × 10⁴ m/s", "B",
       "c ≈ 3×10⁸ m/s.", "easy"),
    _q("Newton's second law states F =:",
       "mv", "ma", "m/a", "a/m", "B",
       "Force equals mass times acceleration.", "easy", "past_paper"),
    _q("Which mirror is used in car headlamps?",
       "Plane", "Convex", "Concave", "Cylindrical only", "C",
       "Concave mirrors produce a parallel beam when source is at focus.", "medium"),
    _q("Work done is zero when force and displacement are:",
       "Parallel", "Anti-parallel", "Perpendicular", "Equal in magnitude", "C",
       "W = Fd cosθ; cos90° = 0.", "medium", "past_paper"),
    _q("Frequency of a wave is measured in:",
       "Metres", "Hertz", "Joules", "Newtons", "B",
       "Hertz (Hz) = cycles per second.", "easy"),
    _q("Escape velocity from Earth is about:",
       "5 km/s", "8 km/s", "11.2 km/s", "15 km/s", "C",
       "Earth's escape speed ≈ 11.2 km/s.", "hard"),
]

# ── Pakistan Studies / Affairs ───────────────────────────────────────────────
PAKISTAN_STUDIES = [
    _q("Pakistan Resolution was passed in:",
       "1930", "1940", "1947", "1956", "B",
       "Lahore Resolution of 23 March 1940 demanded independent Muslim states.", "easy", "past_paper"),
    _q("Who presented the Objectives Resolution?",
       "Liaquat Ali Khan", "Quaid-e-Azam", "Ayub Khan", "Zulfikar Ali Bhutto", "A",
       "Liaquat Ali Khan presented it in March 1949.", "medium", "past_paper"),
    _q("The Constitution of 1973 was enforced on:",
       "14 August 1973", "23 March 1973", "12 April 1973", "1 March 1973", "A",
       "The 1973 Constitution came into effect on 14 August 1973.", "medium"),
    _q("Allama Iqbal delivered the Allahabad Address in:",
       "1928", "1930", "1933", "1940", "B",
       "Iqbal's 1930 address envisioned a consolidated Muslim state in NW India.", "easy", "past_paper"),
    _q("The Rann of Kutch agreement was signed in:",
       "1965", "1966", "1968", "1971", "B",
       "Tribunal award related to 1965 conflict; agreement finalized mid-1960s (1966–68 process).", "hard"),
    _q("Which pass connects Pakistan with China?",
       "Khyber Pass", "Bolan Pass", "Khunjerab Pass", "Tochi Pass", "C",
       "Khunjerab Pass on the Karakoram Highway links Gilgit-Baltistan with Xinjiang.", "medium", "past_paper"),
    _q("Quaid-e-Azam died on:",
       "11 September 1948", "14 August 1948", "25 December 1947", "1 July 1948", "A",
       "Muhammad Ali Jinnah passed away on 11 September 1948.", "easy"),
    _q("The first Constitution of Pakistan was promulgated in:",
       "1947", "1956", "1962", "1973", "B",
       "Pakistan became an Islamic Republic under the 1956 Constitution.", "medium", "past_paper"),
    _q("Indus River originates from:",
       "Hindu Kush", "Tibetan Plateau", "Sulaiman Range", "Karakoram only", "B",
       "The Indus rises near Lake Manasarovar region on the Tibetan Plateau.", "medium"),
    _q("Who was the first Governor-General of Pakistan?",
       "Liaquat Ali Khan", "Muhammad Ali Jinnah", "Ghulam Muhammad", "Iskander Mirza", "B",
       "Quaid-e-Azam was the first Governor-General.", "easy", "past_paper"),
]

# ── Islamic Studies ──────────────────────────────────────────────────────────
ISLAMIC_STUDIES = [
    _q("How many Surahs are there in the Holy Quran?",
       "110", "114", "120", "99", "B",
       "The Quran contains 114 Surahs.", "easy", "past_paper"),
    _q("The first revealed Surah was:",
       "Al-Baqarah", "Al-Fatiha", "Al-Alaq", "An-Nas", "C",
       "First revelation was verses of Surah Al-Alaq.", "easy", "past_paper"),
    _q("Zakat is obligatory when wealth reaches the:",
       "Nisab", "Khums", "Fitrah only", "Jizya", "A",
       "Nisab is the minimum threshold making Zakat due.", "easy"),
    _q("The Battle of Badr took place in:",
       "1 AH", "2 AH", "3 AH", "5 AH", "B",
       "Badr occurred in 2 AH (624 CE).", "medium", "past_paper"),
    _q("Who compiled the Quran into a single book during the Caliphate after the Prophet (PBUH)?",
       "Hazrat Umar (RA) alone", "Hazrat Abu Bakr (RA)", "Hazrat Ali (RA) only", "Hazrat Uthman (RA) first only", "B",
       "Under Abu Bakr (RA), Zayd ibn Thabit compiled the mushaf; Uthman (RA) later standardized copies.", "medium"),
    _q("The number of Farz (obligatory) prayers in a day is:",
       "Three", "Four", "Five", "Six", "C",
       "Five daily Salah are obligatory: Fajr, Zuhr, Asr, Maghrib, Isha.", "easy"),
    _q("Hajj is performed in the month of:",
       "Ramadan", "Shawwal", "Dhul-Hijjah", "Muharram", "C",
       "Hajj rites occur in Dhul-Hijjah.", "easy", "past_paper"),
]

# ── Current Affairs (timeless + structural — avoid stale specifics) ───────────
CURRENT_AFFAIRS = [
    _q("G-20 is a forum of:",
       "Only European states", "Major advanced and emerging economies", "UN Security Council only", "SAARC members only", "B",
       "G20 brings together large advanced and emerging economies on global economic issues.", "medium"),
    _q("The IMF's main purpose is to:",
       "Run world elections", "Promote global monetary cooperation and financial stability", "Build highways", "Set oil prices only", "B",
       "IMF supports exchange stability and assists members with balance-of-payments issues.", "medium", "past_paper"),
    _q("COP conferences are primarily related to:",
       "Trade tariffs", "Climate change", "Space exploration", "Cybercrime only", "B",
       "Conference of the Parties under UNFCCC addresses climate change.", "easy"),
    _q("BRICS originally included Brazil, Russia, India, China and:",
       "Spain", "South Africa", "Singapore", "Sweden", "B",
       "South Africa joined in 2010; membership has since expanded further.", "medium"),
    _q("CPEC stands for:",
       "China–Pakistan Economic Corridor", "Central Pakistan Export Council", "China Port Expansion Contract", "Coastal Pakistan Energy Corridor", "A",
       "CPEC is a flagship BRI corridor linking Gwadar with Xinjiang.", "easy", "past_paper"),
    _q("The SCO is a regional organization focused mainly on:",
       "Football", "Security and regional cooperation in Eurasia", "Fashion", "Antarctic research only", "B",
       "Shanghai Cooperation Organisation addresses security, politics and economics among Eurasian members.", "medium"),
]

# ── Analytical / IQ ──────────────────────────────────────────────────────────
ANALYTICAL = [
    _q("Find the odd one out: 3, 5, 7, 9, 11",
       "3", "7", "9", "11", "C",
       "All except 9 are prime; 9 = 3×3.", "easy", "past_paper"),
    _q("If BOOK is coded as 45511, how is COOK coded? (B=4, O=5, K=1)",
       "45511", "55511", "35511", "45515", "B",
       "C=3? Wait — if pattern maps letters: B→4,O→5,O→5,K→1 then C→5? Better: often C=3. Correct coding if C→5 by position shift: use consistent: C=3 → 35511. Fix: many papers use position. Let's use: B=2,O=15→ use simpler.", "easy"),
]

# Fix the broken analytical question and expand properly
ANALYTICAL = [
    _q("Find the odd one out: 3, 5, 7, 9, 11",
       "3", "7", "9", "11", "C",
       "All except 9 are prime numbers.", "easy", "past_paper"),
    _q("Complete the series: 2, 6, 12, 20, 30, ?",
       "40", "42", "44", "48", "B",
       "Add consecutive even numbers starting at 4: +4,+6,+8,+10,+12.", "medium", "past_paper"),
    _q("If A is brother of B, B is sister of C, and C is brother of D, then D is ___ of A:",
       "Brother only", "Sister only", "Brother or sister", "Uncle", "C",
       "Gender of D is not specified; D is sibling of A.", "medium"),
    _q("A is taller than B but shorter than C. D is shorter than B. Who is tallest?",
       "A", "B", "C", "D", "C",
       "Order: C > A > B > D.", "easy", "past_paper"),
    _q("Which number replaces the question mark? 4, 9, 16, 25, ?",
       "30", "36", "49", "64", "B",
       "Squares: 2²,3²,4²,5²,6² = 36.", "easy"),
    _q("If all Bloops are Razzies and all Razzies are Lazzies, then all Bloops are definitely Lazzies.",
       "True", "False", "Uncertain", "Cannot say without numbers", "A",
       "Transitivity of 'all' statements makes it true.", "medium"),
    _q("Mirror image of the time 3:15 looks closest to:",
       "8:45", "9:45", "8:15", "3:15", "A",
       "Clock hands reverse around 12; 3:15 mirrors near 8:45.", "hard"),
    _q("In a certain code, CAT = 24 and DOG = 26. Then BAT = ?",
       "23", "24", "25", "26", "A",
       "If sum of positions: C3+A1+T20=24; D4+O15+G7=26; B2+A1+T20=23.", "hard", "past_paper"),
]

# ── History ──────────────────────────────────────────────────────────────────
HISTORY = [
    _q("The War of Independence (First War of Independence) in India started in:",
       "1857", "1847", "1867", "1877", "A",
       "The 1857 uprising began in Meerut and spread across North India.", "easy", "past_paper"),
    _q("Mughal Emperor Akbar introduced the:",
       "Doctrine of Lapse", "Din-i-Ilahi", "Permanent Settlement", "Subsidiary Alliance", "B",
       "Akbar promulgated Din-i-Ilahi as a syncretic faith circle.", "medium"),
    _q("The Ottoman Empire ended after:",
       "World War I", "World War II", "Crimean War", "Napoleonic Wars", "A",
       "The empire was dismantled after WWI; Republic of Turkey founded 1923.", "medium", "past_paper"),
    _q("Alexander invaded the Indus region around:",
       "326 BCE", "100 CE", "712 CE", "1526 CE", "A",
       "Alexander crossed the Indus and fought Porus at Hydaspes (~326 BCE).", "medium"),
    _q("The French Revolution began in:",
       "1688", "1776", "1789", "1815", "C",
       "Storming of the Bastille in 1789 marks the conventional start.", "easy", "past_paper"),
    _q("Who founded the Mughal Empire in India?",
       "Akbar", "Babur", "Humayun", "Sher Shah", "B",
       "Babur defeated Ibrahim Lodi at Panipat in 1526.", "easy", "past_paper"),
    _q("The Industrial Revolution began in:",
       "France", "Germany", "Britain", "USA", "C",
       "It started in Britain in the late 18th century.", "easy"),
    _q("Muhammad bin Qasim conquered Sindh in:",
       "712 CE", "711 AH only as year name", "1526 CE", "1857 CE", "A",
       "Umayyad general Muhammad bin Qasim took Debal/Sindh in 712 CE.", "medium", "past_paper"),
    _q("The Cold War was primarily between:",
       "UK and France", "USA and USSR", "China and Japan", "Germany and Italy", "B",
       "Post-1945 geopolitical rivalry between USA and Soviet Union.", "easy"),
    _q("Partition of Bengal by the British occurred in:",
       "1905", "1911 only as annulment year", "1947", "1857", "A",
       "Curzon partitioned Bengal in 1905 (annulled 1911).", "medium", "past_paper"),
]

# ── Urdu (basic competitive MCQs in English stem where needed) ───────────────
URDU = [
    _q("علامہ اقبال کی مشہور نظم 'شکوہ' کا جواب کون سی نظم ہے؟",
       "جوابِ شکوہ", "بالِ جبریل", "ضربِ کلیم", "ارمغانِ حجاز", "A",
       "'جوابِ شکوہ' علامہ اقبال کی نظم ہے جو 'شکوہ' کا جواب ہے۔", "medium", "past_paper"),
    _q("'اردو' زبان کا لفظی تعلق کس زبان سے بتایا جاتا ہے؟",
       "عربی", "ترکی (اردو = لشکر)", "انگریزی", "سنسکرت صرف", "B",
       "اردو کا لفظ ترکی زبان سے منسوب ہے جس کے معنی لشکر/فوج کے ہیں۔", "easy"),
    _q("غزل کی کم از کم تعدادِ اشعار کیا سمجھی جاتی ہے؟",
       "دو", "پانچ", "سات", "دس", "B",
       "روایتی طور پر غزل کم از کم پانچ اشعار پر مشتمل ہوتی ہے۔", "medium"),
    _q("مولانا حالی کی مشہور تصنیف ہے:",
       "آبِ حیات", "یدگارِ غالب", "اسفار", "باغ و بہار", "B",
       "حالی کی مشہور کتاب 'یدگارِ غالب' ہے۔", "medium", "past_paper"),
]

BANK: dict[str, list[dict[str, Any]]] = {
    "everyday science": EVERYDAY_SCIENCE,
    "general knowledge": GENERAL_KNOWLEDGE,
    "mathematics": MATHEMATICS,
    "computer science": COMPUTER_SCIENCE,
    "english": ENGLISH,
    "biology": BIOLOGY,
    "chemistry": CHEMISTRY,
    "physics": PHYSICS,
    "pakistan studies": PAKISTAN_STUDIES,
    "islamic studies": ISLAMIC_STUDIES,
    "current affairs": CURRENT_AFFAIRS,
    "analytical reasoning": ANALYTICAL,
    "history": HISTORY,
    "urdu": URDU,
}


def normalize_topic(topic_name: str) -> str:
    return _n(topic_name)


def get_topic_questions(topic_name: str) -> list[dict[str, Any]]:
    key = _n(topic_name)
    return list(BANK.get(key, []))


def pick_question(
    topic_name: str,
    difficulty: str = "medium",
    exclude_texts: set[str] | None = None,
) -> dict[str, Any] | None:
    """Pick a non-repeating, topic-true question. Prefer difficulty match."""
    exclude_texts = exclude_texts or set()
    pool = get_topic_questions(topic_name)
    if not pool:
        return None

    unused = [q for q in pool if q["text"] not in exclude_texts]
    if not unused:
        unused = pool  # wrap only if exhausted

    matching = [q for q in unused if q["difficulty"] == difficulty]
    choices = matching or unused
    q = dict(random.choice(choices))
    return q
