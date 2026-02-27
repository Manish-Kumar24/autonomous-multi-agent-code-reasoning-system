import os
class GovernancePolicy:
    # Risk weight multiplier
    RISK_WEIGHT = float(os.getenv("RISK_WEIGHT", 3))
    # Depth impact multiplier
    DEPTH_WEIGHT = float(os.getenv("DEPTH_WEIGHT", 10))
    # AI signal weights
    AI_LOW_WEIGHT = float(os.getenv("AI_LOW_WEIGHT", 20))
    AI_MEDIUM_WEIGHT = float(os.getenv("AI_MEDIUM_WEIGHT", 10))
    AI_HIGH_WEIGHT = float(os.getenv("AI_HIGH_WEIGHT", 0))
    # Thresholds
    BLOCK_THRESHOLD = float(os.getenv("BLOCK_THRESHOLD", 70))
    REVIEW_THRESHOLD = float(os.getenv("REVIEW_THRESHOLD", 40))