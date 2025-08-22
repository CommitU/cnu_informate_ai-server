# CNU Infomate AI 서버 프로젝트 기능 정리

## 📋 프로젝트 개요

**CNU Infomate**는 충남대학교 학사/모집 공지를 자동으로 크롤링하고, AI를 통해 카테고리별로 분류하여 데이터베이스에 저장하는 파이프라인 시스템입니다.

### 🎯 주요 목적

- 충남대학교 공지사항 자동 수집
- AI 기반 텍스트 분류 시스템
- 체계적인 데이터베이스 관리
- 사용자 맞춤형 정보 제공 기반 구축

---

## 🏗️ 시스템 아키텍처

### 전체 구조

```
CNU Infomate AI Server
├── 크롤링 모듈 (crawler/)
├── AI 분류 시스템 (text_classifier.py)
├── 데이터베이스 관리 (db.py)
├── MySQL 데이터베이스
└── Docker 컨테이너 환경
```

### 데이터 플로우

```
웹 크롤링 → 텍스트 전처리 → AI 분류 → DB 저장 → 결과 로깅
```

---

## 🔧 핵심 기능

### 1. 웹 크롤링 시스템

#### 지원 소스

- **메인 게시판**: `plus.cnu.ac.kr/_prog/_board/`
  - 0704: 일반 공지
  - 0709: 학사 공지
  - 0705: 모집 공지
  - 070808: 기타 공지
- **리크루트 게시판**: `plus.cnu.ac.kr/_prog/recruit/`
  - 07080401: 채용/인턴십 공고

#### 크롤링 데이터

- **URL**: 공지 원본 링크
- **제목**: 공지 제목
- **본문**: 공지 내용 (HTML 태그 제거, 줄바꿈 보존)
- **게시일**: YYYY-MM-DD 형식
- **해시값**: 중복 방지를 위한 SHA256 해시

#### 크롤링 특징

- **BeautifulSoup4** 기반 HTML 파싱
- **재시도 로직**: 5xx 에러 시 자동 재시도
- **딜레이 시스템**: 서버 부하 방지를 위한 랜덤 딜레이 (0.8~1.8초)
- **User-Agent**: CNU-InfoMate/0.2로 식별

### 2. AI 텍스트 분류 시스템

#### 계층적 분류 구조

```
1단계: 키워드 기반 분류 (로컬)
2단계: ML 모델 분류 (TF-IDF + LogisticRegression)
3단계: OpenAI API 백업 분류
```

#### 지원 카테고리 (12개)

| ID  | 카테고리명      | 영문 코드          | 주요 키워드                  |
| --- | --------------- | ------------------ | ---------------------------- |
| 1   | 특강            | SPECIAL_LECTURE    | 특강, 세미나, 강연, 워크샵   |
| 2   | 기획/마케팅     | PLANNING_MARKETING | 기획, 마케팅, 브랜딩, 홍보   |
| 3   | 취업/인턴십     | JOB_INTERNSHIP     | 채용, 인턴, 취업, 면접       |
| 4   | 봉사 활동       | VOLUNTEER          | 봉사, 자원봉사, 사회공헌     |
| 5   | IT/SW           | IT_SW              | 개발, 프로그래밍, AI, 데이터 |
| 6   | 스터디          | STUDY              | 스터디, 학습, 튜터링, 멘토링 |
| 7   | 디자인          | DESIGN             | 디자인, UI/UX, 그래픽        |
| 8   | 창업            | STARTUP            | 창업, 벤처, 사업계획         |
| 9   | 영상/콘텐츠     | VIDEO_CONTENT      | 영상, 콘텐츠, 유튜브, 편집   |
| 10  | 서포터즈/기자단 | SUPPORTERS_PRESS   | 서포터즈, 기자단, 홍보대사   |
| 11  | 학사 안내       | ACADEMIC_INFO      | 학사, 수강, 성적, 졸업       |
| 12  | 기타            | ETC                | 기타 분류                    |

#### 분류 알고리즘

##### 키워드 기반 분류

