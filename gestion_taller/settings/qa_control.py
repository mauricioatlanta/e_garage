"""Explicit QA tenant matrix loaded by the effective settings package."""

# Audited production tenants. USA remains intentionally unavailable until its
# dedicated QA tenants are created and reviewed.
QA_CONTROL_TENANTS = {
    ("CL", "WORKSHOP"): 48,
    ("CL", "DESARMADURIA"): 49,
    ("CL", "PARTS"): 50,
    ("CL", "DETAILING"): 53,
    ("CL", "TIRE"): 54,
    ("CL", "EXHAUST"): 55,
    ("CL", "FLEET"): 56,
    ("CL", "MIXED"): 57,
}
