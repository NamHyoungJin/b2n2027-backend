"""허용 doc_type — homepageDocPlan.md §2"""

HOMEPAGE_DOC_TYPES_ORDERED = (
    "terms_sensitive",
    "privacy_policy",
    "refund_policy",
    "travel_insurance",
)

HOMEPAGE_DOC_TYPES = frozenset(HOMEPAGE_DOC_TYPES_ORDERED)

HOMEPAGE_DOC_LABELS: dict[str, str] = {
    "terms_sensitive": "이용약관(민감정보)",
    "privacy_policy": "개인정보취급방침",
    "refund_policy": "환불정책",
    "travel_insurance": "여행자보험",
}
