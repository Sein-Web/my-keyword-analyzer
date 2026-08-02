import streamlit as st
import json
import os
import re
import requests

# -----------------------------------------------------------------------------
# 1. Gemini 라이브러리 호환 설정
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

BASE_DIR = os.path.expanduser("~/Documents/Marketing")
BLOG_DIR = os.path.join(BASE_DIR, "blog")

def get_gemini_api_key_details():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"], "Streamlit Secrets", "success"
    key_path = os.path.join(BLOG_DIR, "gemini api key", "api key.txt")
    if os.path.exists(key_path):
        try:
            with open(key_path, "r", encoding="utf-8-sig") as f:
                key = f.read().strip()
                key = re.sub(r'[\u200b-\u200d\ufeff\xa0]', '', key).strip()
                if key:
                    return key, key_path, "success"
        except Exception:
            pass
    return "", "", "not_found"

# -----------------------------------------------------------------------------
# 2. 본문 고도화 자동 집필 엔진
# -----------------------------------------------------------------------------
def generate_copywriting(api_key, plan_data, platform_type="blog"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    outline = plan_data.get("outline", {})
    keywords = plan_data.get("target_keywords", [])
    titles = plan_data.get("hooking_titles", [])

    if platform_type == "blog":
        prompt = f"""
        당신은 대한민국 최정상급의 전문 카피라이터이자 블로그 마케터입니다.
        아래 제공된 [기획안]의 설계에 맞추어 네이버 블로그 검색 상위 노출에 최적화된 1,500자~2,000자 분량의 정밀하고 긴 호흡의 설득형 포스팅 원고를 작성해 주세요.

        [기획안]
        - 대상 키워드군: {", ".join(keywords)}
        - 선택할 타이틀 리스트: {", ".join(titles)}
        - 1단계 (문제 제시): {outline.get("step1_problem", "")}
        - 2단계 (유대 형성): {outline.get("step2_empathy", "")}
        - 3단계 (해결책 처방): {outline.get("step3_solution", "")}
        - 4단계 (행동 촉구): {outline.get("step4_cta", "")}

        [원고 작성 지침]
        1. 단순 나열이 아닌, 독자가 실제로 전문 사설을 읽는 듯한 자연스럽고 탄탄한 스토리텔링 문체로 작성하세요.
        2. 기획안의 1단계부터 4단계까지의 뼈대가 잘 드러나도록 소제목을 작성하고 깊이 있는 내용으로 채우세요.
        3. 연관 키워드들이 문맥 흐름 속에 3~4번 이상 자연스럽게 녹아들게 하세요.
        4. 친근하면서도 고도의 신뢰감을 전달할 수 있는 어조(~합니다, ~해결해 드립니다 등)를 사용하세요.
        5. 마크다운 스타일을 활용해 가독성 있게 줄을 나누고 핵심 어휘는 강조 처리해 주세요.
        """
    else:
        prompt = f"""
        당신은 대한민국 대표 인스타그램 브랜딩 채널을 운영하는 파워 인플루언서이자 비주얼 카피라이터입니다.
        제공된 [기획안]을 바탕으로, 카드뉴스 이미지 슬라이드 대본과 피드 캡션을 기획해 주세요.

        [기획안]
        - 대상 키워드군: {", ".join(keywords)}
        - 선택할 타이틀 리스트: {", ".join(titles)}
        - 1단계 (문제 제시): {outline.get("step1_problem", "")}
        - 2단계 (유대 형성): {outline.get("step2_empathy", "")}
        - 3단계 (해결책 처방): {outline.get("step3_solution", "")}
        - 4단계 (행동 촉구): {outline.get("step4_cta", "")}

        [원고 작성 지침]
        1. **카드뉴스 슬라이드(총 5~6장)**: 
           - 각 슬라이드(표지, 본문1, 2, 3, 결론)에 들어갈 '디자인 시각 기획'과 '핵심 한 줄 텍스트 카피'를 나누어 작성해 주세요.
        2. **피드 본문 캡션**: 
           - 인스타그램 특유의 줄글 스타일(이모지 적극 활용, 가독성 높은 간격 배치)로 작성하고 마지막에 해시태그를 포함하세요.
        """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"오류 발생 (상태 코드: {res.status_code})\n{res.text}"
    except Exception as e:
        return f"AI 연결 중 기술적 예외가 발생했습니다.\n{str(e)}"

# -----------------------------------------------------------------------------
# 3. 레이아웃 테마 정의 (기획기와 통일된 명품 테마)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 실시간 원고 자동 집필기",
    page_icon="✍️",
    layout="wide"
)

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
        font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 860px !important; 
        margin: 50px auto !important;
        padding: 40px 50px !important;
        background-color: #FFFFFF !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.04) !important;
        border: none !important;
    }
    .brand-header-area {
        text-align: center;
        margin-bottom: 35px;
        padding-bottom: 25px;
        border-bottom: 2px dashed #E2E8F0;
    }
    .brand-main-title {
        font-size: 26px;
        font-weight: 850;
        color: #1E3A8A !important; 
        letter-spacing: -0.7px;
    }
    .brand-sub-title {
        font-size: 13.5px;
        color: #64748B !important;
        font-weight: 400;
        margin-top: 6px;
    }
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
    .result-box {
        background-color: #F8FAFC;
        border-radius: 12px;
        padding: 25px 30px;
        border: 1px solid #E2E8F0;
        margin-top: 25px;
        font-size: 15px;
        line-height: 1.8;
        color: #334155;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.markdown("### 🔑 API 설정")
    user_api_key = st.text_input(
        "Gemini API Key 입력",
        type="password",
        placeholder="AIzaSy...",
        help="Google AI Studio에서 발급받은 API 키를 넣어주세요."
    )

selected_api_key = ""
if user_api_key.strip():
    selected_api_key = user_api_key.strip()
else:
    system_key, key_path, status_code = get_gemini_api_key_details()
    if status_code == "success":
        selected_api_key = system_key

# 메인 헤더
st.markdown("""
<div class="brand-header-area">
    <div class="brand-main-title">✍️ AI 고효율 마케팅 본문 자동 집필기</div>
    <div class="brand-sub-title">1단계에서 내려받은 기획서 파일을 넣으시면 상위 노출과 고전환 설득 본문을 자동으로 창작합니다.</div>
</div>
""", unsafe_allow_html=True)

tab_blog, tab_insta = st.tabs(["📝 블로그 원고 집필", "📸 인스타그램 대본 집필"])

def run_writer_layout(platform_key, file_label):
    st.write("")
    st.markdown(f"**📂 1단계에서 다운로드받은 기획서 JSON 파일을 올려주세요:**")
    
    uploaded_file = st.file_uploader(
        "기획서 파일 선택",
        type=["json"],
        label_visibility="collapsed",
        key=f"uploader_{platform_key}"
    )

    if uploaded_file is not None:
        try:
            plan_data = json.load(uploaded_file)
            st.success("✅ 기획서 데이터를 성공적으로 불러왔습니다.")
            
            # 기획서 요약 내용 보여주기
            keywords = plan_data.get("target_keywords", [])
            st.info(f"🎯 **타겟 연관 키워드:** {', '.join(keywords[:5])}")
            
            st.write("")
            if st.button("🔥 마케팅 설득 본문 초고 집필 시작", key=f"btn_{platform_key}"):
                if not selected_api_key:
                    st.error("🔑 API 키가 필요합니다. 왼쪽 사이드바에 Gemini API Key를 입력해 주세요.")
                    return
                
                with st.spinner("🧠 15년 차 브랜드 마케터 AI가 대본 집필 중... 잠시만 기다려 주세요."):
                    generated_text = generate_copywriting(selected_api_key, plan_data, platform_type=platform_key)
                    st.session_state[f"written_{platform_key}"] = generated_text
                    
        except Exception as e:
            st.error(f"기획서 파일을 해석하는 데 실패했습니다. 올바른 JSON 파일인지 확인해 주세요. 오차 로그: {e}")

    # 집필 완료 결과 보여주기 및 저장 기능
    if f"written_{platform_key}" in st.session_state:
        written_text = st.session_state[f"written_{platform_key}"]
        st.markdown("### 📋 AI 작가 추천 완성형 원고 초고")
        st.markdown(f'<div class="result-box">{written_text}</div>', unsafe_allow_html=True)
        
        st.write("")
        st.download_button(
            label="💾 완성형 원고 텍스트 파일로 다운로드",
            data=written_text,
            file_name=f"finished_marketing_{platform_key}.txt",
            mime="text/plain",
            key=f"dl_finished_{platform_key}"
        )

with tab_blog:
    run_writer_layout("blog", "블로그")

with tab_insta:
    run_writer_layout("instagram", "인스타그램")
