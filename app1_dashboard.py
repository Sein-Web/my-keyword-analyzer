import streamlit as st
import os
import json
from datetime import datetime
import feedparser
import requests
from bs4 import BeautifulSoup

# 페이지 기본 설정
st.set_page_config(
    page_title="실시간 트렌드 마케팅 기획기",
    page_icon="📈",
    layout="centered"
)

# 고급스러운 Custom CSS 스타일 적용 (860px 너비 제한 및 미색 배경 디자인)
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
<style>
    /* 전체 배경을 부드러운 초연한 미색/그레이로 지정 */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 탑 네비게이션 및 여백 제거 */
    [data-testid="stHeader"] {
        background: transparent;
    }
    
    /* 중앙 컨테이너 박스 스타일링 (외주 제작 고급 레이아웃) */
    .block-container {
        max-width: 860px !important;
        padding: 40px 20px !important;
    }
    
    /* 메인 카드 박스 */
    .main-card {
        background: #FFFFFF;
        padding: 35px 45px;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(15, 23, 42, 0.04);
        margin-bottom: 25px;
    }
    
    /* 타이틀 및 폰트 설정 */
    .main-title {
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
        text-align: left;
    }
    
    .sub-title {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 30px;
        text-align: left;
        line-height: 1.5;
    }
    
    /* 입력창 및 레이블 스타일 */
    .input-label {
        font-size: 14px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 8px;
    }
    
    /* 하단 구분선 */
    .divider {
        border-bottom: 1.5px solid #F1F5F9;
        margin: 25px 0;
    }
    
    /* 성공 카드 스타일 */
    .success-card {
        background-color: #F8FAFC;
        border-left: 4px solid #1E40AF;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_data_allowed=True)

# --- 사이드바: API 키 및 설정 영역 ---
with st.sidebar:
    st.markdown("### 🔑 API 설정")
    st.markdown("본 서비스는 Google Gemini AI를 사용합니다. 타인에게 공유 시 본인의 API 키를 입력하여 개별 비용으로 안전하게 사용할 수 있습니다.")
    
    # 사용자가 직접 입력하는 API 키 창 (비밀번호 형식)
    user_api_key = st.text_input(
        "Gemini API Key 입력",
        type="password",
        placeholder="AIzaSy...",
        help="Google AI Studio에서 발급받은 API 키를 입력하세요. 입력하지 않으면 서버 기본 설정값(있는 경우)으로 작동합니다."
    )
    
    st.markdown("---")
    st.markdown("💡 **API 키 발급 방법:** [Google AI Studio](https://aistudio.google.com/)에서 무료로 빠르게 발급받으실 수 있습니다.")

# --- API 키 결정 로직 ---
# 사용자가 화면에 입력한 키가 있으면 그것을 최우선으로 쓰고, 없으면 시스템 Secrets에서 가져옵니다.
api_key_to_use = ""
if user_api_key.strip():
    api_key_to_use = user_api_key.strip()
elif "GEMINI_API_KEY" in st.secrets:
    api_key_to_use = st.secrets["GEMINI_API_KEY"]

# 데이터 수집 함수 정의
def fetch_naver_search(keyword):
    try:
        url = f"https://search.naver.com/search.naver?query={keyword}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [el.get_text() for el in soup.select(".news_tit")[:5]]
        return titles if titles else ["실시간 정보를 수집하지 못했습니다."]
    except Exception:
        return ["네이버 정보 일시적 수집 불가"]

def fetch_google_news(keyword):
    try:
        url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        return [entry.title for entry in feed.entries[:5]] if feed.entries else ["실시간 뉴스가 없습니다."]
    except Exception:
        return ["구글 뉴스 일시적 수집 불가"]

# Gemini API 호출 함수 (google-genai 및 레거시 패키지 호환 하이브리드 지원)
def generate_marketing_plan(api_key, keyword, naver_data, google_data):
    # API 엔드포인트를 통한 범용 REST 호출 방식으로 라이브러리 충돌을 완전 차단
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    당신은 15년 경력의 대한민국 최정상급 수석 브랜드 마케터이자 카피라이터입니다.
    제시된 핵심 키워드와 포털 실시간 트렌드 데이터를 기반으로, 타겟 독자의 지갑을 열게 만드는 완벽한 '마케팅 기획서'를 작성해 주세요.
    
    [핵심 키워드]: {keyword}
    [실시간 트네드 참고자료]:
    - 네이버 실시간 뉴스: {", ".join(naver_data)}
    - 구글 뉴스 트렌드: {", ".join(google_data)}
    
    반드시 다음 JSON 형식에 정확히 맞춰서 응답해 주세요. JSON 외의 다른 텍스트는 절대 포함하지 마십시오.
    
    {{
      "target_keywords": ["연관키워드1", "연관키워드2", "연관키워드3"],
      "hooking_titles": [
         "자극적이고 직관적인 타이틀 1",
         "호기심을 자극하는 타이틀 2",
         "이득과 공포를 자극하는 타이틀 3",
         "신뢰감을 주는 타이틀 4",
         "소셜 증거를 활용한 타이틀 5"
      ],
      "marketing_outline": {{
         "step1_hooking": "1단계 도입부: 독자의 가려운 곳을 긁어주고 주의를 완전히 사로잡는 강력한 오프닝 전략",
         "step2_problem": "2단계 문제 제기: 독자가 마주한 고통과 갈증을 공감하고 극대화하여 해결의 필요성 증폭",
         "step3_solution": "3단계 해결책 제시: 당사의 제안이 왜 유일하고 확실한 대안인지 설득력 있는 증거 제시",
         "step4_action": "4단계 행동 촉구: 지금 당장 사거나 행동해야 하는 한정성 및 강력한 베네핏 제안"
      }},
      "image_prompt": "DALL-E 3나 미드저니에 입력하면 바로 매력적인 블로그 썸네일이 나올 수 있는 영문 이미지 생성 프롬프트"
    }}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    res = requests.post(url, headers=headers, json=payload, timeout=20)
    if res.status_code == 200:
        result_json = res.json()
        raw_text = result_json['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw_text)
    else:
        raise Exception(f"Gemini API 호출 실패 (코드 {res.status_code}): {res.text}")

# --- 메인 화면 레이아웃 구성 ---
st.markdown('<div class="main-card">', unsafe_allow_data_allowed=True)
st.markdown('<div class="main-title">실시간 트렌드 기반 마케팅 기획기</div>', unsafe_allow_data_allowed=True)
st.markdown('<div class="sub-title">핵심 키워드 하나로 네이버와 구글의 실시간 뉴스 데이터를 자동 수집하고,<br>타겟 독자의 심리를 꿰뚫는 완벽한 4단계 마케팅 기획안을 도출합니다.</div>', unsafe_allow_data_allowed=True)

# 텍스트 입력창 (1번 레이아웃처럼 깔끔하고 정렬된 스타일)
st.markdown('<div class="input-label">기획할 핵심 타겟 키워드를 입력해 주세요</div>', unsafe_allow_data_allowed=True)
search_keyword = st.text_input(
    "키워드 입력창", 
    placeholder="예시) 성인 심리상담, 주말 근교 드라이브, 브랜드 창업", 
    label_visibility="collapsed"
)

st.markdown('<div class="divider"></div>', unsafe_allow_data_allowed=True)

# 작동 버튼 (브랜드 오렌지 컬러 적용)
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #FF5A1F !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #E04E1A !important;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_data_allowed=True
)

if st.button("실시간 시장 분석 및 고효율 마케팅 기획 시작"):
    if not search_keyword.strip():
        st.warning("👉 키워드를 먼저 입력해 주세요!")
    elif not api_key_to_use:
        st.error("🔑 API 키가 설정되지 않았습니다. 왼쪽 사이드바에 Gemini API Key를 입력하거나 시스템 설정을 완료해 주세요.")
    else:
        with st.status("🚀 실시간 시장 정보 탐색 및 기획안 작성 중...", expanded=True) as status:
            st.write("🔍 네이버 최신 트렌드 정보 수집 중...")
            naver_titles = fetch_naver_search(search_keyword)
            
            st.write("🔍 구글 뉴스 실시간 동향 분석 중...")
            google_titles = fetch_google_news(search_keyword)
            
            st.write("🧠 수석 마케터 인공지능 기획 수립 중...")
            try:
                plan = generate_marketing_plan(api_key_to_use, search_keyword, naver_titles, google_titles)
                status.update(label="✅ 마케팅 기획 수립 및 자동 저장 완료!", state="complete")
                
                # 결과 세션 저장 (추후 다운로드 및 통합 연동 대비)
                st.session_state['marketing_plan'] = plan
                st.session_state['run_success'] = True
            except Exception as e:
                status.update(label="❌ 기획안 도출 오류 발생", state="error")
                st.error(f"상세 오류 원인: {str(e)}")

# 결과 출력 화면
if st.session_state.get('run_success', False):
    plan = st.session_state['marketing_plan']
    
    st.markdown('<div class="success-card">', unsafe_allow_data_allowed=True)
    st.subheader("🎯 추천 타겟 연관 키워드")
    st.write(", ".join([f"`#{k}`" for k in plan['target_keywords']]))
    st.markdown('</div>', unsafe_allow_data_allowed=True)
    
    st.markdown('<div class="success-card">', unsafe_allow_data_allowed=True)
    st.subheader("🔥 독자를 사로잡는 강력한 타이틀 (Hooking)")
    for i, title in enumerate(plan['hooking_titles'], 1):
        st.write(f"**{i}.** {title}")
    st.markdown('</div>', unsafe_allow_data_allowed=True)
    
    st.markdown('<div class="success-card">', unsafe_allow_data_allowed=True)
    st.subheader("📋 설득력을 극대화하는 4단계 마케팅 기획 프레임")
    st.write("**1단계: 주의 집중 (Hooking)**")
    st.info(plan['marketing_outline']['step1_hooking'])
    st.write("**2단계: 문제 제기 (Problem)**")
    st.info(plan['marketing_outline']['step2_problem'])
    st.write("**3단계: 해결책 제시 (Solution)**")
    st.info(plan['marketing_outline']['step3_solution'])
    st.write("**4단계: 행동 촉구 (Action)**")
    st.info(plan['marketing_outline']['step4_action'])
    st.markdown('</div>', unsafe_allow_data_allowed=True)
    
    st.markdown('<div class="success-card">', unsafe_allow_data_allowed=True)
    st.subheader("🎨 추천 AI 이미지 생성 영어 프롬프트")
    st.code(plan['image_prompt'], language="text")
    st.markdown('</div>', unsafe_allow_data_allowed=True)

st.markdown('</div>', unsafe_allow_data_allowed=True)
