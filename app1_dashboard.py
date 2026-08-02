import streamlit as st
import json
import os
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1. 경로 설정 및 API 키 저장/불러오기 기능
# ---------------------------------------------------------------------------
BASE_DIR = os.path.expanduser("~/Documents/Marketing")
BLOG_DIR = os.path.join(BASE_DIR, "blog")
INSTA_DIR = os.path.join(BASE_DIR, "instagram")
KEY_FILE_PATH = os.path.join(BASE_DIR, "gemini_api_key.txt")

# 폴더 생성
os.makedirs(BLOG_DIR, exist_ok=True)
os.makedirs(INSTA_DIR, exist_ok=True)

def save_api_key_locally(api_key):
    """API 키를 로컬 파일에 안전하게 저장합니다."""
    try:
        with open(KEY_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(api_key.strip())
        return True
    except Exception as e:
        return False

def load_api_key_locally():
    """저장된 API 키가 있다면 불러옵니다."""
    if os.path.exists(KEY_FILE_PATH):
        try:
            with open(KEY_FILE_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return ""
    return ""

# ---------------------------------------------------------------------------
# 2. 실시간 외부 데이터 수집 엔진
# ---------------------------------------------------------------------------
def fetch_realtime_data(keyword):
    """네이버 통합검색 결과 및 구글 뉴스 RSS 피드를 수집하여 원천 컨텍스트를 구축합니다."""
    context_text = ""
    
    # 1) 네이버 검색결과 수집
    try:
        naver_url = f"https://search.naver.com/search.naver?query={urllib.parse.quote(keyword)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(naver_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = [tag.get_text().strip() for tag in soup.select(".api_txt_lines, .total_dsc, .dsc_txt")[:12]]
            if snippets:
                context_text += "[Naver Search Results]\n" + "\n".join(f"- {s}" for s in snippets) + "\n\n"
    except Exception:
        pass

    # 2) 구글 뉴스 RSS 수집
    try:
        google_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(google_url, timeout=5)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            titles = [item.find("title").text for item in root.findall(".//item")[:8] if item.find("title") is not None]
            if titles:
                context_text += "[Google News Headlines]\n" + "\n".join(f"- {t}" for t in titles) + "\n\n"
    except Exception:
        pass

    return context_text.strip()

# ---------------------------------------------------------------------------
# 3. Gemini API 기반 기획서 생성 엔진
# ---------------------------------------------------------------------------
def generate_marketing_plan(api_key, keyword, category, context):
    """Gemini 2.5 Flash를 호출하여 정교한 JSON 포맷 기획서를 발행합니다."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
당신은 대한민국 최고의 마케팅 기획자이자 카피라이터입니다.
제시된 실시간 데이터 분석 내용과 키워드를 바탕으로 소비자의 감성을 자극하고 행동을 이끌어내는 완벽한 기획서를 발행하세요.

[실시간 데이터 컨텍스트]
{context}

[분석 타겟 주제]
- 키워드: {keyword}
- 카테고리: {category} (블로그 또는 인스타그램 맞춤형 기획 제공 필요)

반드시 아래 JSON 포맷 표준을 정확하게 준수하여 결과를 반환하세요. 마크다운 기호(```json 등)는 절대 포함하지 말고 순수한 JSON 문자열만 출력해야 합니다. 대괄호, 중괄호가 누락되지 않도록 주의하세요.

{{
  "target_keywords": ["연관키워드1", "연관키워드2", "연관키워드3", "연관키워드4", "연관키워드5"],
  "hooking_titles": [
    "호기심을 유발하고 클릭할 수밖에 없는 감성 헤드라인 1",
    "호기심을 유발하고 클릭할 수밖에 없는 감성 헤드라인 2",
    "호기심을 유발하고 클릭할 수밖에 없는 감성 헤드라인 3",
    "호기심을 유발하고 클릭할 수밖에 없는 감성 헤드라인 4",
    "호기심을 유발하고 클릭할 수밖에 없는 감성 헤드라인 5"
  ],
  "outline": {{
    "step1_problem": "독자가 현재 겪고 있는 가장 고통스럽고 공감 가며 현실적인 문제 상황을 생생하게 묘사",
    "step2_empathy": "그 문제에 대한 심층적인 정서적 공감과 위로, 독자의 속마음을 대변하는 따뜻한 메시지",
    "step3_solution": "기획한 주제와 관련된 명확하고 구체적이며 매력적인 실질적 해결책과 행동 가이드 제시",
    "step4_cta": "자연스럽게 댓글, 공유, 이웃추가, 혹은 구매 등의 행동을 강력하게 유도하는 메시지"
  }},
  "image_prompt": "professional-realistic-aesthetic-photography-of-{keyword}-concept-with-warm-lighting-cinematic"
}}
"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.75
        }
    }
    
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=45)
    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        raise Exception(f"Gemini API Error: {response.status_code} - {response.text}")

# ---------------------------------------------------------------------------
# 4. 고급스러운 미색 테마 UI 스타일링
# ---------------------------------------------------------------------------
st.set_page_config(page_title="1단계: 실시간 트렌드 마케팅 기획기", page_icon="📈", layout="centered")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
        font-family: 'Pretendard', sans-serif !important;
        color: #1E293B !important;
    }
    
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 40px 20px;
    }
    
    .card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 25px;
    }
    
    .brand-title {
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
        text-align: center;
    }
    
    .brand-subtitle {
        font-size: 14px;
        color: #64748B;
        text-align: center;
        margin-bottom: 35px;
        line-height: 1.6;
    }
    
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1E293B;
        border-left: 4px solid #FF5A1F;
        padding-left: 12px;
        margin-bottom: 15px;
    }
    
    /* 주황색 버튼 스타일링 */
    div.stButton > button {
        background-color: #FF5A1F !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 14px 28px !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        transition: background 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(255, 90, 31, 0.2) !important;
    }
    div.stButton > button:hover {
        background-color: #E04E1A !important;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    
    /* 성공 안내 박스 */
    .success-box {
        background-color: #F0FDF4;
        border-left: 5px solid #16A34A;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 5. 사이드바 (API 설정 및 영구 저장 버튼)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔑 API 키 설정")
    st.markdown("본 프로그램을 사용하려면 Gemini API 키가 필요합니다.")
    
    # 이전에 로컬에 저장된 키 로드
    stored_key = load_api_key_locally()
    
    # 비밀번호 형태로 입력 필드 구성
    user_api_key = st.text_input("Gemini API Key", value=stored_key, type="password", placeholder="AI Studio에서 발급받은 키 입력")
    
    if st.button("🔑 API 키 영구 저장"):
        if user_api_key.strip():
            if save_api_key_locally(user_api_key):
                st.success("API 키가 안전하게 기기에 저장되었습니다! (다음 접속 시 자동 적용)")
            else:
                st.error("저장 중 오류가 발생했습니다.")
        else:
            st.warning("저장할 키를 입력하세요.")
            
    st.markdown("---")
    st.markdown("[👉 Google AI Studio 키 발급받기](https://aistudio.google.com/)")

# ---------------------------------------------------------------------------
# 6. 메인 화면 UI 구현
# ---------------------------------------------------------------------------
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<div class="brand-title">📈 1단계: 실시간 트렌드 마케팅 기획기</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-subtitle">실시간 네이버 통합검색 및 구글 뉴스를 크롤링하여 소비자의 마음을 훔치는 감성 마케팅 전략 기획서를 정교하게 도출합니다.</div>', unsafe_allow_html=True)

# 입력단 구성
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("📝 기획할 주제 또는 핵심 키워드를 입력하세요.", placeholder="예: 성인 심리상담, 주말 근교 드라이브, 스마트스토어 부업")
    with col2:
        category = st.selectbox("플랫폼 선택", ["네이버 블로그", "인스타그램 카드뉴스"])
        
    run_button = st.button("🚀 실시간 시장 분석 및 고효율 마케팅 기획 시작")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 7. 기획 실행 및 결과 표출
# ---------------------------------------------------------------------------
if run_button:
    # API 키 검증
    api_key_to_use = user_api_key if user_api_key else stored_key
    if not api_key_to_use:
        st.error("🚨 API 키가 누락되었습니다! 왼쪽 사이드바에 Gemini API 키를 입력하고 저장 버튼을 눌러주세요.")
    elif not keyword.strip():
        st.warning("🚨 분석할 주제 키워드를 입력해 주세요.")
    else:
        with st.status("🔍 실시간 트렌드 분석 및 기획서 작성 중...", expanded=True) as status:
            try:
                # 1) 실시간 크롤러 작동
                status.write("1. 네이버 및 구글 실시간 정보 수집 중...")
                realtime_context = fetch_realtime_data(keyword)
                
                # 2) AI 기획 발행
                status.write("2. Gemini AI 기반 마케팅 페르소나 분석 및 프레임워크 설계 중...")
                raw_json = generate_marketing_plan(api_key_to_use, keyword, category, realtime_context)
                
                # JSON 결과 파싱
                plan_data = json.loads(raw_json)
                status.update(label="✅ 분석 및 전략 기획서 발행 완료!", state="complete")
                
                # 결과 출력을 위한 상태 저장
                st.session_state["plan_result"] = plan_data
                st.session_state["analyzed_keyword"] = keyword
                st.session_state["analyzed_category"] = category
                
            except Exception as e:
                status.update(label="❌ 기획 실패", state="error")
                st.error(f"오류가 발생했습니다: {str(e)}")

# 기획서 결과 렌더링
if "plan_result" in st.session_state:
    data = st.session_state["plan_result"]
    kw = st.session_state["analyzed_keyword"]
    cat = st.session_state["analyzed_category"]
    
    st.markdown('<div class="success-box"><strong>🎉 마케팅 기획서 발행 완료!</strong> 아래 내용을 확인하고 <b>기획서 JSON 다운로드</b>를 진행해 주세요.</div>', unsafe_allow_html=True)
    
    # 1) 타겟 키워드 분석 결과
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎯 타겟 및 연관 고효율 키워드</div>', unsafe_allow_html=True)
    cols = st.columns(len(data.get("target_keywords", [])))
    for i, token in enumerate(data.get("target_keywords", [])):
        with cols[i]:
            st.info(f"#{token}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 2) 클릭률 높은 헤드라인 제안
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔥 고클릭 감성 헤드라인 제안 (5종)</div>', unsafe_allow_html=True)
    for idx, title in enumerate(data.get("hooking_titles", []), 1):
        st.markdown(f"**{idx}.** {title}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 3) 4단계 고효율 마케팅 구성안
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 4단계 마케팅 심리 프레임워크</div>', unsafe_allow_html=True)
    outline = data.get("outline", {})
    st.markdown(f"**1단계 [문제제기]:** {outline.get('step1_problem', '')}")
    st.markdown(f"**2단계 [감성공감]:** {outline.get('step2_empathy', '')}")
    st.markdown(f"**3단계 [해결제시]:** {outline.get('step3_solution', '')}")
    st.markdown(f"**4단계 [행동유도]:** {outline.get('step4_cta', '')}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 4) 이미지 생성 가이드라인
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎨 AI 이미지 매칭 프롬프트</div>', unsafe_allow_html=True)
    st.code(data.get("image_prompt", ""), language="text")
    st.markdown('</div>', unsafe_allow_html=True)

    # 5) 파일 저장 및 내보내기 버튼 구역
    st.markdown('<div class="card" style="text-align: center;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📥 2단계로 보낼 기획서 파일 다운로드</div>', unsafe_allow_html=True)
    st.write("아래 버튼을 눌러 JSON 기획 파일을 PC에 저장하세요. 이 다운로드한 파일 그대로 2단계 본문 자동 집필기에 업로드하면 완벽한 글이 자동 창작됩니다.")
    
    # JSON 파일 데이터 생성
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    file_name = "today_topic.json" if cat == "네이버 블로그" else "today_topic_insta.json"
    
    st.download_button(
        label="📥 마케팅 기획서 JSON 다운로드",
        data=json_str,
        file_name=file_name,
        mime="application/json"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
