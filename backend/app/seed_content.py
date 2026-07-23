"""Detailed notes, essay prompts, and past-paper style sets."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Topic, ExamTrack, TopicNote, EssayPrompt, PastPaper, PastPaperQuestion
from app.services.question_bank import normalize_topic, get_topic_questions

# Canonical note bodies keyed like question bank
NOTES: dict[str, list[dict]] = {
    "everyday science": [
        {
            "title": "Human Body & Life Processes",
            "summary": "Core biology for job tests and CSS Everyday Science.",
            "key_points": "Cells → tissues → organs\nPhotosynthesis in chloroplasts\nKidneys filter blood\nHeart has 4 chambers\nVitamins: A,B,C,D,K roles",
            "content": """## Cells and energy
Living cells use **mitochondria** for ATP and **chloroplasts** (plants) for photosynthesis.

## Body systems (high-yield)
- **Circulatory:** heart pumps blood; RBCs carry O₂; platelets clot.
- **Excretory:** nephrons in kidneys remove urea.
- **Nervous:** brain + spinal cord; neurons transmit impulses.
- **Endocrine:** hormones (e.g. insulin from pancreas β-cells).

## Everyday chemistry links
- Water pH ≈ 7; acids < 7; bases > 7.
- Ozone O₃ protects from UV; CO₂ drives greenhouse effect.
- Antibiotics kill **bacteria**, not viruses.

## Physics of daily life
- Sound needs a medium (no sound in vacuum).
- Force unit: Newton; current: Ampere; frequency: Hertz.
""",
        },
        {
            "title": "Environment, Space & Materials",
            "summary": "Atmosphere, planets, hardness, and common materials.",
            "key_points": "N₂ ~78% of air\nMars = Red Planet\nDiamond hardest natural\nVitamin D from sunlight",
            "content": """## Atmosphere
Dry air ≈ **78% nitrogen**, 21% oxygen, ~0.9% argon, CO₂ traces.

## Solar system quick facts
- **Mars** appears red due to iron oxide.
- Earth–Sun light travel ~8 minutes; c ≈ 3×10⁸ m/s.

## Materials
- Diamond is the hardest natural substance (Mohs 10).
- Metals conduct heat/electricity; non-metals generally do not.
""",
        },
    ],
    "mathematics": [
        {
            "title": "Percentages, Ratios & Averages",
            "summary": "Most frequent NTS/PPSC quantitative types.",
            "key_points": "x% of N = x/100 × N\nRatio a:b and sum S → parts a+b\nAverage = sum/n\nSI = PRT/100",
            "content": """## Percentages
If 15% of N = 45 → N = 45 × 100/15 = 300.

## Profit & loss
Profit% = (Profit / Cost Price) × 100.

## Simple Interest
SI = (P × R × T) / 100.

## Ratios
If a:b = 3:5 and a+b = 40 → 8x=40 → x=5 → numbers 15 and 25.
""",
        },
        {
            "title": "Algebra, Geometry & Series",
            "summary": "Equations, area, and number series patterns.",
            "key_points": "2x+5=17 → x=6\nArea circle = πr²\nSquare series: 4,9,16,25,36",
            "content": """## Linear equations
Isolate the variable: 2x + 5 = 17 → 2x = 12 → x = 6.

## Geometry
Circle area = πr². With r=7 and π=22/7 → 154.

## Series
Look at differences or squares/cubes. 2,6,12,20,30 → differences +4,+6,+8,+10 → next +12 = 42.
""",
        },
    ],
    "computer science": [
        {
            "title": "Hardware, Memory & OS",
            "summary": "Foundations asked in NTS/NET computer sections.",
            "key_points": "CPU = processing\nRAM volatile; ROM non-volatile\n1 KB = 1024 bytes\nOS = system software",
            "content": """## Hardware
- **CPU:** executes instructions (ALU + CU + registers).
- **Input vs output:** keyboard/mouse in; monitor/printer out.

