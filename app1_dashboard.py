import streamlit as st
import os
import json
import requests
import urllib.parse
from datetime import datetime
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
# 1. 시스템 및 디렉토리 설정 (요청된 저장 경로 규칙 준수)
# -----------------------------------------------------------------------------
BASE_DIR = os.path.expanduser("~/Documents/Marketing/today_topic")
BLOG_DIR = os.path.join(BASE_DIR, "blog")
INSTA_DIR = os.path.join(BASE_DIR, "instagram")
KEY_FILE_PATH = os.path.expanduser("~/Documents/Marketing/gemini_api_key.txt")

# 폴더 생성
os.makedirs(BLOG_DIR, exist_ok=True)
os.makedirs(INSTA_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 2. API 키 로컬 저장 및 로드 함수 (최초 실행 시 빈칸 유지)
# -----------------------------------------------------------------------------
def save_api_key_locally(key_value):
    try:
        key_dir = os.path.dirname(KEY_FILE_PATH)
        os.makedirs(key_dir, exist_ok=True)
        with open(KEY_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(key_value.strip())
        return True
    except Exception as e:
        st.error(f"API 키 로컬 저장 중 오류 발생: {e}")
        return False

def load_api_key_locally():
    if os.path.exists(KEY_FILE_PATH):
        try:
            with open(KEY_FILE_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""
    return ""

# -----------------------------------------------------------------------------
# 3. 실시간 트렌드 데이터 수집 (네이버 검색 및 구글 뉴스 RSS)
# -----------------------------------------------------------------------------
def fetch_realtime_data(keyword):
    context_text = ""
    
    # 네이버 검색 결과 크롤링
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        naver_url = f"https://search.naver.com/search.naver?query={encoded_keyword}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        res = requests.get(naver_url, headers=headers, timeout=5)
        if res.status_code == 200:
            context_text += f"[Naver Search Results for '{keyword}']\n"
            context_text += res.text[:2500] + "\n\n"
    except Exception as e:
        context_text += f"[Naver Error] {e}\n\n"
        
    # 구글 뉴스 RSS 수집
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        google_rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(google_rss_url, timeout=5)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            context_text += f"[Google News RSS for '{keyword}']\n"
            for item in root.findall(".//item")[:5]:
                title = item.find("title").text if item.find("title") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                context_text += f"- Title: {title}\n  Snippet: {desc}\n"
    except Exception as e:
        context_text += f"[Google News Error] {e}\n\n"
        
    return context_text

# -----------------------------------------------------------------------------
# 4. Gemini 2.5 Flash API 활용 마케팅 기획서 생성
# -----------------------------------------------------------------------------
def generate_marketing_plan(api_key, keyword, platform, trend_context):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    system_instruction = (
        "You are an expert digital marketing strategist. Analyze the provided real-time search and news trend data, "
        "then generate a JSON-formatted marketing plan strictly following the specified schema. "
        "All output text inside the JSON must be written in fluent, professional, and highly persuasive Korean."
    )
    
    prompt = f"""
[Target Keyword]
{keyword}

[Selected Platform]
{platform}

[Real-time Trend Context Data]
{trend_context}

[Instructions]
Based on the platform ({platform}) and the trend context, generate a professional marketing plan.
You must output ONLY a valid JSON object. Do not include markdown code block formatting (like ```json ... ```).
The JSON object must strictly match this structure:
{{
  "target_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "hooking_titles": [
    "Title option 1",
    "Title option 2",
    "Title option 3",
    "Title option 4",
    "Title option 5"
  ],
  "outline": {{
    "step1": "Introduction and attention-grabbing hook",
    "step2": "Present the core problem or current trend",
    "step3": "Introduce the solution or value proposition related to {keyword}",
    "step4": "Call to action or wrap-up"
  }},
  "image_prompt": "An English prompt for AI image generation. It must be highly descriptive, professional, cinematic, and warm, representing the concept of {keyword} without using the keyword directly as text in the image."
}}
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_text.strip())
        else:
            st.error(f"Gemini API 호출 실패 (코드 {response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"기획서 생성 중 예외 발생: {e}")
        return None

# -----------------------------------------------------------------------------
# 5. UI 및 스타일 정의 (키 차단 스크립트 탑재, 불필요 상자 제거, 인풋창 복구)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="실시간 트렌드 마케팅 기획기", layout="wide")

# CSS 및 JavaScript 주입 (입력창 테두리 명확화, 빈 테두리 제거, C 단축키 원천 차단)
st.markdown("""
<style>
    /* 전체 미색 톤 배경 및 폰트 설정 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FAF9F6 !important;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 사이드바 어두운 톤 테마 */
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    
    /* 오렌지 메인 액션 버튼 */
    .stButton>button {
        background-color: #FF5A1F !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button:hover {
        background-color: #E04E1A !important;
        transform: translateY(-1px);
    }

    /* ⚠️ 중요: 유령 사각 박스 완전히 없애기 (st.markdown으로 들어가는 불필요 카드 스타일 해제) */
    .report-block, .download-card, .prompt-box {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* 💡 중요: 질문하신 "키워드 입력 및 플랫폼 선택" 텍스트박스 테두리 완벽 원상복구 및 심플 디자인 적용 */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stSelectbox"] div[role="combobox"] {
        border: 2px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 15px !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] div[role="combobox"]:focus {
        border-color: #FF5A1F !important;
        box-shadow: 0 0 0 2px rgba(255, 90, 31, 0.2) !important;
    }

    /* 키워드 태그 정렬 (줄바꿈 방지) */
    .keyword-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 15px 0 30px 0;
    }
    .keyword-badge {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
        white-space: nowrap; /* 줄바꿈 안되게 지정 */
    }

    /* 고클릭 감성 헤드라인 디자인 */
    .headline-item {
        background-color: #FFFFFF;
        border-left: 5px solid #FF5A1F;
        padding: 14px 20px;
        margin-bottom: 12px;
        border-radius: 0 8px 8px 0;
        font-size: 15px;
        font-weight: 500;
        color: #1E293B;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }

    /* 아웃라인 섹션 타이틀 및 본문 줄간격 가독성 개선 */
    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #0F172A;
        margin-top: 35px;
        margin-bottom: 15px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 8px;
    }
    .outline-step {
        font-size: 16px;
        line-height: 1.8;
        color: #334155;
        margin-bottom: 12px;
        padding-left: 10px;
    }

    /* 프롬프트 출력 에어리어 (가로 바 없이 세로로 줄바꿈 자동 적용) */
    .prompt-text {
        background-color: #F1F5F9;
        color: #334155;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 14px;
        line-height: 1.6;
        white-space: pre-wrap; /* 단어 자동 줄바꿈 활성화 */
        word-break: break-all;
        margin-bottom: 10px;
        border: 1px solid #CBD5E1;
    }

    /* 네모겹침 복사 아이콘 버튼 스타일 */
    .copy-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #FFFFFF !important;
        color: #475569 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 6px 12px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.2s;
    }
    .copy-btn:hover {
        background-color: #F1F5F9 !important;
        border-color: #94A3B8 !important;
    }
</style>

<!-- 💡 중요: Cmd+C / Ctrl+C를 눌렀을 때 Streamlit 단축키 팝업(Clear cache)이 뜨지 않도록 완벽히 방어하는 스크립트 -->
<script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'c' || e.key === 'C') {
            e.stopPropagation();
        }
    }, true);