- **제목 가중치**: 제목에서 키워드 매치 시 3배 점수
- **본문 가중치**: 본문에서 키워드 매치 시 1배 점수
- **신뢰도 계산**: 점수를 0~1 범위로 정규화

##### ML 모델 분류

- **벡터화**: TF-IDF (최대 5000개 특성)
- **분류기**: LogisticRegression
- **전처리**: 제목 3번 반복으로 가중치 부여

##### OpenAI API 백업

- **모델**: GPT-4o-mini (기본값)
- **프롬프트**: 구조화된 카테고리 정보 제공
- **신뢰도**: 0.85 (기본값)

#### 분류 버전 관리

- `keyword-local`: 키워드 기반 분류
- `ml-1.0`: 머신러닝 모델 분류
- `openai-backup`: OpenAI API 백업 분류
- `keyword-final`: 최종 키워드 분류
- `default-fallback`: 기본값 (기타)

### 3. 데이터베이스 관리 시스템

#### MySQL 스키마

##### 핵심 테이블

- **notice**: 공지사항 메인 정보
- **category**: 카테고리 정보
- **source**: 크롤링 소스 정보
- **notice_category**: 공지-카테고리 매핑
- **attachment**: 첨부파일 정보

##### 사용자 관련 테이블

- **app_user**: 사용자 정보
- **user_interest_category**: 사용자 관심 카테고리
- **user_keyword**: 사용자 키워드 설정
- **notification**: 알림 정보

##### 시스템 테이블

- **crawl_job**: 크롤링 작업 로그

#### 데이터 무결성

- **중복 방지**: URL 기반 UNIQUE 제약
- **해시 검증**: SHA256 해시로 내용 변경 감지
- **외래키 제약**: 참조 무결성 보장
- **UPSERT**: INSERT ... ON DUPLICATE KEY UPDATE

### 4. 파이프라인 실행 시스템

#### 실행 파라미터

- **pages**: 크롤링할 페이지 수 (기본값: 5)
- **confidence_threshold**: 분류 신뢰도 임계값 (기본값: 0.7)
- **api_config**: OpenAI API 설정

#### 실행 로직

1. **소스 순회**: 정의된 모든 크롤링 소스 처리
2. **페이지 순회**: 각 소스별로 지정된 페이지 수만큼 처리
3. **공지 순회**: 각 페이지의 모든 공지사항 처리
4. **상세 정보 수집**: 공지 상세 페이지 크롤링
5. **AI 분류**: 제목과 본문을 AI로 분류
6. **DB 저장**: 분류 결과와 함께 데이터베이스 저장

#### 로깅 시스템

- **진행 상황**: 소스별, 페이지별 진행 상황 표시
- **성공 로그**: `[OK] src=1 p=1 notice=12 cat=11 conf=0.82 ver=keyword-local`
- **에러 로그**: 크롤링 실패, 분류 실패 등 상세 에러 정보
- **통계 정보**: 페이지별 처리된 공지 수량

---

## 🛠️ 기술 스택

### 백엔드

- **Python 3.x**: 메인 개발 언어
- **BeautifulSoup4**: HTML 파싱
- **Requests**: HTTP 클라이언트
- **PyMySQL**: MySQL 데이터베이스 연결
- **scikit-learn**: 머신러닝 모델
- **NumPy**: 수치 계산
- **OpenAI API**: GPT 모델 활용

### 데이터베이스

- **MySQL 8.0**: 메인 데이터베이스
- **UTF8MB4**: 이모지 지원 문자셋
- **Docker**: 컨테이너화된 데이터베이스

### 개발 환경

- **Docker Compose**: 개발 환경 구성
- **python-dotenv**: 환경변수 관리
- **Git**: 버전 관리

---

## 📊 데이터 모델

### 공지사항 (notice)

```sql
CREATE TABLE notice (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  source_id    BIGINT NOT NULL,
  url          VARCHAR(600) NOT NULL UNIQUE,
  title        VARCHAR(500) NOT NULL,
  content      MEDIUMTEXT NULL,
  posted_at    DATETIME NULL,
  scraped_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  hash         CHAR(64) NULL
);
```

