# CNU InfoMate

충남대 공지(학사/장학/취업 등)를 크롤링 → 분류 → MySQL에 저장하는 파이프라인.  
향후 Spring Boot API + 알림(WS/웹푸시)로 확장 예정.

---

## 📦 프로젝트 구조
```plaintext
cnu_informate/
├── crawler/                  # 크롤링 & 파이프라인
│   ├── __init__.py
│   ├── db.py                  # DB 연결 / UPSERT 유틸
│   ├── classifier_stub.py     # 임시 분류기 (추후 KoELECTRA 교체 예정)
│   ├── cnu_main_crawler.py    # CNU 메인 공지 크롤러 (재시도 / 백오프 포함)
│   ├── cnu_cse_crawler.py     # CNU 컴퓨터융합학부 공지 크롤러
│   └── pipeline.py            # 엔트리 포인트; 목록 → 상세 → 분류 → DB 저장
├── mysql-init/                # MySQL 초기화 SQL
│   └── 00_init.sql            # 스키마 & 시드 데이터 정의
├── mysql-data/                # (볼륨 마운트) 실제 MySQL 데이터
├── venv/                      # (가상환경) - git 제외
├── .env                       # (민감값) DB 접속정보 - git 제외
├── .gitignore
├── requirements.txt           # crawler 의존성
├── docker-compose.yml         # MySQL 컨테이너 구성
└── README.md