</script>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 사이드바 UI (API 키 관리 - 최초 실행 시 공란 처리)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔑 API 키 설정")
    st.markdown("본 프로그램을 사용하려면 Gemini API 키가 필요합니다.")
    
    # 세션 상태 초기화
    if "api_key" not in st.session_state:
        st.session_state.api_key = load_api_key_locally()
        
    api_key_input = st.text_input(
        "Gemini API Key", 
        value=st.session_state.api_key, 
        type="password",
        placeholder="AIzaSy..."
    )
    
    if st.button("🔑 입력한 API 키 로컬에 저장"):
        if api_key_input.strip():
            if save_api_key_locally(api_key_input):
                st.session_state.api_key = api_key_input.strip()
                st.success("API 키가 안전하게 로컬 장치에 저장되었습니다.")
        else:
            st.warning("API 키를 입력해주세요.")
            
    st.markdown("---")
    st.markdown("[👉 Google AI Studio 키 발급받기](https://aistudio.google.com/)")

# -----------------------------------------------------------------------------
# 7. 메인 화면 UI (1단계 대시보드)
# -----------------------------------------------------------------------------
st.write("")  # 불필요한 연베이지 텍스트 상자가 있던 곳을 모두 제거하고 깔끔한 여백 처리
st.markdown("<h1 style='text-align: center; color: #0F172A; font-size: 32px; font-weight: 800; margin-bottom: 5px;'>📈 1단계: 실시간 트렌드 마케팅 기획기</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 15px; margin-bottom: 40px;'>실시간 검색 트렌드를 기반으로 고성능 마케팅 설계를 정교하게 구성합니다.</p>", unsafe_allow_html=True)

# 입력 폼 컬럼 구성 (사용자 피드백 반영: 입력 상자 테두리와 스타일 완벽 활성화)
col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input("✍️ 기획할 주제 또는 핵심 키워드를 입력하세요.", value="바이브코딩", placeholder="예: 바이브코딩, 여름 침구 세트")
with col2:
    platform = st.selectbox("플랫폼 선택", ["네이버 블로그", "인스타그램"])

# 분석 및 기획 시작 버튼
start_btn = st.button("🚀 실시간 시장 분석 및 고효율 마케팅 기획 시작")

