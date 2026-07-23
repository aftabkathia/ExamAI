from app.database import SessionLocal
from app.models import ExamTrack, Topic

EXAMS = [
    {
        "code": "CSS",
        "name": "CSS — Central Superior Services",
        "category": "academic",
        "description": "Pakistan's premier civil service exam covering GK, English, Pakistan Affairs, Islamiat, and optional subjects.",
        "icon": "landmark",
        "topics": [
            "Current Affairs",
            "Pakistan Affairs",
            "Islamic Studies",
            "English Precis & Composition",
            "General Science & Ability",
            "Everyday Science",
            "History",
            "Essay Writing",
        ],
    },
    {
        "code": "MDCAT",
        "name": "MDCAT — Medical & Dental College",
        "category": "academic",
        "description": "Entrance test for medical and dental colleges covering Biology, Chemistry, Physics, and English.",
        "icon": "heart-pulse",
        "topics": ["Biology", "Chemistry", "Physics", "English", "Logical Reasoning"],
    },
    {
        "code": "ECAT",
        "name": "ECAT — Engineering College Admission",
        "category": "academic",
        "description": "Engineering university admission test focused on Mathematics, Physics, Chemistry, and English.",
        "icon": "cpu",
        "topics": ["Mathematics", "Physics", "Chemistry", "English"],
    },
    {
        "code": "NET",
        "name": "NET — NUST Entrance Test",
        "category": "academic",
        "description": "NUST entrance exam with Mathematics, Physics, Chemistry/Computer Science, and English.",
        "icon": "graduation-cap",
        "topics": ["Mathematics", "Physics", "Chemistry", "Computer Science", "English"],
    },
    {
        "code": "NTS",
        "name": "NTS — National Testing Service",
        "category": "government",
        "description": "Widely used aptitude tests for government and private sector recruitment across Pakistan.",
        "icon": "clipboard-list",
        "topics": [
            "General Knowledge",
            "IQ / Analytical Reasoning",
            "Mathematics",
            "English",
            "Computer Science",
            "Everyday Science",
            "Pakistan Studies",
            "Islamic Studies",
            "History",
        ],
    },
    {
        "code": "PPSC",
        "name": "PPSC — Punjab Public Service Commission",
        "category": "government",
        "description": "Punjab provincial civil service and departmental recruitment exams.",
        "icon": "building-2",
        "topics": [
            "General Knowledge",
            "Pakistan Studies",
            "Current Affairs",
            "Islamic Studies",
            "English",
            "Urdu",
            "Mathematics",
            "Computer Literacy",
            "History",
        ],
    },
    {
        "code": "FPSC",
        "name": "FPSC — Federal Public Service Commission",
        "category": "government",
        "description": "Federal government recruitment exams including CSS screening and departmental posts.",
        "icon": "scale",
        "topics": [
            "General Knowledge",
            "Current Affairs",
            "Pakistan Affairs",
            "Islamic Studies",
            "English",
            "Everyday Science",
            "Analytical Reasoning",
            "History",
        ],
    },
    {
        "code": "OTS",
        "name": "OTS-Style Job Tests",
        "category": "government",
        "description": "Open Testing Service and similar MCQ patterns for various government job openings.",
        "icon": "briefcase",
        "topics": [
            "General Knowledge",
            "IQ / Analytical Reasoning",
            "Mathematics",
            "English",
            "Computer Science",
            "Everyday Science",
            "Pakistan Studies",
            "History",
        ],
    },
]


def seed_exams() -> None:
    db = SessionLocal()
    try:
        if db.query(ExamTrack).count() > 0:
            return
        for exam in EXAMS:
            track = ExamTrack(
                code=exam["code"],
                name=exam["name"],
                category=exam["category"],
                description=exam["description"],
                icon=exam["icon"],
            )
            db.add(track)
            db.flush()
            for topic_name in exam["topics"]:
                db.add(
                    Topic(
                        exam_track_id=track.id,
                        name=topic_name,
                        description=f"{topic_name} for {exam['code']}",
                    )
                )
        db.commit()
    finally:
        db.close()
