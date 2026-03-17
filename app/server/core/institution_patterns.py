"""
Canadian brokerage institution detection patterns.
Each pattern includes regex patterns for text matching and account type mappings.
"""

import re

INSTITUTION_PATTERNS = [
    {
        "name": "RBC Direct Investing",
        "patterns": [r"rbc\s+direct\s+investing", r"royal\s+bank", r"rbc\s+dominion", r"rbcdirectinvesting"],
        "account_patterns": {
            "RRSP": [r"rrsp", r"registered\s+retirement\s+savings"],
            "TFSA": [r"tfsa", r"tax.free\s+savings"],
            "RESP": [r"resp", r"registered\s+education"],
            "Non-Registered": [r"non.reg", r"margin", r"cash\s+account"],
            "RRIF": [r"rrif", r"retirement\s+income\s+fund"],
        },
    },
    {
        "name": "TD Direct Investing",
        "patterns": [r"td\s+direct\s+investing", r"td\s+waterhouse", r"td\s+wealth"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "RESP": [r"resp"],
            "Non-Registered": [r"non.reg", r"margin"],
            "RRIF": [r"rrif"],
        },
    },
    {
        "name": "Wealthsimple",
        "patterns": [r"wealthsimple", r"wealth\s+simple"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"personal", r"non.reg"],
            "FHSA": [r"fhsa", r"first\s+home"],
        },
    },
    {
        "name": "Questrade",
        "patterns": [r"questrade"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "RESP": [r"resp"],
            "Non-Registered": [r"margin", r"non.reg"],
            "LIRA": [r"lira", r"locked.in"],
        },
    },
    {
        "name": "BMO InvestorLine",
        "patterns": [r"bmo\s+investorline", r"bmo\s+nesbitt", r"bank\s+of\s+montreal"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"non.reg", r"cash"],
        },
    },
    {
        "name": "CIBC Investor's Edge",
        "patterns": [r"cibc\s+investor", r"cibc\s+wood\s+gundy"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"non.reg"],
        },
    },
    {
        "name": "Scotia iTRADE",
        "patterns": [r"scotia\s+itrade", r"scotiabank", r"scotia\s+mcleod"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"non.reg"],
        },
    },
    {
        "name": "National Bank Direct Brokerage",
        "patterns": [r"national\s+bank", r"banque\s+nationale", r"nbdb"],
        "account_patterns": {
            "RRSP": [r"rrsp", r"reer"],
            "TFSA": [r"tfsa", r"celi"],
            "Non-Registered": [r"non.reg"],
        },
    },
    {
        "name": "Desjardins Online Brokerage",
        "patterns": [r"desjardins", r"disnat"],
        "account_patterns": {
            "RRSP": [r"rrsp", r"reer"],
            "TFSA": [r"tfsa", r"celi"],
            "Non-Registered": [r"non.reg"],
        },
    },
    {
        "name": "Manulife Securities",
        "patterns": [r"manulife\s+securities", r"manulife\s+investment"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"non.reg"],
        },
    },
    {
        "name": "Sun Life",
        "patterns": [r"sun\s+life", r"sunlife"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
        },
    },
    {
        "name": "Great-West Lifeco",
        "patterns": [r"great.west", r"canada\s+life", r"london\s+life"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
        },
    },
    {
        "name": "IG Wealth Management",
        "patterns": [r"ig\s+wealth", r"investors\s+group"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"non.reg"],
        },
    },
    {
        "name": "Edward Jones",
        "patterns": [r"edward\s+jones"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"non.reg"],
        },
    },
    {
        "name": "CI Direct Investing",
        "patterns": [r"ci\s+direct", r"ci\s+investment", r"virtual\s+brokers"],
        "account_patterns": {
            "RRSP": [r"rrsp"],
            "TFSA": [r"tfsa"],
            "Non-Registered": [r"non.reg"],
        },
    },
]


def detect_institution(text: str) -> dict:
    """
    Detect the brokerage institution from statement text.
    Returns: { name, confidence, account_types_found }
    """
    text_lower = text.lower()

    for inst in INSTITUTION_PATTERNS:
        for pattern in inst["patterns"]:
            if re.search(pattern, text_lower):
                # Detect account types
                account_types = []
                for acct_type, acct_patterns in inst.get("account_patterns", {}).items():
                    for ap in acct_patterns:
                        if re.search(ap, text_lower):
                            account_types.append(acct_type)
                            break

                return {
                    "name": inst["name"],
                    "confidence": 0.9,
                    "account_types_found": list(set(account_types)),
                }

    return {
        "name": "Unknown",
        "confidence": 0.1,
        "account_types_found": [],
    }


def detect_account_type(text: str) -> str:
    """Detect account type from a text section."""
    text_lower = text.lower()

    patterns = [
        ("RRSP", [r"rrsp", r"registered\s+retirement\s+savings"]),
        ("TFSA", [r"tfsa", r"tax.free\s+savings"]),
        ("RESP", [r"resp", r"registered\s+education"]),
        ("RRIF", [r"rrif", r"retirement\s+income\s+fund"]),
        ("LIRA", [r"lira", r"locked.in\s+retirement"]),
        ("RDSP", [r"rdsp", r"registered\s+disability"]),
        ("FHSA", [r"fhsa", r"first\s+home\s+savings"]),
        ("Non-Registered", [r"non.reg", r"margin\s+account", r"cash\s+account"]),
    ]

    for acct_type, regexes in patterns:
        for regex in regexes:
            if re.search(regex, text_lower):
                return acct_type

    return "Unknown"
