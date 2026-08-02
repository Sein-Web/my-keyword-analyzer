import streamlit as st
import json
import os
import re
import urllib.parse
import feedparser
import requests
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# 1. Gemini 라이브러리 2중 예외 호환
# -----------------------------------------------------------------------------
GEMINI_MODE = None
try:
    from google import genai
    from google.genai import types
    GEMINI_MODE = "new"
except ImportError:
    try:
        import google.generativeai as legacy_genai
        GEMINI_MODE = "legacy"
    except ImportError:
        GEMINI_MODE = "missing"

# -----------------------------------------------------------------------------
# 2. 경로 설정 및 API 키 완벽 로더
# -----------------------------------------------------------------------------
BASE_DIR = os.path.expanduser("~/Documents/Marketing")
BLOG_DIR = os.path.join(BASE_DIR, "blog")
INSTA_DIR = os.path.join(BASE_DIR, "instagram")

# 폴더 자동 생성
for d in [BASE_DIR, BLOG_DIR, INSTA_DIR]:
    os.makedirs(d, exist_ok=True)

# 시스템 기본 키 가져오기 함수 (Secrets 또는 파일)
def get_gemini_api_key_details():
    # 1. Streamlit Secrets에 저장된 키가 있다면 최우선 반환
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"], "Streamlit Secrets", "success"
        
    # 2. 시스템 로컬 파일에서 읽기 시도
    key_path = os.path.join(BLOG_DIR, "gemini api key", "api key.txt")
    if os.path.exists(key_path):
        try:
            with open(key_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                key = f.read().strip()
                key = re.sub(r'[\u200b-\u200d\ufeff\xa0]', '', key).strip()
                if key:
                    return key, key_path, "success"
            return "", key_path, "empty_file"
        except Exception as e:
            return "", key_path, f"read_error: {str(e)}"
    return "", key_path, "not_found"

# -----------------------------------------------------------------------------
# 3. 실시간 트렌드 빅데이터 수집기
# -----------------------------------------------------------------------------
def fetch_realtime_data(keyword):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    scraped_texts = []
    
    # 네이버 서치 뷰어 크롤링
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        naver_url = f"https://search.naver.com/search.naver?query={encoded_keyword}"
        res = requests.get(naver_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            titles = soup.select(".api_txt_lines, .total_tit, .news_tit")
            for t in titles[:8]:
                txt = t.get_text().strip()
                if txt:
                    scraped_texts.append(txt)
    except Exception:
        pass

    # 구글 뉴스 RSS 피드 파싱
    try:
        rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:8]:
            scraped_texts.append(entry.title)
    except Exception:
        pass

    return "\n".join(list(set(scraped_texts)))

# -----------------------------------------------------------------------------
# 4. 하이브리드 AI 기획 빌더 (안전한 배포용 API 로직 탑재)
# -----------------------------------------------------------------------------
def generate_marketing_plan(api_key, raw_context, user_keyword, platform_type="blog"):
    if not api_key:
        return {"error": "API 키가 설정되지 않았습니다. 왼쪽 사이드바에 본인의 Gemini API Key를 입력해 주세요."}
    
    if GEMINI_MODE == "missing":
        return {"error": "시스템에 Google Gemini 패키지가 설치되어 있지 않습니다.\n터미널에 'pip install google-genai'를 실행해 주세요."}

    # 사장님이 만족해하셨던 풍성하고 깊이 있는 오리지널 프롬프트 스키마 그대로 사용
    prompt = f"""
    [사용자 핵심 주제어]: {user_keyword}
    [실시간 수집 시장 데이터]:
    {raw_context}

    위 수집된 실시간 데이터를 기반으로 사용자의 타겟 플랫폼({platform_type})에 최적화된 마케팅 기획안을 도출하세요.
    반드시 마크다운 백틱(```json) 없이 완벽한 JSON 형식으로만 반환해 주세요.

    응답 스키마:
    {{
      "target_keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
      "hooking_titles": [
        "대표 타이틀 후보 1",
        "대표 타이틀 후보 2",
        "대표 타이틀 후보 3",
        "대표 타이틀 후보 4",
        "대표 타이틀 후보 5"
      ],
      "outline": {{
        "step1_problem": "불편한 페인 포인트 상황 기술...",
        "step2_empathy": "고객 마음에 깊이 스며드는 공감 서사 기술...",
        "step3_solution": "강력하고 유용한 논리적 정답 제시...",
        "step4_cta": "독자의 참여 및 행동을 이끌 마침표 카피..."
      }},
      "image_prompt": "Minimal modern realistic aesthetic photography capturing..."
    }}
    """

    try:
        if GEMINI_MODE == "new":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.75,
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text
        else:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            raw_text = response.text

        # JSON 정제 후 파싱
        cleaned_response = raw_text.strip()
        if cleaned_response.startswith("```"):
            cleaned_response = re.sub(r"^```(?:json)?", "", cleaned_response, flags=re.IGNORECASE)
            cleaned_response = re.sub(r"```$", "", cleaned_response, flags=re.IGNORECASE)
        
        return json.loads(cleaned_response.strip())

    except Exception as e:
        return {"error": f"AI 분석 프로세스 도중 에러가 발생했습니다.\n\n[상세 오류 로그]: {str(e)}"}

# -----------------------------------------------------------------------------
# 5. 초고급 전문가 사설 앱 전용 CSS 테마 적용
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 실시간 마케팅 기획 플랫폼",
    page_icon="🔑",
    layout="wide"
)

