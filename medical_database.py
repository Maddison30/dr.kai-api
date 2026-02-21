# Medical condition database sourced from Swedish medical websites
# Format: condition -> {symptoms, causes, treatment, sources}

MEDICAL_DATABASE = {
    "shoulder pain": {
        "symptoms": [
            "Pain when raising arm",
            "Limited range of motion",
            "Stiffness",
            "Weakness",
            "Swelling or redness"
        ],
        "common_causes": [
            "Rotator cuff strain or tears",
            "Frozen shoulder (adhesive capsulitis)",
            "Shoulder dislocation",
            "Arthritis",
            "Bursitis",
            "Tendinitis",
            "Nerve compression"
        ],
        "treatment": [
            "Rest and ice for the first 48 hours",
            "Over-the-counter pain relief (paracetamol, ibuprofen)",
            "Physical therapy and exercises",
            "Heat therapy after initial inflammation",
            "Medical imaging (X-ray, MRI) if symptoms persist",
            "Specialist consultation if no improvement in 2-3 weeks"
        ],
        "urgent_signs": [
            "Severe sudden pain",
            "Loss of sensation",
            "Inability to move arm",
            "Signs of infection (fever, severe swelling)"
        ],
        "sources": [
            "https://www.1177.se/ - Swedish Healthcare Guide",
            "https://www.socialstyrelsen.se/ - National Board of Health and Welfare"
        ]
    },
    
    "headache": {
        "symptoms": [
            "Throbbing or pressure in head",
            "Pain on one or both sides",
            "Nausea or vomiting",
            "Sensitivity to light or sound",
            "Dizziness"
        ],
        "common_causes": [
            "Tension headache",
            "Migraine",
            "Stress",
            "Dehydration",
            "Lack of sleep",
            "Caffeine withdrawal",
            "Fever or infection"
        ],
        "treatment": [
            "Rest in a quiet, dark room",
            "Stay hydrated",
            "Over-the-counter pain relief (paracetamol, ibuprofen, aspirin)",
            "Apply cold or warm compress",
            "Relaxation techniques",
            "See a doctor if headaches are frequent or severe"
        ],
        "urgent_signs": [
            "Sudden severe headache (worst ever)",
            "Headache with fever and stiff neck",
            "Vision changes",
            "Weakness or numbness",
            "Confusion or difficulty speaking"
        ],
        "sources": [
            "https://www.1177.se/ - Swedish Healthcare Guide",
            "https://www.socialstyrelsen.se/ - National Board of Health and Welfare"
        ]
    },
    
    "back pain": {
        "symptoms": [
            "Aching, sharp, or burning pain",
            "Stiffness",
            "Reduced mobility",
            "Pain radiating to legs",
            "Numbness or tingling"
        ],
        "common_causes": [
            "Muscle strain",
            "Poor posture",
            "Disc problems",
            "Osteoarthritis",
            "Sciatica",
            "Lifestyle factors (sedentary work)",
            "Injuries"
        ],
        "treatment": [
            "Rest and activity modification",
            "Heat or ice therapy",
            "Over-the-counter pain relief",
            "Physical therapy and stretching",
            "Maintain good posture",
            "Regular exercise",
            "Medical imaging if persistent"
        ],
        "urgent_signs": [
            "Sudden severe pain",
            "Pain after trauma/fall",
            "Bowel or bladder dysfunction",
            "Weakness in legs",
            "Fever with back pain"
        ],
        "sources": [
            "https://www.1177.se/ - Swedish Healthcare Guide",
            "https://www.socialstyrelsen.se/ - National Board of Health and Welfare"
        ]
    },
    
    "fever": {
        "symptoms": [
            "Body temperature above 38°C",
            "Chills",
            "Sweating",
            "Weakness",
            "Headache",
            "Muscle aches"
        ],
        "common_causes": [
            "Common cold",
            "Influenza",
            "Infection",
            "COVID-19",
            "Other viral infections",
            "Bacterial infections",
            "Inflammatory conditions"
        ],
        "treatment": [
            "Rest and stay hydrated",
            "Paracetamol or ibuprofen",
            "Cool compresses",
            "Wear light clothing",
            "Monitor temperature",
            "See a doctor if fever persists or worsens"
        ],
        "urgent_signs": [
            "Fever above 40°C",
            "Difficulty breathing",
            "Chest pain",
            "Severe headache with stiff neck",
            "Confusion or dizziness",
            "Persistent high fever"
        ],
        "sources": [
            "https://www.1177.se/ - Swedish Healthcare Guide",
            "https://www.socialstyrelsen.se/ - National Board of Health and Welfare"
        ]
    },
    
    "joint pain": {
        "symptoms": [
            "Pain in joints",
            "Swelling",
            "Stiffness",
            "Reduced range of motion",
            "Redness around joint",
            "Warmth"
        ],
        "common_causes": [
            "Osteoarthritis",
            "Rheumatoid arthritis",
            "Injury or strain",
            "Gout",
            "Bursitis",
            "Inflammation",
            "Aging"
        ],
        "treatment": [
            "Rest and elevation",
            "Ice or heat therapy",
            "Over-the-counter pain relief",
            "Gentle movement and stretching",
            "Physical therapy",
            "Weight management",
            "Medical evaluation for persistent pain"
        ],
        "urgent_signs": [
            "Sudden severe swelling",
            "Unable to move joint",
            "Signs of infection",
            "Severe pain without improvement"
        ],
        "sources": [
            "https://www.1177.se/ - Swedish Healthcare Guide",
            "https://www.socialstyrelsen.se/ - National Board of Health and Welfare"
        ]
    }
}

def find_medical_condition(query: str) -> dict:
    """Search the medical database for conditions matching the query."""
    query_lower = query.lower()
    
    # Exact match
    if query_lower in MEDICAL_DATABASE:
        return MEDICAL_DATABASE[query_lower]
    
    # Partial match
    for condition, info in MEDICAL_DATABASE.items():
        if condition in query_lower or query_lower in condition:
            return info
    
    # Search in symptoms
    for condition, info in MEDICAL_DATABASE.items():
        for symptom in info.get("symptoms", []):
            if symptom.lower() in query_lower or query_lower in symptom.lower():
                return info
    
    return None