if start_btn:
    api_key = st.session_state.api_key
    if not api_key:
        st.error("오류: 사이드바에서 Gemini API 키를 먼저 설정하고 저장해 주세요.")
    else:
        with st.spinner("실시간 트렌드를 분석하고 기획안을 수립 중입니다..."):
            # 1. 크롤링 진행
            trend_data = fetch_realtime_data(keyword)
            # 2. 기획안 작성 요청
            plan = generate_marketing_plan(api_key, keyword, platform, trend_data)
            
            if plan:
                st.session_state.marketing_plan = plan
                st.session_state.current_keyword = keyword
                st.session_state.current_platform = platform
                st.success("🎉 실시간 마케팅 기획서 작성이 완료되었습니다!")

# -----------------------------------------------------------------------------
# 8. 분석 결과 렌더링 영역 (고급스럽고 깔끔한 레이아웃 제공)
# -----------------------------------------------------------------------------
if "marketing_plan" in st.session_state:
    plan = st.session_state.marketing_plan
    keyword_val = st.session_state.current_keyword
    platform_val = st.session_state.current_platform
    
    # 1. 타겟 및 연관 고효율 키워드
    st.markdown("<div class='section-title'>🎯 타겟 및 연관 고효율 키워드</div>", unsafe_allow_html=True)
    keywords_html = "".join([f"<div class='keyword-badge'>#{kw}</div>" for kw in plan.get("target_keywords", [])])
    st.markdown(f"<div class='keyword-container'>{keywords_html}</div>", unsafe_allow_html=True)
    
    # 2. 헤드라인 제안
    st.markdown("<div class='section-title'>🔥 고클릭 감성 헤드라인 제안 (5종)</div>", unsafe_allow_html=True)
    for i, title in enumerate(plan.get("hooking_titles", []), 1):
        st.markdown(f"<div class='headline-item'>{i}. {title}</div>", unsafe_allow_html=True)
        
    # 3. 작성 아웃라인
    st.markdown("<div class='section-title'>📝 본문 구성 아웃라인 단계별 가이드</div>", unsafe_allow_html=True)
    outline = plan.get("outline", {})
    st.markdown(f"<div class='outline-step'><b>1단계 (도입부):</b> {outline.get('step1', '')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='outline-step'><b>2단계 (문제제시):</b> {outline.get('step2', '')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='outline-step'><b>3단계 (해결책 제시):</b> {outline.get('step3', '')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='outline-step'><b>4단계 (마무리 및 CTA):</b> {outline.get('step4', '')}</div>", unsafe_allow_html=True)
    
    # 4. 이미지 생성 프롬프트 영역 (줄바꿈 자동 처리 및 세련된 네모-네모 복사 아이콘 배치)
    st.markdown("<div class='section-title'>🖼️ AI 이미지 생성 전용 프롬프트 (English)</div>", unsafe_allow_html=True)
    img_prompt = plan.get("image_prompt", "")
    
    # 프롬프트 출력
    st.markdown(f"<div class='prompt-text' id='prompt-area'>{img_prompt}</div>", unsafe_allow_html=True)
    
    # 📋 네모 두개가 겹친 대중적인 클립보드 복사 아이콘 구현
    # Streamlit 기본 copy 기능을 우회해 브라우저 클립보드에 즉시 복사하는 컴팩트한 복사 아이콘 버튼 추가
    copy_html_code = f"""
    <button class="copy-btn" onclick="navigator.clipboard.writeText(`{img_prompt.replace('`','\\`')}`); alert('📋 프롬프트가 클립보드에 복사되었습니다!');">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span>복사하기</span>
    </button>
    """
    st.markdown(copy_html_code, unsafe_allow_html=True)
    
    # 5. 파일 자동 저장 및 단순 내보내기 다운로드 버튼만 제공 (구구절절 설명 제거)
    st.markdown("<div class='section-title'>💾 마케팅 기획서 최종 다운로드</div>", unsafe_allow_html=True)
    
    # 동적 파일명 정의 (예: 2026-08-02_바이브코딩.json)
    date_str = datetime.now().strftime("%Y-%m-%d")
    clean_keyword = "".join([c for c in keyword_val if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    filename = f"{date_str}_{clean_keyword}.json"
    
    # 플랫폼별 로컬 폴더 경로 자동 지정 및 저장
    target_subfolder = BLOG_DIR if platform_val == "네이버 블로그" else INSTA_DIR
    full_local_path = os.path.join(target_subfolder, filename)
    
    # JSON 파일 가공 및 로컬 자동 디렉토리 저장
    json_data = json.dumps(plan, ensure_ascii=False, indent=2)
    try:
        with open(full_local_path, "w", encoding="utf-8") as f:
            f.write(json_data)
        st.success(f"로컬 저장 완료: {full_local_path}")
    except Exception as e:
        st.warning(f"로컬 파일 자동 저장에 어려움이 발생했습니다: {e}")
        
    # 복잡한 가이드 없이, 최종 다운로드 버튼 딱 1개만 배치
    st.download_button(
        label="📥 기획서 JSON 파일 다운로드",
        data=json_data,
        file_name=filename,
        mime="application/json"
    )
