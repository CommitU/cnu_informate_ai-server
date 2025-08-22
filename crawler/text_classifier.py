import os
import pickle
import numpy as np
import requests
import json
import re
from typing import Tuple, Optional, Dict, List
import warnings
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

load_dotenv()

# 12개 카테고리 분류 코드
CATEGORY_CODES = {
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
    "ACADEMIC_INFO": 11,      # 학사 안내
    "ETC": 12,                # 기타
}

CATEGORY_NAMES = [
    "특강", "기획/마케팅", "취업/인턴십", "봉사 활동", "IT/SW",
    "스터디", "디자인", "창업", "영상/콘텐츠", "서포터즈/기자단",
    "학사 안내", "기타"
]

class TextClassifier:
    def __init__(self, model_path: str = None, confidence_threshold: float = 0.7, api_config: Dict = None):
        """
        텍스트 분류 모델 초기화
        
        Args:
            model_path: 학습된 모델이 저장된 경로
            confidence_threshold: API 백업을 사용할 신뢰도 임계값
            api_config: API 설정 (url, headers 등)
        """
        self.model = None
        self.vectorizer = None
        self.model_version = "ml-1.0"
        self.confidence_threshold = confidence_threshold
        self.api_config = api_config or {}
        
        # 강화된 키워드 분류 시스템
        self.keyword_categories = self._build_keyword_categories()
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def _build_keyword_categories(self) -> Dict[int, List[str]]:
        """강화된 키워드 카테고리 구축"""
        return {
            CATEGORY_CODES["SPECIAL_LECTURE"]: [
                "특강", "세미나", "강연", "강의", "lecture", "seminar", "워크샵", "workshop",
                "교육", "설명회", "오리엔테이션", "briefing", "설명회", "안내회"
            ],
            CATEGORY_CODES["PLANNING_MARKETING"]: [
                "기획", "마케팅", "브랜딩", "홍보", "marketing", "planning", "브랜드",
                "광고", "캠페인", "프로모션", "promotion", "홍보대사", "기획안", "마케터"
            ],
            CATEGORY_CODES["JOB_INTERNSHIP"]: [
                "채용", "인턴", "recruit", "신입", "취업", "job", "career", "면접",
                "입사", "구인", "구직", "employment", "사원", "직원", "인력", "직무",
                "채용공고", "모집공고", "지원", "서류", "면접", "취직"
            ],
            CATEGORY_CODES["VOLUNTEER"]: [
                "봉사", "volunteer", "자원봉사", "사회공헌", "기부", "volunteer",
                "봉사활동", "사회봉사", "나눔", "헌혈", "환경", "지역사회", "복지"
            ],
            CATEGORY_CODES["IT_SW"]: [
                "개발", "프로그래", "ai", "데이터", "코딩", "software", "it", "개발자",
                "프로그래밍", "앱", "app", "웹", "web", "시스템", "database", "알고리즘",
                "머신러닝", "딥러닝", "빅데이터", "클라우드", "서버", "네트워크", "보안"
            ],
            CATEGORY_CODES["STUDY"]: [
                "스터디", "study", "공부", "학습", "튜터링", "멘토링", "교육",
                "학습모임", "독서", "시험", "자격증", "토익", "토플", "어학", "언어"
            ],
            CATEGORY_CODES["DESIGN"]: [
                "디자인", "ui", "ux", "design", "그래픽", "웹디자인", "디자이너",
                "포토샵", "일러스트", "영상편집", "3d", "타이포그래피", "브랜딩디자인"
            ],
            CATEGORY_CODES["STARTUP"]: [
                "창업", "startup", "사업", "벤처", "기업가정신", "사업계획",
                "투자", "펀딩", "비즈니스", "스타트업", "창업가", "entrepreneur"
            ],
            CATEGORY_CODES["VIDEO_CONTENT"]: [
                "영상", "콘텐츠", "video", "content", "유튜브", "영화", "촬영",
                "편집", "미디어", "방송", "라이브", "스트리밍", "크리에이터"
            ],
            CATEGORY_CODES["SUPPORTERS_PRESS"]: [
                "서포터즈", "기자단", "supporters", "press", "홍보대사", "리포터",
                "앰버서더", "블로거", "인플루언서", "홍보단", "서포터", "대학생기자"
            ],
            CATEGORY_CODES["ACADEMIC_INFO"]: [
                "학사", "수강", "성적", "졸업", "학점", "등록", "장학", "academic",
                "학적", "수업", "강의", "학기", "등록금", "장학금", "성적표", "졸업요건"
            ]
        }

    def load_model(self, model_path: str):
        """저장된 모델과 벡터라이저 로드"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.vectorizer = model_data['vectorizer']
                self.model_version = model_data.get('version', 'ml-1.0')
            print(f"모델 로드 완료: {model_path}")
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            self.model = None
            self.vectorizer = None
    
    def save_model(self, model_path: str):
        """모델과 벡터라이저 저장"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("저장할 모델이 없습니다.")
        
        model_data = {
            'model': self.model,
            'vectorizer': self.vectorizer,
            'version': self.model_version
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"모델 저장 완료: {model_path}")
    
    def preprocess_text(self, title: str, content: str) -> str:
        """텍스트 전처리"""
        # 제목에 가중치를 부여하여 결합
        title = (title or "").strip()
        content = (content or "").strip()
        
        # 제목을 3번 반복하여 가중치 부여
        combined_text = f"{title} {title} {title} {content}"
        return combined_text
    
    def predict_with_ml(self, text: str) -> Tuple[int, float]:
        """머신러닝 모델을 사용한 예측"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("모델이 로드되지 않았습니다.")
        
        # 텍스트 벡터화
        text_vector = self.vectorizer.transform([text])
        
        # 예측 및 확률 계산
        prediction = self.model.predict(text_vector)[0]
        probabilities = self.model.predict_proba(text_vector)[0]
        confidence = float(np.max(probabilities))
        
        return int(prediction), confidence
    
    def predict_with_keywords(self, title: str, content: str) -> Tuple[int, float]:
        """강화된 키워드 기반 예측"""
        title_text = (title or "").lower()
        content_text = (content or "").lower()
        
        # 점수 계산 시스템
        category_scores = {}
        
        for category_id, keywords in self.keyword_categories.items():
            score = 0
            title_matches = 0
            content_matches = 0
            
            for keyword in keywords:
                keyword = keyword.lower()
                # 제목에서 키워드 매치 (가중치 3배)
                if keyword in title_text:
                    title_matches += 1
                    score += 3
                
                # 본문에서 키워드 매치 (가중치 1배)
                if keyword in content_text:
                    content_matches += 1
                    score += 1
            
            if score > 0:
                category_scores[category_id] = score
        
        if not category_scores:
            return CATEGORY_CODES["ETC"], 0.1
        
        # 최고 점수 카테고리 선택
        best_category = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_category]
        
        # 신뢰도 계산 (점수를 0~1 범위로 정규화)
        confidence = min(best_score / 10.0, 0.95)
        
        return best_category, confidence
    
    def predict_with_openai(self, title: str, content: str) -> Tuple[int, float]:
        """OpenAI API를 사용한 백업 분류"""
        if not self.api_config.get('api_key'):
            raise ValueError("OpenAI API key가 설정되지 않았습니다.")
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_config['api_key'])
            
            # 카테고리 정보 문자열 생성
            category_info = []
            for name, code in CATEGORY_CODES.items():
                korean_name = CATEGORY_NAMES[code - 1]
                category_info.append(f"{code}: {korean_name} ({name})")
            
            categories_text = "\n".join(category_info)
            
            prompt = f"""다음 텍스트를 분석하여 가장 적절한 카테고리로 분류해주세요.

