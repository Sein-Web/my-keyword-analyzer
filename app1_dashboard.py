import streamlit as st
import json
import os
import requests
import urllib.parse
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1. 경로 설정 및 API 키 저장/불러오기 기능
# ---------------------------------------------------------------------------
BASE_DIR = os.path.expanduser("~/Documents/Marketing/today_topic")
BLOG_DIR = os.path.join(BASE_DIR, "blog")
INSTA_DIR = os.path.join(BASE_DIR, "instagram")
KEY_FILE_PATH = os.path.expanduser("~/Documents/Marketing/gemini_api_key.txt")

# 폴더 자동 생성
os.makedirs(BLOG_DIR, exist_ok=True)
os.makedirs(INSTA_DIR, exist_ok=True)

def save_api_key_locally(api_key):
    try:
        os.makedirs(os.path.dirname(KEY_FILE_PATH), exist_ok=True)
        with open(KEY_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(api_key.strip())
        return True
    except:
        return False

def load_api_key_locally():
    if os.path.exists(KEY_FILE_PATH):
        try:
            with open(KEY_FILE_PATH, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    return val
        except:
            pass
    return ""

# ---------------------------------------------------------------------------
# 2. 실시간 외부 데이터 수집 엔진
# ---------------------------------------------------------------------------
def fetch_realtime_data(keyword):
    context_text = ""
    try:
        naver_url = f"https://search.naver.com/search.naver?query={urllib.parse.quote(keyword)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(naver_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = [tag.get_text().strip() for tag in soup.select(".api_txt_lines, .total_dsc, .dsc_txt")[:12]]
            if snippets:
                context_text += "[Naver Search Results]\n" + "\n".join(f"- {s}" for s in snippets) + "\n\n"
    except:
        pass

    try:
        google_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(google_url, timeout=5)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            titles = [item.find("title").text for item in root.findall(".//item")[:8] if item.find("title") is not None]
            if titles:
                context_text += "[Google News Headlines]\n" + "\n".join(f"- {t}" for t in titles) + "\n\n"
    except:
        pass

    return context_text.strip()

# ---------------------------------------------------------------------------
# 3. Gemini API 기반 기획서 생성 엔진 (2단계 명품 본문 생성을 위한 알짜 기획 정제)
# ---------------------------------------------------------------------------
def generate_marketing_plan(api_key, keyword, category, context):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
당신은 대한민국 최고의 마케팅 기획자이자 카피라이터입니다.
제시된 실시간 데이터 분석 내용과 키워드를 바탕으로 소비자의 감성을 자극하고 행동을 이끌어내는 완벽한 기획서를 발행하세요.

[실시간 데이터 컨텍스트]
{context}

[분석 타겟 주제]
- 키워드: {keyword}
- 카테고리: {category}

반드시 아래 JSON 포맷 표준을 정확하게 준수하여 결과를 반환하세요. 마크다운 기호(```json 등)는 절대 포함하지 말고 순수한 JSON 문자열만 출력해야 합니다.

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
  "image_prompt": "A highly detailed warm cinematic photography of a professional stylish Korean individual engaging with {keyword} concept, soft emotional indoor studio lighting, neutral colors, 8k resolution, award-winning composition, realistic skin texture, no text"
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
# 4. 정밀 보정된 감성적 미색 테마 UI 스타일링 (불필요한 모든 사각상자 완벽 제거)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="1단계: 실시간 트렌드 마케팅 기획기", page_icon="📈", layout="centered")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 기본 배경 및 글꼴 설정 */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FAF9F6 !important; /* 따뜻하고 연한 고급 미색 */
        font-family: 'Pretendard', sans-serif !important;
        color: #2D3748 !important;
    }
    
    .main-container {
        max-width: 860px;
        margin: 0 auto;
        padding: 40px 20px;
    }
    
    /* 입력창 및 결과창을 가두던 유령 테두리/박스들 완전히 강제 제거 */
    div[data-testid="stVerticalBlock"] > div, 
    div[data-testid="stVerticalBlock"],
    div[class^="st-emotion-cache"], .element-container {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-style: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    
    .brand-title {
        font-size: 32px;
        font-weight: 800;
        color: #1A202C;
        letter-spacing: -0.8px;
        margin-bottom: 12px;
        text-align: center;
    }
    
    .brand-subtitle {
        font-size: 15px;
        color: #718096;
        text-align: center;
        margin-bottom: 45px;
        line-height: 1.6;
    }
    
    /* 섹션 타이틀 */
    .section-title {
        font-size: 21px;
        font-weight: 800;
        color: #1A202C;
        border-left: 5px solid #FF5A1F;
        padding-left: 14px;
        margin-top: 40px;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }
    
    /* 키워드 가로 배치 */
    .keyword-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    
    .keyword-badge {
        background-color: #EDF2F7;
        color: #2B6CB0;
        padding: 8px 18px;
        border-radius: 30px;
        font-size: 14px;
        font-weight: 600;
        white-space: nowrap;
        display: inline-block;
        border: 1px solid #E2E8F0;
    }
    
    /* 헤드라인 */
    .headline-item {
        font-size: 16.5px;
        font-weight: 700;
        color: #2D3748;
        line-height: 1.6;
        padding: 16px 20px;
        background-color: #FFFFFF;
        border-left: 4px solid #CBD5E0;
        margin-bottom: 12px;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    
    /* 4단계 구조 */
    .framework-step {
        margin-bottom: 30px;
        line-height: 1.8;
    }
    
    .step-header {
        font-size: 16.5px;
        font-weight: 800;
        color: #DD6B20;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .step-body {
        font-size: 15.5px;
        color: #4A5568;
        font-weight: 400;
        text-align: justify;
    }
    
    /* 이미지 프롬프트 상자 (단축키 충돌을 완벽 차단하는 순수 정적 컨테이너) */
    .prompt-text-box {
        background-color: #EDF2F7 !important;
        border: 1px solid #CBD5E0 !important;
        border-radius: 8px !important;
        padding: 18px 22px !important;
        font-family: 'Pretendard', sans-serif !important;
        font-size: 15.5px !important;
        color: #2D3748 !important;
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        line-height: 1.6 !important;
        margin-bottom: 15px !important;
    }
    
    /* 복사 성공 토스트 알림 메시지 스타일 */
    .copy-toast {
        display: none;
        background-color: #2D3748;
        color: #FFFFFF;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 14px;
        margin-top: 10px;
        font-weight: 600;
    }
    
    /* 주황색 버튼 스타일 */
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
    
    /* 사이드바 UI */
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
    }
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label {
        color: #F8FAFC !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        caret-color: #0F172A !important;
        border-radius: 6px !important;
        border: 1px solid #94A3B8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 5. 사이드바 (API 설정)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔑 API 키 설정")
    st.markdown("본 프로그램을 사용하려면 Gemini API 키가 필요합니다.")
    
    stored_key = load_api_key_locally()
    
    user_api_key = st.text_input("Gemini API Key", value=stored_key, type="password", placeholder="여기에 제미나이 API 키를 입력하세요")
    
    if st.button("🔑 입력한 API 키 로컬에 저장"):
        if user_api_key.strip():
            if save_api_key_locally(user_api_key):
                st.success("API 키가 안전하게 연동 및 기기에 저장되었습니다!")
            else:
                st.error("저장 중 오류 발생")
        else:
            st.warning("저장할 키를 먼저 입력하세요.")
            
    st.markdown("---")
    st.markdown("[👉 Google AI Studio 키 발급받기](https://aistudio.google.com/)")

# ---------------------------------------------------------------------------
# 6. 메인 화면 UI 구현 (연베이지 사각 테두리까지 완전 삭제하여 전면 트인 레이아웃)
# ---------------------------------------------------------------------------
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<div class="brand-title">📈 1단계: 실시간 트렌드 마케팅 기획기</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-subtitle">실시간 검색 트렌드를 기반으로 고성능 마케팅 설계를 정교하게 구성합니다.</div>', unsafe_allow_html=True)

# 입력 컨트롤러 (상자 태그를 일절 배제하여 연베이지 보더 라인을 원천 삭제)
col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input("📝 기획할 주제 또는 핵심 키워드를 입력하세요.", placeholder="예: 성인 심리상담, 바이브코딩")
with col2:
    category = st.selectbox("플랫폼 선택", ["네이버 블로그", "인스타그램 카드뉴스"])
    
run_button = st.button("🚀 실시간 시장 분석 및 고효율 마케팅 기획 시작")

# ---------------------------------------------------------------------------
# 7. 기획 실행 및 결과 자동 로컬 저장 / 파일 이름 정교화
# ---------------------------------------------------------------------------
if run_button:
    api_key_to_use = user_api_key if user_api_key else stored_key
    if not api_key_to_use:
        st.error("🚨 API 키가 감지되지 않았습니다. 왼쪽 사이드바에 먼저 입력 후 저장해주세요.")
    elif not keyword.strip():
        st.warning("🚨 분석할 주제 키워드를 채워주세요.")
    else:
        with st.status("🔍 실시간 데이터를 가져오는 중...", expanded=True) as status:
            try:
                status.write("1. 네이버 통합검색 및 구글 뉴스 실시간 크롤링 작동...")
                realtime_context = fetch_realtime_data(keyword)
                
                status.write("2. Gemini AI 기획 메커니즘 엔진 가동...")
                raw_json = generate_marketing_plan(api_key_to_use, keyword, category, realtime_context)
                
                plan_data = json.loads(raw_json)
                status.update(label="✅ 마케팅 기획서 작성 완료!", state="complete")
                
                st.session_state["plan_result"] = plan_data
                st.session_state["analyzed_keyword"] = keyword
                st.session_state["analyzed_category"] = category
                
                # -----------------------------------------------------------
                # 동적 파일 관리 시스템 (요청 경로에 따른 명명 및 자동 물리 저장)
                # -----------------------------------------------------------
                today_str = datetime.today().strftime("%Y-%m-%d")
                clean_keyword = "".join(c for c in keyword if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                
                # 블로그/인스타 폴더 분리 구조
                if category == "네이버 블로그":
                    target_folder = BLOG_DIR
                else:
                    target_folder = INSTA_DIR
                    
                custom_filename = f"{today_str}_{clean_keyword}.json"
                local_auto_save_path = os.path.join(target_folder, custom_filename)
                
                # 지정 경로 자동 물리 저장 실행 (2단계 본문 생성 전용 데이터만 정갈히 저장)
                with open(local_auto_save_path, "w", encoding="utf-8") as f:
                    json.dump(plan_data, f, ensure_ascii=False, indent=2)
                
                st.session_state["saved_file_path"] = local_auto_save_path
                st.session_state["custom_filename"] = custom_filename
                
            except Exception as e:
                status.update(label="❌ 기획 실패", state="error")
                st.error(f"오류가 발생했습니다: {str(e)}")

# 결과 출력 화면 구성
if "plan_result" in st.session_state:
    data = st.session_state["plan_result"]
    kw = st.session_state["analyzed_keyword"]
    cat = st.session_state["analyzed_category"]
    
    # A. 타겟 및 연관 고효율 키워드
    st.markdown('<div class="section-title">🎯 타겟 및 연관 고효율 키워드</div>', unsafe_allow_html=True)
    keyword_html = '<div class="keyword-container">'
    for token in data.get("target_keywords", []):
        keyword_html += f'<span class="keyword-badge">#{token}</span>'
    keyword_html += '</div>'
    st.markdown(keyword_html, unsafe_allow_html=True)
    
    # B. 고클릭 감성 헤드라인 제안 (5종)
    st.markdown('<div class="section-title">🔥 고클릭 감성 헤드라인 제안 (5종)</div>', unsafe_allow_html=True)
    headline_html = ""
    for idx, title in enumerate(data.get("hooking_titles", []), 1):
        headline_html += f'<div class="headline-item">{idx}. {title}</div>'
    st.markdown(headline_html, unsafe_allow_html=True)
    
    # C. 4단계 마케팅 심리 프레임워크 (상자 없이 완벽히 트인 레이아웃)
    st.markdown('<div class="section-title">📊 4단계 마케팅 심리 프레임워크 분석</div>', unsafe_allow_html=True)
    outline = data.get("outline", {})
    framework_html = f"""
    <div class="framework-step">
        <div class="step-header">📢 1단계. 독자들의 잠재적 고통 자극 [문제제기]</div>
        <div class="step-body">{outline.get('step1_problem', '')}</div>
    </div>
    <div class="framework-step">
        <div class="step-header">🤝 2단계. 속마음을 알아주는 정서적 연결 [감성공감]</div>
        <div class="step-body">{outline.get('step2_empathy', '')}</div>
    </div>
    <div class="framework-step">
        <div class="step-header">💡 3단계. 구체적이고 현실적인 변화 가이드 [해결제시]</div>
        <div class="step-body">{outline.get('step3_solution', '')}</div>
    </div>
    <div class="framework-step">
        <div class="step-header">🎯 4단계. 망설임 없는 행동 및 전환 유도 [행동촉구]</div>
        <div class="step-body">{outline.get('step4_cta', '')}</div>
    </div>
    """
    st.markdown(framework_html, unsafe_allow_html=True)

    # D. 이미지 매칭 프롬프트 (단축키 충돌 오작동이 완벽하게 방지된 원클릭 무결성 복사 버튼 적용)
    st.markdown('<div class="section-title">🎨 추천 비주얼 이미지 프롬프트</div>', unsafe_allow_html=True)
    
    # 순수 HTML 렌더링으로 팝업 에러를 강제 차단하고 클립보드 원클릭 복사 탑재
    prompt_value = data.get("image_prompt", "").replace("'", "\\'")
    copier_html = f"""
    <div class="prompt-text-box" id="promptText">{data.get("image_prompt", "")}</div>
    <button onclick="copyPrompt()" style="
        background-color: #2D3748;
        color: white;
        border: none;
        padding: 10px 18px;
        border-radius: 6px;
        font-size: 13.5px;
        font-weight: 700;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 20px;
    ">📋 이미지 프롬프트 복사하기</button>
    <div id="toastMessage" class="copy-toast">✓ 클립보드에 프롬프트가 복사되었습니다!</div>
    
    <script>
        function copyPrompt() {{
            var text = document.getElementById('promptText').innerText;
            navigator.clipboard.writeText(text).then(function() {{
                var toast = document.getElementById('toastMessage');
                toast.style.display = 'block';
                setTimeout(function() {{
                    toast.style.display = 'none';
                }}, 2500);
            }});
        }}
    </script>
    """
    st.markdown(copier_html, unsafe_allow_html=True)

    # E. 2단계 본문 집필기용 기획서 내보내기 (불필요한 모든 수식어구/설명문 영구 삭제)
    st.markdown('<div class="section-title">🗳️ 기획서 내보내기</div>', unsafe_allow_html=True)
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    file_name_to_download = st.session_state.get("custom_filename", "today_topic.json")
    
    # 오직 직관적인 텍스트 다운로드 버튼 1개만 정갈하게 노출
    st.download_button(
        label=f"📥 기획서 파일 저장 ({file_name_to_download})",
        data=json_str,
        file_name=file_name_to_download,
        mime="application/json"
    )

st.markdown('</div>', unsafe_allow_html=True)
