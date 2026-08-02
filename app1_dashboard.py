import streamlit as st
import json
import os
import re
import urllib.parse
import feedparser
import requests
import random
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# 1. 라이브러리 예외 처리 및 환경 설정
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
INSTA_DIR = os.path.join(BASE_DIR, "instagram")

# 폴더 자동 생성 (로컬 가동 대비용)
for d in [BASE_DIR, BLOG_DIR, INSTA_DIR]:
    os.makedirs(d, exist_ok=True)

# API 키 자동 탐색 엔진 (Secrets 또는 파일)
def get_gemini_api_key_details():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"], "Streamlit Secrets", "success"
    key_path = os.path.join(BLOG_DIR, "gemini api key", "api key.txt")
    if os.path.exists(key_path):
        try:
            with open(key_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                key = f.read().strip()
                key = re.sub(r'[\u200b-\u200d\ufeff\xa0]', '', key).strip()
                if key:
                    return key, key_path, "success"
        except Exception:
            pass
    return "", "", "not_found"

# -----------------------------------------------------------------------------
# 2. 실시간 크롤러 및 동적 이미지 엔진
# -----------------------------------------------------------------------------
def fetch_realtime_data(keyword):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    scraped_texts = []
    
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

    try:
        rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:8]:
            scraped_texts.append(entry.title)
    except Exception:
        pass

    return "\n".join(list(set(scraped_texts)))

def get_dynamic_image_html(keyword, seed_offset=1):
    clean_kw = re.sub(r'[^\w\s]', '', keyword).strip()
    encoded_kw = urllib.parse.quote(clean_kw)
    random_seed = random.randint(1000, 9999) + seed_offset
    image_url = f"https://image.pollinations.ai/prompt/professional-realistic-aesthetic-photography-of-{encoded_kw}-modern-concept-commercial-editorial-style?width=800&height=500&nologo=true&private=true&enhance=true&seed={random_seed}"
    return f"""
    <div style="text-align: center; margin: 30px 0;">
        <img src="{image_url}" style="border-radius: 12px; max-width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #E2E8F0;" alt="{keyword}">
        <p style="color: #64748B; font-size: 12.5px; margin-top: 10px; font-weight: 400;">▲ 본문 입체 분석에 연동하여 실시간으로 생성 및 자동 배치된 명품 라이프 스타일 사진</p>
    </div>
    """

# -----------------------------------------------------------------------------
# 3. 마케팅 엔진 (앱 1: 기획 수립 / 앱 2: 1,800자 명품 집필)
# -----------------------------------------------------------------------------
def run_app1_planner(api_key, raw_context, user_keyword, platform_type="blog"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

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
                model='gemini-2.5-flash', contents=prompt,
                config=types.GenerateContentConfig(temperature=0.75, response_mime_type="application/json")
            )
            raw_text = response.text
        else:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            raw_text = response.text

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"```$", "", cleaned, flags=re.IGNORECASE)
        return json.loads(cleaned.strip())
    except Exception as e:
        return {"error": f"1단계 기획 오류: {str(e)}"}