제목: {title or ''}
내용: {content or ''}

사용 가능한 카테고리:
{categories_text}

응답 형식:
- 카테고리 번호만 숫자로 반환 (1-12)
- 추가 설명 없이 숫자만

카테고리 번호:"""

            response = client.chat.completions.create(
                model=self.api_config.get('model', 'gpt-4o-mini'),
                messages=[
                    {"role": "system", "content": "당신은 텍스트 분류 전문가입니다. 주어진 텍스트를 정확히 분류하고 카테고리 번호만 반환하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 숫자 추출
            category_id = None
            for char in result_text:
                if char.isdigit():
                    num = int(char)
                    if 1 <= num <= 12:
                        category_id = num
                        break
            
            if category_id is None:
                # 두 자리 숫자도 체크
                import re
                match = re.search(r'\b(1[0-2]|[1-9])\b', result_text)
                if match:
                    category_id = int(match.group(1))
            
            if category_id is None or not (1 <= category_id <= 12):
                print(f"OpenAI 분류 결과 파싱 실패: {result_text}")
                return CATEGORY_CODES["ETC"], 0.3
            
            # OpenAI 응답은 보통 높은 신뢰도로 가정
            confidence = 0.85
            
            return category_id, confidence
            
        except Exception as e:
            print(f"OpenAI API 분류 오류: {e}")
            return CATEGORY_CODES["ETC"], 0.2
    
    def classify(self, title: str, content: str) -> Tuple[int, float, str]:
        """
        텍스트 분류 메인 함수 - 계층적 분류 시스템
        
        1. 로컬 키워드 분류 시도
        2. 신뢰도가 임계값 이하면 ML 모델 시도
        3. 여전히 신뢰도가 낮으면 API 백업 사용
        
        Args:
            title: 제목
            content: 본문
            
        Returns:
            (category_id, confidence, version)
        """
        try:
            # 1단계: 로컬 키워드 분류
            category_id, confidence = self.predict_with_keywords(title, content)
            
            if confidence >= self.confidence_threshold:
                return category_id, confidence, "keyword-local"
            
            # 2단계: ML 모델 분류 (있는 경우)
            if self.model is not None and self.vectorizer is not None:
                text = self.preprocess_text(title, content)
                ml_category_id, ml_confidence = self.predict_with_ml(text)
                
                if ml_confidence >= self.confidence_threshold:
                    return ml_category_id, ml_confidence, self.model_version
                
                # 키워드와 ML 결과가 일치하면 신뢰도 증가
                if ml_category_id == category_id:
                    combined_confidence = min((confidence + ml_confidence) / 2 + 0.1, 0.95)
                    return category_id, combined_confidence, f"{self.model_version}+keyword"
            
            # 3단계: OpenAI API 백업 분류 (설정된 경우)
            if self.api_config.get('api_key') and confidence < self.confidence_threshold:
                try:
                    api_category_id, api_confidence = self.predict_with_openai(title, content)
                    if api_confidence >= self.confidence_threshold:
                        return api_category_id, api_confidence, "openai-backup"
                except Exception as e:
                    print(f"OpenAI API 백업 실패: {e}")
            
            # 최종: 키워드 결과 또는 기본값 반환
            if confidence > 0.1:
                return category_id, confidence, "keyword-final"
            else:
                return CATEGORY_CODES["ETC"], 0.1, "default-fallback"
        
        except Exception as e:
            print(f"분류 오류: {e}")
            return CATEGORY_CODES["ETC"], 0.1, "error-fallback"

# 전역 분류기 인스턴스
_classifier = None

def get_classifier(confidence_threshold: float = 0.7, api_config: Dict = None) -> TextClassifier:
    """전역 분류기 인스턴스 반환"""
    global _classifier
    if _classifier is None:
        # API 설정이 없으면 환경변수에서 로드
        if api_config is None:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                api_config = {
                    'api_key': openai_key,
                    'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
                }
        
        # 모델 파일 경로 확인
        model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
        _classifier = TextClassifier(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            api_config=api_config
        )
    return _classifier

def configure_classifier(confidence_threshold: float = 0.7, api_config: Dict = None):
    """분류기 설정 업데이트"""
    global _classifier
    _classifier = None  # 기존 인스턴스 초기화
    return get_classifier(confidence_threshold, api_config)

def classify(title: str, content: str) -> Tuple[int, float, str]:
    """
    기존 classifier_stub.py와 호환되는 인터페이스
    
    Args:
        title: 제목
        content: 본문
        
    Returns:
        (category_id, confidence, version)
    """
    classifier = get_classifier()
    return classifier.classify(title, content)

# Colab에서 모델을 학습하고 저장하는 예제 함수
def train_and_save_model_example():
    """
    Colab에서 이 함수를 참고하여 모델을 학습하고 저장하세요.
    실제 구현시에는 Colab의 모델 코드로 대체하세요.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    
    # 예시 데이터 (실제로는 크롤링된 데이터 사용)
    texts = [
        "소프트웨어 개발자 채용 공고",
        "AI 머신러닝 특강 안내",
        "창업 경진대회 모집",
        "UX 디자인 워크숍"
    ]
    labels = [3, 1, 8, 7]  # 카테고리 ID
    
    # 벡터라이저와 모델 생성
    vectorizer = TfidfVectorizer(max_features=5000, stop_words=None)
    model = LogisticRegression(random_state=42)
    
    # 학습
    X = vectorizer.fit_transform(texts)
    model.fit(X, labels)
    
    # 모델 저장
    model_data = {
        'model': model,
        'vectorizer': vectorizer,
        'version': 'ml-1.0'
    }
    
    model_path = 'model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"모델이 {model_path}에 저장되었습니다.")
    return model_path

if __name__ == "__main__":
    # 테스트
    test_classifier = TextClassifier()
    result = test_classifier.classify("AI 개발자 채용", "인공지능 백엔드 개발자를 모집합니다")
    print(f"분류 결과: 카테고리={result[0]}, 신뢰도={result[1]:.2f}, 버전={result[2]}")