CRITICAL_PATTERNS = [
    "auth", "token", "jwt", "password", "payment", "stripe", "database", "execute", "eval"
]

def detect_sensitive_keywords(file_content):
    findings = []
    for keyword in CRITICAL_PATTERNS:
        if keyword in file_content.lower():
            findings.append(keyword)
    return findings