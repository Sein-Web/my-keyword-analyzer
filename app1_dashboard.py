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
# 4. Gemini 2.5 Flash API 활용 마케팅 기획서 생성 (독창적 A-C-R-S-A 프레임워크 적용)
# -----------------------------------------------------------------------------
def generate_marketing_plan(api_key, keyword, platform, trend_context):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    system_instruction = (
        "You are an expert digital marketing strategist. Analyze the provided real-time search and news trend data, "
        "then generate a highly detailed and cohesive marketing plan. "
        "All output text inside the JSON must be written in fluent, professional, and highly persuasive Korean."
    )
    
    if platform == "네이버 블로그":
        prompt = f"""
[Target Keyword]
{keyword}

[Selected Platform]
네이버 블로그 (검색 목적형 상세 정보 탐색)

[Real-time Trend Context Data]
{trend_context}

[Instructions]
네이버 블로그 노출에 최적화된 마케팅 기획서를 생성하세요. 
2단계 글쓰기 앱에서 공백 제외 최소 1,800자 이상의 신뢰도 높고 풍부한 서술형 본문이 완벽히 도출될 수 있도록 구체적인 논리와 지침을 담아야 합니다.
'A-C-R-S-A' (Attract-Claim-Reason-Story-Action) 설득 프레임워크에 맞추어 기획서를 완성하세요.

You must output ONLY a valid JSON object. Do not include markdown code block formatting (like ```json ... ```).
The JSON object must strictly match this structure:
{{
  "target_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "hooking_titles": [
    "블로그 제목 옵션 1",
    "블로그 제목 옵션 2",
    "블로그 제목 옵션 3",
    "블로그 제목 옵션 4",
    "블로그 제목 옵션 5"
  ],
  "outline": {{
    "attract": "시선 집중(Attract): 검색 유저의 유입을 유도하는 오프닝 설계 및 문제의식 유발 기획안",
    "claim": "핵심 주장(Claim): 분석 흐름을 토대로 {keyword} 개념이 어떻게 명쾌한 해답이 되는지 던지는 강력한 한 문장",
    "reason": "명확한 근거(Reason): 소비자가 신뢰할 수밖에 없도록 증명하는 논리적이고 객관적인 마케팅 근거",
    "story": "공감 사례(Story): 감성을 자극하고 확신을 줄 생생한 사례, 비유 혹은 경험적 일화 구성안",
    "action": "행동 제안(Action): 망설임 없이 상담, 구매, 문의 등으로 연결시키는 최종 제안 설계"
  }}
}}
"""
    else:  # 인스타그램 / 스레드 선택 시
        prompt = f"""
[Target Keyword]
{keyword}

[Selected Platform]
인스타그램 & 스레드 (캐러셀 카드뉴스 형태 및 감성 소통형 피드)

[Real-time Trend Context Data]
{trend_context}

[Instructions]
인스타그램 피드 및 스레드 연계 업로드에 최적화된 마케팅 기획서를 생성하세요.
스마트폰 화면을 넘겨보는 '5~7장 캐러셀 카드뉴스' 문법에 완벽히 맞추어 각 슬라이드(장)별 배치 내용과 텍스트 아웃라인을 설계해야 합니다.
트렌디하고 감각적인 언어를 사용하며, 2단계 글쓰기 앱에서 카드뉴스 각 페이지 디자인 텍스트 및 스레드 타래 글이 온전하게 생성되도록 구성안을 제공하세요.

You must output ONLY a valid JSON object. Do not include markdown code block formatting (like ```json ... ```).
The JSON object must strictly match this structure:
{{
  "target_keywords": ["인스타해시태그1", "인스타해시태그2", "인스타해시태그3", "인스타해시태그4", "인스타해시태그5"],
  "hooking_titles": [
    "피드 첫 장 표지 카피 1 (초강력 훅)",
    "피드 첫 장 표지 카피 2 (호기심 유발)",
    "피드 첫 장 표지 카피 3 (공감 자극)",
    "피드 첫 장 표지 카피 4 (반전 대사)",
    "피드 첫 장 표지 카피 5 (솔루션 예고)"
  ],
  "outline": {{
    "slide_1_cover": "1장(표지): 스크롤을 무조건 멈추게 할 극강의 메인 카피와 비주얼 무드 설계",
    "slide_2_problem": "2장(도입/문제제기) 독자가 무조건 공감할 만한 일상의 깊은 페인포인트(Pain Point) 표현안",
    "slide_3_solution": "3장(핵심주장/해결책) {keyword} 개념을 적용하여 얻을 수 있는 결정적인 변화와 명쾌한 해결 제시",
    "slide_4_reason": "4장(이유/원리) '왜 이 방법이어야 하는지' 아주 쉽고 감각적으로 축약해 풀어낸 핵심 근거",
    "slide_5_story_or_benefit": "5장(사례/체험) 감성에 와닿는 짤막한 성공 사례, 비유 또는 직관적인 비포앤애프터 구성",
    "slide_6_action": "6장(행동제안/CTA) '댓글 남겨주시면 발송', '프로필 링크 클릭' 등 손쉬운 동참을 제안하는 쐐기 슬라이드",
    "slide_7_closing": "7장(마무리/엔딩) 브랜드 정체성을 남기고 여운을 주는 마침 카드 및 아웃트로 구성",
    "threads_vibe": "스레드 및 피드 본문 구성안: 캐러셀 하단에 들어갈 편안하고 쿨한 독백체 형태의 스레드 연동 텍스트 전개 방향"
  }}
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
            "temperature": 0.75
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_text.strip())
        else:
            st.error(f"Gemini API 호출 실패 (코드 {response.status_code}): {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("⏳ 구글 인공지능 서버의 응답 시간이 초과되었습니다. 현재 서버 트래픽이 일시적으로 혼잡하오니 잠시 후 다시 시도해 주세요.")
        return None
    except Exception as e:
        st.error(f"기획서 생성 중 예외 발생: {e}")
        return None

# -----------------------------------------------------------------------------
# 5. UI 및 스타일 정의
# -----------------------------------------------------------------------------
st.set_page_config(page_title="실시간 트렌드 마케팅 기획기", layout="centered")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FAF9F6 !important;
        font-family: 'Pretendard', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    
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

    .report-block, .download-card, .prompt-box {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

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
        white-space: nowrap;
    }

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
        margin-bottom: 15px;
        padding-left: 10px;
    }
    .framework-badge {
        background-color: #FFEDE6;
        color: #FF5A1F;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 13px;
        margin-right: 8px;
    }

    .header-area {
        margin-bottom: 60px !important;
    }
</style>

<script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'c' || e.key === 'C') {
            e.stopPropagation();
        }
    }, true);
</script>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 사이드바 UI
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔑 API 키 설정")
    st.markdown("본 프로그램을 사용하려면 Gemini API 키가 필요합니다.")
    
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
# 7. 메인 화면 UI
# -----------------------------------------------------------------------------
st.write("")
st.markdown("""
<div class="header-area">
    <h1 style='text-align: center; color: #0F172A; font-size: 32px; font-weight: 800; margin-bottom: 12px;'>📈 1단계: 실시간 트렌드 마케팅 기획기</h1>
    <p style='text-align: center; color: #64748B; font-size: 15px; margin-bottom: 0;'>실시간 트렌드에 최적의 플랫폼별 마케팅 문법을 융합합니다.</p>