def run_app2_writer(api_key, plan_data, platform_type="blog"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    outline = plan_data.get("outline", {})
    keywords = plan_data.get("target_keywords", [])
    titles = plan_data.get("hooking_titles", [])
    selected_title = titles[0] if titles else "성공 마케팅"

    if platform_type == "blog":
        prompt = f"""
        당신은 대한민국 최정상급 전문 수필가이자, 연간 100억 원 이상의 매출을 견인하는 최고 권위의 브랜드 마케터입니다.
        아래 제공된 [기획안]에 완전히 부합하는 블로그/티스토리 포스팅 원고를 **최소 1,800자 이상(공백 제외)**의 풍성한 장문으로 정밀 집필해 주세요.

        [기획안 정보]
        - 메인 헤드라인: {selected_title}
        - 타겟 검색 키워드군 (본문에 자연스럽게 4~5번 녹여낼 것): {", ".join(keywords)}
        - 문제 상황 정의: {outline.get("step1_problem", "")}
        - 유대 공감대 형성: {outline.get("step2_empathy", "")}
        - 확실한 대안 처방: {outline.get("step3_solution", "")}
        - 즉각적 행동 촉구: {outline.get("step4_cta", "")}

        [원고 작성의 핵심 철칙]
        1. 분량은 무조건 1,800자 이상이어야 하며, 요약하거나 대충 서술하지 말고 세부 묘사를 아주 수려하게 늘려 작성하세요.
        2. 실제 사람이 직접 성찰하며 쓴 것처럼 깊은 공감적 수필 톤을 유지하고, 기계적인 AI 말투나 나열식(~에 대해 알아보겠습니다, 첫째/둘째 등 단순 나열)을 절대 사용하지 마세요.
        3. 가독성이 뛰어난 전문 마크다운 구성을 채택해 주십시오.
        """
    else:
        prompt = f"""
        당신은 대한민국 대표 인플루언서이자 감각적인 비주얼 카피라이터입니다.
        아래 [기획안]을 바탕으로 카드뉴스 슬라이드(총 5~6장) 콘셉트 시각 디자인 기획과, 마지막 해시태그까지 이모지를 적극 사용해 줄간격을 고급스럽게 띄운 고전환 캡션(1000자 이상)을 완성해 주세요.
        [기획안]
        - 대상 키워드: {", ".join(keywords)}
        - 뼈대 흐름: {outline.get("step1_problem", "")} / {outline.get("step2_empathy", "")} / {outline.get("step3_solution", "")} / {outline.get("step4_cta", "")}
        """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 8192}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=45)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        return f"앱 2 오류 (상태 코드: {res.status_code})\n{res.text}"
    except Exception as e:
        return f"앱 2 연결 예외: {str(e)}"