st.markdown("""
<style>
    /* 1. 웹 전역 배경: 부드러운 스노우 그레이 톤으로 감각적으로 채움 */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
        font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }

    /* 2. 기획기 사각 박스 가로폭 고정 및 초고급 카드 섀도우 효과 */
    [data-testid="stMainBlockContainer"] {
        max-width: 860px !important; /* 3번 피드백 영역 사이즈 반영 */
        margin: 50px auto !important;
        padding: 40px 50px !important;
        background-color: #FFFFFF !important;
        border-radius: 20px !important;
        /* 복잡하고 촌스러운 테두리를 제거하고 은은하고 웅장한 소프트 섀도우 처리 */
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.04) !important;
        border: none !important;
    }

    /* 3. 명품 디자이너 톤 서체 세팅 */
    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #1E293B !important; /* 소프트 차콜 */
        font-weight: 600;
    }

    /* 4. 브랜딩 헤더 라인 */
    .brand-header-area {
        text-align: center;
        margin-bottom: 35px;
        padding-bottom: 25px;
        border-bottom: 2px dashed #E2E8F0;
    }
    .brand-main-title {
        font-size: 26px;
        font-weight: 850;
        color: #1E3A8A !important; /* 딥 미드나잇 블루 */
        letter-spacing: -0.7px;
    }
    .brand-sub-title {
        font-size: 13.5px;
        color: #64748B !important;
        font-weight: 400;
        margin-top: 6px;
    }

    /* 5. 탭 메뉴 초현대식 디자인 튜닝 */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #94A3B8 !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 10px 20px !important;
    }
    button[aria-selected="true"] {
        color: #1E3A8A !important;
        border-bottom: 3px solid #1E3A8A !important;
    }

    /* 6. 입력 상자 프리미엄 가공 */
    div[data-baseweb="input"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
    }
    input {
        color: #1E293B !important;
        font-weight: 500 !important;
    }

    /* 7. 명품 오렌지(#FF5A1F) 원색 실행 버튼 */
    div.stButton > button {
        background-color: #FF5A1F !important;
        color: #FFFFFF !important;
        border: none !important;
        padding: 14px 24px !important;
        font-size: 15.5px !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        width: 100% !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 14px rgba(255, 90, 31, 0.2);
    }
    div.stButton > button:hover {
        background-color: #E04810 !important;
        box-shadow: 0 6px 20px rgba(255, 90, 31, 0.35);
        transform: translateY(-1px);
    }

    /* 8. 1번 스타일 복원용 좌측 정렬 결과 영역 뱃지 */
    .expert-sec-title {
        font-size: 17px;
        font-weight: 800;
        color: #1E3A8A !important;
        margin: 35px 0 15px 0;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .expert-sec-sub {
        font-size: 13px;
        color: #64748B !important;
        font-weight: 400;
        margin-top: -10px;
        margin-bottom: 18px;
    }

    /* 줄글 출력용 세련된 명품 폰트 텍스트 스타일 */
    .row-text-line {
        font-size: 14.5px;
        color: #334155;
        font-weight: 500;
        line-height: 1.8;
        padding: 8px 12px;
        background-color: #F8FAFC;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 3px solid #E2E8F0;
        letter-spacing: -0.2px;
    }
    
    .row-keyword-tag {
        display: inline-block;
        background-color: #F1F5F9;
        color: #1E3A8A;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 30px;
        margin-right: 8px;
        margin-bottom: 8px;
        font-size: 13.5px;
    }

    .row-4step-box {
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px dashed #F1F5F9;
    }
    .row-4step-label {
        font-size: 14.5px;
        font-weight: 800;
        color: #FF5A1F;
        margin-bottom: 5px;
    }
    .row-4step-desc {
        font-size: 14px;
        color: #334155;
        font-weight: 400;
        line-height: 1.7;
    }

    /* 기본 부스러기 제거 */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 사이드바 영역: 타인 배포를 위한 수동 API 키 입력 기능 설계 ---
with st.sidebar:
    st.markdown("### 🔑 API 설정")
    st.markdown("본 서비스는 Google Gemini AI를 사용합니다. 외부 공유용으로 배포 시 타인이 본인의 개별 API 키를 직접 넣어 안전하게 사용할 수 있습니다.")
    
    # 비밀 키 입력 마스킹 필드
    user_api_key = st.text_input(
        "Gemini API Key 입력",
        type="password",
        placeholder="AIzaSy...",
        help="Google AI Studio에서 발급받은 API 키를 넣어주세요. 미입력 시 서버의 디폴트 시스템 키가 우선 작동합니다."
    )
    st.markdown("---")
    st.markdown("💡 **Gemini API 키 발급은 어디서 하나요?**\n[Google AI Studio](https://aistudio.google.com/)에서 로그인 후 클릭 한 번으로 무료 발급 가능합니다.")

# API 키 자동 세팅 (1순위: 사용자가 사이드바에 입력한 키 / 2순위: 서버 백그라운드 키)
selected_api_key = ""
if user_api_key.strip():
    selected_api_key = user_api_key.strip()
else:
    system_key, key_path, status_code = get_gemini_api_key_details()
    if status_code == "success":
        selected_api_key = system_key

# -----------------------------------------------------------------------------
# 6. 메인 뷰 구성
# -----------------------------------------------------------------------------

# 헤더 탑 박스
st.markdown("""
<div class="brand-header-area">
    <div class="brand-main-title">🔑 AI 실시간 핵심 키워드 기획기</div>
    <div class="brand-sub-title">실시간 트렌드 빅데이터를 기반으로 노출 최적화 타겟 키워드와 설득 구조 콘텐츠 기획안을 수립합니다.</div>
</div>
""", unsafe_allow_html=True)

# 탭 메뉴 구현
tab_blog, tab_insta = st.tabs(["📝 블로그 분석 대시보드", "📸 인스타그램 분석 대시보드"])

def run_application_layout(platform_name, platform_key, save_filename, dest_dir):
    st.write("")
    st.markdown("**🔍 분석을 희망하는 단어나 주제어를 입력해 주세요:**")
    
    user_keyword = st.text_input(
        "입력 창", 
        placeholder="예시) 바이브코딩, 성인 심리상담, 주말 근교 드라이브", 
        label_visibility="collapsed",
        key=f"keyword_{platform_key}"
    )
    
    st.write("")
    
    if st.button("🚀 실시간 시장 분석 및 고효율 마케팅 기획 시작", key=f"action_{platform_key}"):
        if not user_keyword.strip():
            st.error("⚠️ 기획안을 도출할 주제 키워드를 입력해 주세요.")
            return
            
        if not selected_api_key:
            st.error("🔑 API 키가 검색되지 않았습니다. 화면 좌측 사이드바에 Gemini API Key를 올바르게 넣어 가동해 주세요.")
            return

        with st.status("🔍 네이버/구글 실시간 동향 수집 및 기획안 생성 중...", expanded=True) as status:
            raw_context = fetch_realtime_data(user_keyword)
            result = generate_marketing_plan(selected_api_key, raw_context, user_keyword, platform_type=platform_key)
            
            if "error" in result:
                status.update(label="❌ 기획안 생성 및 추출 오류 발생", state="error")
                st.error(result["error"])
                return
            
            status.update(label="✅ 분석과 정밀 기획 가이드라인 수립 완료!", state="complete")
        
        # 로컬 세이브 파일 출력
        save_path = os.path.join(dest_dir, save_filename)
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.warning(f"로컬 디스크 백업 실패: {e}")

        # ---------------------------------------------------------------------
        # 1번 피드백 반영: 깔끔하고 고급스러운 좌측 정렬 줄글 결과 뷰
        # ---------------------------------------------------------------------
        st.write("")
        st.markdown(f"### 📋 '{user_keyword}' 실시간 콘텐츠 기획 보고서")
        st.write("")

        # Section 1. 타겟 키워드 뱃지 정렬
        st.markdown('<div class="expert-sec-title">🎯 추천 확장 타겟 키워드</div>', unsafe_allow_html=True)
        st.markdown('<div class="expert-sec-sub">핵심 주제어 유도를 극대화할 수 있도록 연동될 주요 세부 검색어 키워드입니다.</div>', unsafe_allow_html=True)
        
        keywords = result.get("target_keywords", [])
        tags_html = "".join([f'<span class="row-keyword-tag">#{kw}</span>' for kw in keywords[:5]])
        st.markdown(f'<div style="margin-bottom: 25px;">{tags_html}</div>', unsafe_allow_html=True)

        # Section 2. 추천 카피 타이틀 줄글 정렬 (1번 레이아웃 복원)
        st.markdown('<div class="expert-sec-title">🔥 썸네일 & 콘텐츠 대표 타이틀 추천 카피</div>', unsafe_allow_html=True)
        st.markdown('<div class="expert-sec-sub">소비자의 흥미와 반응률을 직관적으로 증폭시키는 헤드라인 카피 리스트입니다. (마우스 드래그로 복사 가능)</div>', unsafe_allow_html=True)
        
        titles = result.get("hooking_titles", [])
        for idx, t in enumerate(titles[:5]):
            st.markdown(f'<div class="row-text-line"><strong>{idx+1}순위:</strong> {t}</div>', unsafe_allow_html=True)

        # Section 3. 마케팅 기법 적용 본문 4단계 (깔끔하고 트렌디하게 가공)
        st.markdown('<div class="expert-sec-title">📊 마케팅 공식 4단계 본문 골격 기획안</div>', unsafe_allow_html=True)
        st.markdown('<div class="expert-sec-sub">이탈 방지 및 최종 타겟 전환율 상승을 보장하는 설득 지향적 구조 설계안입니다.</div>', unsafe_allow_html=True)

        outline = result.get("outline", {})
        
        # 1단계
        st.markdown(f"""
        <div class="row-4step-box">
            <div class="row-4step-label">🚨 1단계: 문제 상황 정의 (Problem)</div>
            <div class="row-4step-desc">{outline.get("step1_problem", "")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2단계
        st.markdown(f"""
        <div class="row-4step-box">
            <div class="row-4step-label">🤝 2단계: 유대감 및 공감대 형성 (Empathy)</div>
            <div class="row-4step-desc">{outline.get("step2_empathy", "")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3단계
        st.markdown(f"""
        <div class="row-4step-box">
            <div class="row-4step-label">💡 3단계: 논리적 해결책 처방 (Solution)</div>
            <div class="row-4step-desc">{outline.get("step3_solution", "")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 4단계
        st.markdown(f"""
        <div class="row-4step-box">
            <div class="row-4step-label">⚡ 4단계: 행동 전환 촉구 (CTA)</div>
            <div class="row-4step-desc">{outline.get("step4_cta", "")}</div>
        </div>
        """, unsafe_allow_html=True)

        # Section 4. 이미지 생성 프롬프트
        st.markdown('<div class="expert-sec-title">🎨 AI 썸네일 이미지 제작용 프롬프트 (영문)</div>', unsafe_allow_html=True)
        st.markdown('<div class="expert-sec-sub">미드저니(Midjourney) 또는 DALL-E에 그대로 입력하여 고품질 커버 디자인 이미지를 출력할 수 있습니다.</div>', unsafe_allow_html=True)
        
        img_prompt = result.get("image_prompt", "")
        st.markdown(f'<div class="row-text-line" style="font-family: monospace; background-color: #F1F5F9; border-left: 3px solid #FF5A1F;">{img_prompt}</div>', unsafe_allow_html=True)

        st.success(f"💾 로컬 디렉토리 데이터 파일 저장 완료: `{save_filename}`")

# 각 탭 매핑 활성화
with tab_blog:
    run_application_layout("블로그", "blog", "today_topic.json", BLOG_DIR)

with tab_insta:
    run_application_layout("인스타그램", "instagram", "today_topic_insta.json", INSTA_DIR)