## Memory
- **RAM** is volatile (lost on power-off).
- **ROM/Flash** retain data without power.
- 1 KB = 1024 bytes (binary).

## Operating systems
Manage processes, memory, files, and device I/O. Examples: Windows, Linux, Android.
""",
        },
        {
            "title": "Networks, Databases & Logic",
            "summary": "Internet protocols, SQL, and data structures.",
            "key_points": "SMTP = email send\nHTTP = web\nSQL for RDBMS\nQueue = FIFO; Stack = LIFO\nIPv4 = 32-bit",
            "content": """## Networking
- **LAN** = local area network.
- **SMTP** sends email; **HTTP/HTTPS** for web; **FTP** for file transfer.
- IPv4 = 32-bit addresses; IPv6 = 128-bit.

## Data structures
- **Queue:** FIFO · **Stack:** LIFO.
- Merge sort average O(n log n).

## Databases
SQL queries relational tables (SELECT, INSERT, JOIN).
""",
        },
    ],
    "english": [
        {
            "title": "Grammar Essentials",
            "summary": "Articles, tenses, voice, and agreement.",
            "key_points": "an honest (vowel sound)\nsince + point in time; for + duration\nPassive: was/were + V3",
            "content": """## Articles
Use **an** before vowel **sounds** (an hour, an honest man).

## Tenses & agreement
He **doesn't know** (not don't / doesn't knows).

## Active → Passive
They built the bridge → The bridge **was built** by them.
""",
        },
        {
            "title": "Vocabulary & Idioms",
            "summary": "Synonyms, antonyms, and common idioms.",
            "key_points": "Benevolent ≈ kind\nScarce ≠ abundant\nBlessing in disguise = hidden good",
            "content": """## High-frequency words
- Benevolent → kind / charitable
- Scarce → antonym abundant
- Lexicographer → writes dictionaries

## Idioms
- Blessing in disguise
- Hit the nail on the head = exactly right
""",
        },
    ],
    "pakistan studies": [
        {
            "title": "Freedom Movement & Early Years",
            "summary": "1905–1948 milestones for CSS/PPSC.",
            "key_points": "1905 Bengal partition\n1930 Allahabad Address\n1940 Lahore Resolution\n1947 Independence\n1948 Quaid's death",
            "content": """## Timeline
- **1905:** Partition of Bengal (annulled 1911).
- **1930:** Iqbal's Allahabad Address.
- **23 Mar 1940:** Lahore Resolution.
- **14 Aug 1947:** Independence.
- **11 Sep 1948:** Quaid-e-Azam dies.

## Leadership
Quaid-e-Azam = first Governor-General; Liaquat Ali Khan = first Prime Minister.
""",
        },
        {
            "title": "Constitution & Geography",
            "summary": "1956/1962/1973 constitutions and physical geography.",
            "key_points": "1956 first constitution\n1973 enforced 14 Aug 1973\nKhunjerab Pass → China\nIndus from Tibetan Plateau",
            "content": """## Constitutions
- **1956:** First constitution; Islamic Republic.
- **1973:** Current constitution; enforced **14 August 1973**.
- **Objectives Resolution (1949):** presented by Liaquat Ali Khan.

## Geography
- **Khunjerab Pass** links Pakistan–China.
- Indus originates near the Tibetan Plateau region.
""",
        },
    ],
    "islamic studies": [
        {
            "title": "Quran, Pillars & Seerah Basics",
            "summary": "High-frequency Islamiat MCQs.",
            "key_points": "114 Surahs\nFirst revelation Al-Alaq\n5 daily prayers\nHajj in Dhul-Hijjah\nBadr in 2 AH",
            "content": """## Quran
- **114 Surahs**; first revelation from **Al-Alaq**.
- Compilation begun under **Abu Bakr (RA)**; standardized under **Uthman (RA)**.

## Pillars
Shahadah, Salah (5), Zakat (nisab), Sawm, Hajj (Dhul-Hijjah).

