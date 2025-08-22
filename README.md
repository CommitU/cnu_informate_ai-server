# CNU InfoMate

충남대 학사/모집 공지를 크롤링 → 분류(AI) → DB 저장하는 파이프라인입니다.
실행 시, CNU 사이트의 공지를 자동으로 수집하고 카테고리별로 분류하여 DB에 저장합니다.

---

## 📦 프로젝트 구조
```plaintext
cnu_informate/
├── crawler/                  # 크롤링 & 파이프라인 모듈
│   ├── __init__.py
│   ├── db.py                  # DB 연결 / UPSERT 유틸
│   ├── pipeline.log           # 실행 로그
│   ├── pipeline.py            # 엔트리 포인트; 다중 소스 순회 → 목록 → 상세 → 분류 → DB 저장
│   ├── requirements.txt       # 크롤러 의존성
│   └── text_classifier.py     # 계층적 분류기 (키워드 / ML / OpenAI 백업)
├── mysql-data/                # MySQL 데이터 (볼륨 마운트)
├── mysql-init/                # MySQL 초기화 SQL
├── venv/                      # 가상환경 (git 제외)
├── .env                       # 환경 변수 (DB 접속정보 등, git 제외)
├── .gitignore
├── CLAUDE.md                  # AI 코드 리뷰/노트
├── docker-compose.yml         # MySQL 컨테이너 구성
└── README.md
```
---

## 🚀 실행 방법

    pip install -r crawler/requirements.txt
    python crawler/pipeline.py

--- 

## 📝 진행 방식(Overview)
    1. 크롤링 모듈
	    • BeautifulSoup 기반으로 plus.cnu.ac.kr 게시판/리크루트 공지 크롤링
	    • URL / 제목 / 본문 / 게시일 / 해시값 수집
	2. DB 저장
	    • MySQL 사용
	    • notice 테이블에 공지 저장
	    • 중복 방지를 위해 Upsert(ON DUPLICATE KEY UPDATE) 구조 설계
	3. 분류 시스템
	    • 키워드 매칭: 도메인 사전으로 1차 분류
	    • ML 모델(TF-IDF + LogisticRegression): 학습된 모델 있으면 2차 보정
	    • OpenAI API 백업: 신뢰도 낮을 때만 호출하여 품질 보완

--- 

## 🔍 분류 방식
	1. 키워드 기반 분류 (기본)
	2. OpenAI API 백업 (선택, 임계값 미달 시 호출)

---

## ✅ 실행 결과 예시
    [OK] src=1 p=1 notice=12 cat=11 conf=0.82 ver=keyword-local AI 특강 안내...
    [OK] src=2 p=1 notice=13 cat=3  conf=0.91 ver=openai-backup 채용 공고...