</div>
""", unsafe_allow_html=True)

# 입력 폼 컬럼 구성
col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input("✍️ 기획할 주제 또는 핵심 키워드를 입력하세요.", value="", placeholder="예: 바이브코딩, 여름 침구 세트")
with col2:
    platform = st.selectbox("플랫폼 선택", ["네이버 블로그", "인스타그램"])

start_btn = st.button("🚀 실시간 시장 분석 및 고효율 마케팅 기획 시작")

if start_btn:
    if not keyword.strip():
        st.error("오류: 분석 및 기획을 원하시는 키워드 혹은 주제를 입력해 주세요.")
    else:
        api_key = st.session_state.api_key
        if not api_key:
            st.error("오류: 사이드바에서 Gemini API 키를 먼저 설정하고 저장해 주세요.")
        else:
            with st.spinner("실시간 트렌드를 분석하고 기획안을 수립 중입니다..."):
                trend_data = fetch_realtime_data(keyword)
                plan = generate_marketing_plan(api_key, keyword, platform, trend_data)
                
                if plan:
                    st.session_state.marketing_plan = plan
                    st.session_state.current_keyword = keyword
                    st.session_state.current_platform = platform
                    st.success("🎉 실시간 마케팅 기획서 작성이 완료되었습니다!")

# -----------------------------------------------------------------------------
# 8. 분석 결과 렌더링 영역 및 이원화 로컬 자동 저장
# -----------------------------------------------------------------------------
if "marketing_plan" in st.session_state:
    plan = st.session_state.marketing_plan
    keyword_val = st.session_state.current_keyword
    platform_val = st.session_state.current_platform
    
    # 1. 타겟 및 연관 고효율 키워드 (해시태그)
    st.markdown(f"<div class='section-title'>🎯 타겟 및 연관 고효율 {'해시태그' if platform_val == '인스타그램' else '키워드'}</div>", unsafe_allow_html=True)
    keywords_html = "".join([f"<div class='keyword-badge'>#{kw}</div>" for kw in plan.get("target_keywords", [])])
    st.markdown(f"<div class='keyword-container'>{keywords_html}</div>", unsafe_allow_html=True)
    
    # 2. 헤드라인 제안
    headline_title_text = "🔥 첫 장 표지 카피 제안 (5종)" if platform_val == "인스타그램" else "🔥 고클릭 감성 헤드라인 제안 (5종)"
    st.markdown(f"<div class='section-title'>{headline_title_text}</div>", unsafe_allow_html=True)
    for i, title in enumerate(plan.get("hooking_titles", []), 1):
        st.markdown(f"<div class='headline-item'>{i}. {title}</div>", unsafe_allow_html=True)
        
    # 3. 작성 아웃라인 분기 처리
    outline = plan.get("outline", {})
    
    if platform_val == "네이버 블로그":
        st.markdown("<div class='section-title'>📝 블로그 작성 뼈대 구조 (A-C-R-S-A)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Attract (시선집중)</span> {outline.get('attract', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Claim (핵심주장)</span> {outline.get('claim', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Reason (명확근거)</span> {outline.get('reason', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Story (공감사례)</span> {outline.get('story', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Action (행동제안)</span> {outline.get('action', '')}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='section-title'>📸 인스타그램 캐러셀(카드뉴스) 및 스레드 기획 구조</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Slide 1 (표지)</span> {outline.get('slide_1_cover', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Slide 2 (공감)</span> {outline.get('slide_2_problem', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Slide 3 (해결)</span> {outline.get('slide_3_solution', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Slide 4 (원리)</span> {outline.get('slide_4_reason', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Slide 5 (체험)</span> {outline.get('slide_5_story_or_benefit', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Slide 6 (제안)</span> {outline.get('slide_6_action', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>Slide 7 (엔딩)</span> {outline.get('slide_7_closing', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='outline-step'><span class='framework-badge'>본문 피드/스레드</span> {outline.get('threads_vibe', '')}</div>", unsafe_allow_html=True)
        
    # 4. 파일 자동 저장 및 단순 내보내기 다운로드
    st.markdown("<div class='section-title'>💾 마케팅 기획서 최종 다운로드</div>", unsafe_allow_html=True)
    
    # 💡 [핵심 보완]: 파일명 뒤에 플랫폼 정보를 명확히 명시하여 중복 저장 방지 및 자동화 연결 지원
    date_str = datetime.now().strftime("%Y-%m-%d")
    clean_keyword = "".join([c for c in keyword_val if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    
    if platform_val == "네이버 블로그":
        filename = f"{date_str}_{clean_keyword}_blog.json"
        target_subfolder = BLOG_DIR
    else:
        filename = f"{date_str}_{clean_keyword}_insta.json"
        target_subfolder = INSTA_DIR
        
    full_local_path = os.path.join(target_subfolder, filename)
    
    json_data = json.dumps(plan, ensure_ascii=False, indent=2)
    try:
        with open(full_local_path, "w", encoding="utf-8") as f:
            f.write(json_data)
        st.success(f"로컬 저장 완료: {full_local_path}")
    except Exception as e:
        st.warning(f"로컬 파일 자동 저장 중 오류 발생: {e}")
        
    st.download_button(
        label="📥 기획서 JSON 파일 다운로드",
        data=json_data,
        file_name=filename,
        mime="application/json"
    )