## Seerah
Battle of **Badr: 2 AH**.
""",
        },
    ],
    "history": [
        {
            "title": "Subcontinent & World Landmarks",
            "summary": "Empires, 1857, modern revolutions.",
            "key_points": "712 CE Muhammad bin Qasim\n1526 Babur / Panipat\n1857 War of Independence\n1789 French Revolution\nWWI ends Ottomans",
            "content": """## Subcontinent
- **712 CE:** Muhammad bin Qasim in Sindh.
- **1526:** Babur founds Mughal Empire (Panipat).
- **1857:** War of Independence.

## World
- **1789:** French Revolution.
- Industrial Revolution begins in **Britain**.
- Ottoman collapse after **World War I**.
""",
        },
    ],
    "general knowledge": [
        {
            "title": "World Organizations & Facts",
            "summary": "UN, SAARC, ICJ, treaties.",
            "key_points": "UN 1945\nSAARC HQ Kathmandu\nICJ The Hague\nIndus Waters Treaty 1960",
            "content": """## Organizations
- UN founded **1945**.
- SAARC HQ: **Kathmandu**.
- ICJ: **The Hague**.
- WTO: World Trade Organization.

## Pakistan-linked GK
Indus Waters Treaty **1960**; first PM **Liaquat Ali Khan**.
""",
        },
    ],
    "biology": [
        {
            "title": "Cell Biology & Human Physiology",
            "summary": "MDCAT core notes.",
            "key_points": "Mitochondria = ATP\nGene = heredity unit\nInsulin from β-cells\n4-chambered heart",
            "content": """## Cell
Mitochondria → ATP; nucleus → DNA; ribosomes → protein synthesis.

## Human body
Insulin from pancreatic β-cells; nephron = kidney unit; platelets clot blood.
""",
        },
    ],
    "chemistry": [
        {
            "title": "Atomic Structure & Reactions",
            "summary": "ECAT/MDCAT chemistry essentials.",
            "key_points": "C atomic number 6\nH₂SO₄ sulphuric acid\nOxidation = loss of e−\nAvogadro 6.02×10²³",
            "content": """## Basics
Atomic number = protons. Carbon = 6.

## Acids
H₂SO₄ = sulphuric acid. Neutral pH ≈ 7.

## Redox
Oxidation = loss of electrons; reduction = gain.
""",
        },
    ],
    "physics": [
        {
            "title": "Mechanics & Electricity",
            "summary": "NET/ECAT physics backbone.",
            "key_points": "F=ma\nCurrent in Ampere\nc≈3×10⁸ m/s\nW=0 when F ⊥ d",
            "content": """## Mechanics
Newton II: F = ma. Work W = Fd cosθ (zero if perpendicular).

## Waves & EM
c ≈ 3×10⁸ m/s. Frequency in Hertz. Current in Amperes.
""",
        },
    ],
    "analytical reasoning": [
        {
            "title": "Series, Odd-One-Out & Logic",
            "summary": "NTS IQ patterns.",
            "key_points": "Check primes / squares\nDifference patterns\nTransitivity of 'all'\nOrder comparisons",
            "content": """## Series
Squares: 4,9,16,25,36. Difference growth: +4,+6,+8…

## Odd one out
Often the non-prime, non-multiple, or different category.

## Syllogisms
If all A are B and all B are C → all A are C.
""",
        },
    ],
    "current affairs": [
        {
            "title": "Global Forums & Pakistan Diplomacy",
            "summary": "Stable frameworks rather than daily news.",
            "key_points": "IMF monetary stability\nCOP = climate\nCPEC corridor\nG20 major economies\nSCO Eurasia security",
            "content": """## Must-know acronyms
- **IMF:** monetary cooperation / BoP support.
- **COP:** climate change conferences (UNFCCC).
- **CPEC:** China–Pakistan Economic Corridor.
- **G20 / SCO / BRICS:** major plurilateral forums.
""",
        },
    ],
    "urdu": [
        {
            "title": "ادب اور لسانیات — بنیادی نوٹس",
            "summary": "غزل، اقبال، حالی — امتحانی نکات۔",
            "key_points": "شکوہ → جوابِ شکوہ\nاردو = لشکر (ترکی)\nغزل کم از کم ۵ اشعار",
            "content": """## اہم نکات