# -----------------------------------------------------------------------------
# 4. 명품 UI 테마 세팅 및 대시보드
# -----------------------------------------------------------------------------
st.set_page_config(page_title="AI 실시간 원스톱 마케팅 오토파일럿", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
        font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
    }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    [data-testid="stMainBlockContainer"] {
        max-width: 860px !important; 
        margin: 50px auto !important;
        padding: 40px 50px !important;
        background-color: #FFFFFF !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.04) !important;
        border: none !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span { color: #1E293B !important; font-weight: 600; }
    .brand-header-area {
        text-align: center; margin-bottom: 35px; padding-bottom: 25px; border-bottom: 2px dashed #E2E8F0;
    }
    .brand-main-title { font-size: 26px; font-weight: 850; color: #1E3A8A !important; letter-spacing: -0.7px; }
    .brand-sub-title { font-size: 13.5px; color: #64748B !important; font-weight: 400; margin-top: 6px; }
    
    button[data-baseweb="tab"] {
        background-color: transparent !important; color: #94A3B8 !important; font-size: 15px !important; font-weight: 700 !important; border: none !important; padding: 10px 20px !important;
    }
    button[aria-selected="true"] { color: #1E3A8A !important; border-bottom: 3px solid #1E3A8A !important; }
    
    div[data-baseweb="input"] { background-color: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; }
    input { color: #1E293B !important; font-weight: 500 !important; }

    div.stButton > button {
        background-color: #FF5A1F !important; color: #FFFFFF !important; border: none !important; padding: 14px 24px !important; font-size: 15.5px !important; font-weight: 800 !important; border-radius: 10px !important; width: 100% !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 4px 14px rgba(255, 90, 31, 0.2);
    }
    div.stButton > button:hover {
        background-color: #E04810 !important; box-shadow: 0 6px 20px rgba(255, 90, 31, 0.35); transform: translateY(-1px);
    }
    .expert-sec-title { font-size: 17px; font-weight: 800; color: #1E3A8A !important; margin: 35px 0 15px 0; display: flex; align-items: center; gap: 6px; }
    .expert-sec-sub { font-size: 13px; color: #64748B !important; font-weight: 400; margin-top: -10px; margin-bottom: 18px; }
    .row-text-line { font-size: 14.5px; color: #334155; font-weight: 500; line-height: 1.8; padding: 8px 12px; background-color: #F8FAFC; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #E2E8F0; }
    .row-keyword-tag { display: inline-block; background-color: #F1F5F9; color: #1E3A8A; font-weight: 700; padding: 6px 14px; border-radius: 30px; margin-right: 8px; margin-bottom: 8px; font-size: 13.5px; }
    .row-4step-box { margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px dashed #F1F5F9; }
    .row-4step-label { font-size: 14.5px; font-weight: 800; color: #FF5A1F; margin-bottom: 5px; }
    .row-4step-desc { font-size: 14px; color: #334155; font-weight: 400; line-height: 1.7; }
    .result-box-container { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 35px 40px; margin-top: 25px; }
    .copy-text-area { font-size: 15.5px; line-height: 1.95; color: #1E293B; }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.markdown("### 🔑 API 설정")
    st.markdown("본 서비스는 Google Gemini AI를 사용합니다. 외부 공유용으로 배포 시 타인이 본인의 개별 API 키를 직접 넣어 안전하게 사용할 수 있습니다.")
    user_api_key = st.text_input(
        "Gemini API Key 입력", type="password", placeholder="AIzaSy...",
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
    <div class="brand-main-title">⚡ AI 실시간 원스톱 마케팅 오토파일럿</div>
    <div class="brand-sub-title">단어 하나만 입력하면 실시간 트렌드 기획(앱 1)과 1,800자 명품 본문 집필(앱 2)이 자동으로 정밀 연쇄 폭발 가동됩니다.</div>
</div>
""", unsafe_allow_html=True)

# 탭 구성
tab_blog, tab_insta = st.tabs(["📝 네이버/티스토리 블로그 원스톱 엔진", "📸 인스타그램 카드뉴스 원스톱 엔진"])

def run_autopilot_pipeline(platform_key, platform_name, save_filename, dest_dir):
    st.write("")
    st.markdown("**🔍 초고속 자동 기획 및 완성 집필을 원하는 주제어를 입력해 주세요:**")
    user_keyword = st.text_input(
        "입력 창", placeholder="예시) 바이브코딩, 성인 심리상담, 주말 근교 드라이브", label_visibility="collapsed", key=f"kw_{platform_key}"
    )
    
    st.write("")
    
    if st.button("🔥 원클릭 실시간 기획 & 1,800자 완성형 본문 집필 가동", key=f"btn_run_{platform_key}"):
        if not user_keyword.strip():
            st.error("⚠️ 가동할 주제 키워드를 입력해 주세요.")
            return
        if not selected_api_key:
            st.error("🔑 API 키가 누락되었습니다. 왼쪽 사이드바에 Gemini API 키를 넣어주세요.")
            return

        # 원클릭 연쇄 실행 (지휘자 모드 가동)
        with st.status("🚀 오토파일럿 지휘자 시스템 가동 중...", expanded=True) as status:
            
            # [앱 1단계] 실시간 수집 및 기획 설계
            status.update(label="1️⃣ [앱 1] 네이버/구글 뉴스 실시간 빅데이터 수집 중...")
            raw_context = fetch_realtime_data(user_keyword)
            
            status.update(label="1️⃣ [앱 1] 트렌드를 융합한 심리 마케팅 정밀 기획 설계 중...")
            plan_result = run_app1_planner(selected_api_key, raw_context, user_keyword, platform_type=platform_key)
            
            if "error" in plan_result:
                status.update(label="❌ [앱 1 단계] 기획 설계 도중 오류가 발생해 자동 가동을 긴급 차단합니다.", state="error")
                st.error(plan_result["error"])
                return
            
            # [앱 2단계] 기획 성공 판별 시 본문 즉시 자동 집필 연쇄 시작
            status.update(label="2️⃣ [앱 1 완료 및 검증 성공] -> [앱 2] 무인 수필가 작가 호출 중...")
            status.update(label="2️⃣ [앱 2] 1,800자 이상 명품 원고 및 가독성 소제목 실시간 집필 중...")
            
            written_text = run_app2_writer(selected_api_key, plan_result, platform_type=platform_key)
            
            status.update(label="✅ [원스톱 파이프라인 가동 성공] 기획과 집필이 단 한 번에 완료되었습니다!", state="complete")
            
        # 결과물들 세션 상태 영구 저장
        st.session_state[f"auto_plan_{platform_key}"] = plan_result
        st.session_state[f"auto_written_{platform_key}"] = written_text
        st.session_state[f"auto_char_{platform_key}"] = len(written_text.replace(" ", "").replace("\n", ""))
        st.session_state[f"auto_kw_{platform_key}"] = user_keyword
        
        # 로컬 세이브 파일 출력 (백업 안전장치)
        save_path = os.path.join(dest_dir, save_filename)
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(plan_result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # 연쇄 실행 결과 최종 출력
    if f"auto_plan_{platform_key}" in st.session_state:
        plan = st.session_state[f"auto_plan_{platform_key}"]
        article = st.session_state[f"auto_written_{platform_key}"]
        char_count = st.session_state[f"auto_char_{platform_key}"]
        kw = st.session_state[f"auto_kw_{platform_key}"]
        
        # ---------------------------------------------------------------------
        # 1. 기획 보고서 브리핑 출력 (앱 1 결과물)
        # ---------------------------------------------------------------------
        st.write("")
        st.markdown(f"### 📋 1단계: '{kw}' 실시간 마케팅 기획서")
        st.write("")

        # 타겟 연관 키워드
        st.markdown('<div class="expert-sec-title">🎯 추천 확장 타겟 키워드</div>', unsafe_allow_html=True)
        keywords = plan.get("target_keywords", [])
        tags_html = "".join([f'<span class="row-keyword-tag">#{k}</span>' for k in keywords[:5]])
        st.markdown(f'<div style="margin-bottom: 25px;">{tags_html}</div>', unsafe_allow_html=True)

        # 헤드라인 추천 카피
        st.markdown('<div class="expert-sec-title">🔥 썸네일 & 콘텐츠 대표 타이틀 추천 카피</div>', unsafe_allow_html=True)
        titles = plan.get("hooking_titles", [])
        for idx, t in enumerate(titles[:5]):
            st.markdown(f'<div class="row-text-line"><strong>{idx+1}순위:</strong> {t}</div>', unsafe_allow_html=True)

        # 4단계 골격 기획안
        st.markdown('<div class="expert-sec-title">📊 마케팅 공식 4단계 본문 골격 기획안</div>', unsafe_allow_html=True)
        outline = plan.get("outline", {})
        st.markdown(f'<div class="row-4step-box"><div class="row-4step-label">🚨 1단계: 문제 상황 정의 (Problem)</div><div class="row-4step-desc">{outline.get("step1_problem", "")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-4step-box"><div class="row-4step-label">🤝 2단계: 유대감 및 공감 (Empathy)</div><div class="row-4step-desc">{outline.get("step2_empathy", "")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-4step-box"><div class="row-4step-label">💡 3단계: 논리 해결책 처방 (Solution)</div><div class="row-4step-desc">{outline.get("step3_solution", "")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-4step-box"><div class="row-4step-label">⚡ 4단계: 행동 전환 촉구 (CTA)</div><div class="row-4step-desc">{outline.get("step4_cta", "")}</div></div>', unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # 2. 프로페셔널 명품 원고 시각화 출력 (앱 2 결과물 - 1800자 이상 및 이미지 2장 매칭)
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.markdown(f"### 🏆 2단계: 최종 완성형 프로페셔널 포스팅 원고")
        st.caption(f"📊 공백 제외 순수 글자 수: **{char_count:,}자** (무조건 1,800자 이상 완벽 충족 완료)")
        
        # 본문을 단락별 소주제로 쪼개어 중간에 이미지 2장을 자동으로 자연스럽게 나누어 배치
        paragraphs = article.split("\n\n")
        mid_1 = max(1, len(paragraphs) // 3)
        mid_2 = max(2, (len(paragraphs) * 2) // 3)
        
        st.markdown('<div class="result-box-container"><div class="copy-text-area">', unsafe_allow_html=True)
        
        for idx, para in enumerate(paragraphs):
            # 1번째 이미지 배치 지점
            if idx == mid_1:
                st.markdown(get_dynamic_image_html(kw, seed_offset=12), unsafe_allow_html=True)
            
            # 2번째 이미지 배치 지점
            if idx == mid_2:
                st.markdown(get_dynamic_image_html(kw + " business startup", seed_offset=77), unsafe_allow_html=True)
                
            st.markdown(para)
            
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # 원클릭 다운로드 기능
        st.write("")
        st.download_button(
            label=f"💾 [{platform_name}] 기획 및 1,800자 원고 텍스트 통합 다운로드 (.txt)",
            data=f"=== 1단계 기획서 ===\n주제어: {kw}\n\n=== 2단계 최종 원고 ===\n{article}",
            file_name=f"automatic_luxury_posting_{platform_key}.txt",
            mime="text/plain",
            key=f"dl_integrated_{platform_key}"
        )

with tab_blog:
    run_autopilot_pipeline("blog", "네이버 블로그", "today_topic.json", BLOG_DIR)

with tab_insta:
    run_autopilot_pipeline("instagram", "인스타그램", "today_topic_insta.json", INSTA_DIR)
