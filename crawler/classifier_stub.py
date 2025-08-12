from typing import Tuple

# 새 카테고리: 1~10
CODES = {
    "SPECIAL_LECTURE": 1,     # 특강
    "PLANNING_MARKETING": 2,  # 기획/마케팅
    "JOB_INTERNSHIP": 3,      # 취업/인턴십
    "VOLUNTEER": 4,           # 봉사 활동
    "IT_SW": 5,               # IT/SW
    "STUDY": 6,               # 스터디
    "DESIGN": 7,              # 디자인
    "STARTUP": 8,             # 창업
    "VIDEO_CONTENT": 9,       # 영상/콘텐츠
    "SUPPORTERS_PRESS": 10,   # 서포터즈/기자단
}

# 우선순위: 다중 매칭 시 앞에 있는 것 우선
RULES = [
    (CODES["JOB_INTERNSHIP"], [
        "채용", "인턴", "recruit", "intern", "신입", "공채", "수습", "채용공고", "모집(.*)인턴"
    ]),
    (CODES["IT_SW"], [
        "개발", "프로그래", "소프트웨어", "소프트웨어", "it", "ai", "데이터", "딥러닝",
        "머신러닝", "백엔드", "프론트엔드", "서버", "코딩", "컴퓨터", "알고리즘", "해커톤"
    ]),
    (CODES["SPECIAL_LECTURE"], [
        "특강", "초청강연", "세미나", "콜로퀴엄", "워크숍", "컨퍼런스", "강연회", "강좌", "세미너"
    ]),
    (CODES["PLANNING_MARKETING"], [
        "마케팅", "브랜딩", "프로모션", "기획", "캠페인", "시장조사", "ux 리서치", "홍보대사\(마케팅\)"
    ]),
    (CODES["VOLUNTEER"], [
        "봉사", "volunteer", "자원봉사", "사회봉사", "교육봉사"
    ]),
    (CODES["STUDY"], [
        "스터디", "study", "학습모임", "공부모임", "공부 스터디", "학습 스터디"
    ]),
    (CODES["DESIGN"], [
        "디자인", "ui", "ux", "그래픽", "일러스트", "포스터", "브랜딩 디자인", "시각디자인"
    ]),
    (CODES["STARTUP"], [
        "창업", "startup", "예비창업", "창업동아리", "액셀러레이터", "창업경진"
    ]),
    (CODES["VIDEO_CONTENT"], [
        "영상", "유튜브", "크리에이터", "콘텐츠", "편집", "촬영", "pd", "mcN", "숏폼", "릴스", "틱톡"
    ]),
    (CODES["SUPPORTERS_PRESS"], [
        "서포터즈", "기자단", "홍보대사", "프레스", "에디터", "앰배서더", "홍보 서포터즈"
    ]),
]

def _contains_any(text: str, keywords) -> bool:
    return any(k.lower() in text for k in keywords)

def classify(title: str, content: str) -> Tuple[int, float, str]:
    """
    간단 규칙 기반 스텁:
    - 제목 > 본문 순으로 매칭
    - 다중 매칭 시 RULES 순서 우선
    """
    t = (title or "").lower()
    c = (content or "").lower()

    # 제목 우선 탐지
    for cat, keys in RULES:
        if _contains_any(t, keys):
            return (cat, 0.88, "stub-0.2")

    # 본문 보조 탐지
    for cat, keys in RULES:
        if _contains_any(c, keys):
            return (cat, 0.72, "stub-0.2")

    # 기본값: 서포터즈/기자단으로 몰릴 위험이 있어 마지막은 낮은 확신치로 IT/SW 대신 범용 처리 X
    # 여기서는 '특강'을 기본 폴백으로 둔다. (원하면 0번 '기타'를 만들어 사용)
    return (CODES["SPECIAL_LECTURE"], 0.51, "stub-0.2")