- علامہ اقبال کی نظم **شکوہ** کا جواب **جوابِ شکوہ** ہے۔
- لفظ اردو ترکی زبان سے منسوب ہے (معنی: لشکر)۔
- غزل عموماً کم از کم پانچ اشعار پر مشتمل ہوتی ہے۔
""",
        },
    ],
}

ESSAYS: dict[str, list[dict]] = {
    "pakistan studies": [
        {
            "title": "Ideology of Pakistan",
            "prompt": "Explain the Ideology of Pakistan with reference to the Quaid-e-Azam and Allama Iqbal. Discuss how it shaped the demand for a separate homeland.",
            "outline": "1. Introduction: Two-Nation Theory\n2. Iqbal's vision (1930)\n3. Quaid's speeches & leadership\n4. Lahore Resolution 1940\n5. Conclusion: relevance today",
            "word_limit": 300,
            "difficulty": "medium",
        },
        {
            "title": "Problems of Federation in Pakistan",
            "prompt": "Discuss the major challenges to federalism in Pakistan and suggest reforms for provincial harmony.",
            "outline": "1. Definition of federation\n2. Centre–province tensions\n3. NFC / resource sharing\n4. 18th Amendment impact\n5. Way forward",
            "word_limit": 350,
            "difficulty": "hard",
        },
    ],
    "current affairs": [
        {
            "title": "Climate Change and Pakistan",
            "prompt": "Analyse how climate change threatens Pakistan's economy and security. Propose a policy roadmap.",
            "outline": "1. Evidence: floods, heatwaves, glaciers\n2. Agriculture & water security\n3. Energy transition\n4. International climate finance\n5. Recommendations",
            "word_limit": 300,
            "difficulty": "medium",
        },
    ],
    "english": [
        {
            "title": "Education System of Pakistan",
            "prompt": "Write an essay on reforming Pakistan's education system to meet 21st-century needs.",
            "outline": "1. Current challenges\n2. Curriculum & skills gap\n3. Equity (gender/rural)\n4. Technology & teachers\n5. Conclusion",
            "word_limit": 250,
            "difficulty": "medium",
        },
        {
            "title": "Role of Youth in Nation Building",
            "prompt": "Discuss the role of youth in Pakistan's social, economic, and political development.",
            "outline": "1. Demographic dividend\n2. Education & entrepreneurship\n3. Civic participation\n4. Challenges (unemployment)\n5. Conclusion",
            "word_limit": 250,
            "difficulty": "easy",
        },
    ],
    "islamic studies": [
        {
            "title": "Concept of Justice in Islam",
            "prompt": "Elaborate the Islamic concept of Adl (justice) with Quranic references and its application in society.",
            "outline": "1. Meaning of Adl\n2. Quranic injunctions\n3. Prophetic example\n4. Social/economic justice\n5. Conclusion",
            "word_limit": 280,
            "difficulty": "medium",
        },
    ],
    "history": [
        {
            "title": "Causes of the 1857 War of Independence",
            "prompt": "Examine the political, economic, and socio-religious causes of the 1857 uprising in India.",
            "outline": "1. Background Company rule\n2. Political annexations\n3. Economic exploitation\n4. Socio-religious triggers\n5. Consequences",
            "word_limit": 300,
            "difficulty": "medium",
        },
    ],
    "general knowledge": [
        {
            "title": "Globalization: Pros and Cons",
            "prompt": "Critically evaluate globalization with special reference to developing countries like Pakistan.",
            "outline": "1. Definition\n2. Benefits (trade, tech)\n3. Costs (inequality, culture)\n4. Pakistan case\n5. Balanced conclusion",
            "word_limit": 280,
            "difficulty": "medium",
        },
    ],
}


def _ensure_topics(db: Session) -> None:
    """Add History (and other missing) topics to exams that should have them."""
    extras = {
        "CSS": ["History", "Essay Writing"],
        "FPSC": ["History"],
        "NTS": ["History"],
        "PPSC": ["History"],
        "OTS": ["History"],
    }
    tracks = db.query(ExamTrack).all()
    for track in tracks:
        wanted = extras.get(track.code, [])
        existing = {t.name for t in track.topics}
        for name in wanted:
            if name not in existing:
                db.add(Topic(exam_track_id=track.id, name=name, description=f"{name} for {track.code}"))
    db.commit()


def seed_learning_content(db: Session | None = None) -> None:
    close = False
    if db is None:
        from app.database import SessionLocal

        db = SessionLocal()
        close = True
    try:
        _ensure_topics(db)
        topics = db.query(Topic).all()
        if not topics:
            return

        # Notes — seed per topic if empty for that topic
        for topic in topics:
            key = normalize_topic(topic.name)
            if key == "essay writing":
                key = "english"
            if db.query(TopicNote).filter(TopicNote.topic_id == topic.id).count() > 0:
                continue
            for i, note in enumerate(NOTES.get(key, [])):
                db.add(
                    TopicNote(
                        topic_id=topic.id,
                        title=note["title"],
                        summary=note["summary"],
                        content=note["content"],
                        key_points=note["key_points"],
                        order_index=i,
                    )
                )
            # Generic stub if no curated note
            if key not in NOTES:
                db.add(
                    TopicNote(
                        topic_id=topic.id,
                        title=f"{topic.name} — Revision Sheet",
                        summary=f"Core revision points for {topic.name}.",
                        content=f"## {topic.name}\n\nFocus on definitions, landmark facts, and past-paper patterns for this topic under your exam track.\n\nPractice adaptive MCQs and past papers after reading.",
                        key_points=f"Revise definitions\nPractice MCQs\nReview past papers\nTrack weak sub-areas",
                        order_index=0,
                    )
                )

        # Essays
        for topic in topics:
            key = normalize_topic(topic.name)
            if key == "essay writing":
                key = "english"
            if db.query(EssayPrompt).filter(EssayPrompt.topic_id == topic.id).count() > 0:
                continue
            for essay in ESSAYS.get(key, []):
                db.add(
                    EssayPrompt(
                        topic_id=topic.id,
                        title=essay["title"],
                        prompt=essay["prompt"],
                        outline=essay["outline"],
                        word_limit=essay["word_limit"],
                        difficulty=essay["difficulty"],
                    )
                )

        # Past papers — one set per exam×topic using bank questions marked past_paper
        for topic in topics:
            if db.query(PastPaper).filter(PastPaper.topic_id == topic.id).count() > 0:
                continue
            key = normalize_topic(topic.name)
            qs = [q for q in get_topic_questions(topic.name) if q.get("source") == "past_paper"]
            if not qs:
                qs = get_topic_questions(topic.name)[:8]
            if not qs:
                continue
            track = db.get(ExamTrack, topic.exam_track_id)
            year = "2018–2024"
            paper = PastPaper(
                exam_track_id=topic.exam_track_id,
                topic_id=topic.id,
                title=f"{track.code if track else 'Exam'} — {topic.name} Past Paper Mix",
                year=year,
                description=f"Curated past-paper style MCQs for {topic.name}, aligned with {track.name if track else 'exam'} patterns.",
            )
            db.add(paper)
            db.flush()
            for i, q in enumerate(qs[:12]):
                db.add(
                    PastPaperQuestion(
                        past_paper_id=paper.id,
                        text=q["text"],
                        option_a=q["option_a"],
                        option_b=q["option_b"],
                        option_c=q["option_c"],
                        option_d=q["option_d"],
                        correct_option=q["correct_option"],
                        explanation=q["explanation"],
                        order_index=i,
                    )
                )

        db.commit()
    finally:
        if close:
            db.close()