### 카테고리 분류 (notice_category)

```sql
CREATE TABLE notice_category (
  notice_id     BIGINT NOT NULL,
  category_id   BIGINT NOT NULL,
  confidence    DECIMAL(5,4) NULL,
  model_version VARCHAR(50) NULL,
  PRIMARY KEY (notice_id, category_id)
);
```

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r crawler/requirements.txt

# 환경변수 설정 (.env 파일)
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=cnu_app
DB_PASSWORD=비밀번호
DB_NAME=cnu_info
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

### 2. 데이터베이스 실행

```bash
# Docker Compose로 MySQL 실행
docker-compose up -d mysql
```

### 3. 크롤링 실행

```bash
# 기본 실행 (5페이지, 신뢰도 0.7)
python crawler/pipeline.py

# 커스텀 파라미터로 실행
python -c "
from crawler.pipeline import run
run(pages=3, confidence_threshold=0.6)
"
```

---

## 📈 성능 및 확장성

### 성능 최적화

- **병렬 처리**: 소스별 독립적 처리
- **메모리 효율성**: 제너레이터 패턴으로 대용량 데이터 처리
- **네트워크 최적화**: 재시도 로직과 딜레이 시스템

### 확장 가능성

- **새로운 소스 추가**: SOURCES 리스트에 소스 정보 추가
- **새로운 카테고리**: CATEGORY_CODES에 카테고리 추가
- **새로운 분류 모델**: TextClassifier 클래스 확장
- **API 백업 시스템**: 다양한 AI 서비스 연동 가능

### 모니터링

- **실행 로그**: 상세한 진행 상황과 에러 정보
- **성능 메트릭**: 처리 시간, 성공률, 분류 정확도
- **데이터 품질**: 중복률, 누락률, 분류 신뢰도

---

## 🔒 보안 및 안정성

### 보안 기능

- **환경변수**: 민감한 정보 환경변수로 관리
- **SQL 인젝션 방지**: 파라미터화된 쿼리 사용
- **네트워크 보안**: HTTPS 요청, 적절한 User-Agent

### 안정성 기능

- **에러 처리**: 예외 상황에 대한 적절한 처리
- **재시도 로직**: 네트워크 오류 시 자동 재시도
- **데이터 무결성**: 해시 검증, 외래키 제약
- **백업 시스템**: OpenAI API 백업으로 분류 안정성 확보

---

## 📝 개발 가이드

### 새로운 크롤링 소스 추가

1. `SOURCES` 리스트에 소스 정보 추가
2. 필요한 경우 새로운 Adapter 클래스 구현
3. 데이터베이스에 source 테이블에 정보 추가

### 새로운 카테고리 추가

1. `CATEGORY_CODES`에 카테고리 코드 추가
2. `CATEGORY_NAMES`에 카테고리명 추가
3. `_build_keyword_categories()`에 키워드 추가
4. 데이터베이스에 category 테이블에 정보 추가

### ML 모델 업데이트

1. 새로운 학습 데이터로 모델 재학습
2. `model.pkl` 파일 업데이트
3. `model_version` 업데이트

---

## 🎯 향후 개발 계획

### 단기 계획

- [ ] 실시간 알림 시스템 구현
- [ ] 웹 대시보드 개발
- [ ] 사용자 맞춤형 추천 시스템
- [ ] 모바일 앱 연동

### 장기 계획

- [ ] 다중 대학 지원 확장
- [ ] 고급 AI 모델 도입 (BERT, GPT 등)
- [ ] 실시간 크롤링 시스템
- [ ] 빅데이터 분석 및 인사이트 제공

---

## 📞 문의 및 지원

이 프로젝트는 충남대학교 학생들을 위한 정보 수집 및 분류 시스템입니다.
기술적 문의나 개선 제안은 프로젝트 저장소를 통해 연락해 주세요.

---

_마지막 업데이트: 2024년_
