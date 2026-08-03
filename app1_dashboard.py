cat << 'EOF' > app2_writer.py
import os, json, glob, io, re
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

BASE_DIR = os.path.expanduser("~/Documents/Marketing/today_topic")
BLOG_DIR = os.path.join(BASE_DIR, "blog")
INSTA_DIR = os.path.join(BASE_DIR, "instagram")
API_KEY_PATH = os.path.expanduser("~/Documents/Marketing/gemini_api_key.txt")
BGM_DIR = os.path.join(BASE_DIR, "BGM")
MORNING_WAV = os.path.join(BGM_DIR, "Morning Light.wav")
EVENING_WAV = os.path.join(BGM_DIR, "Midnight Vinyl.wav")

os.makedirs(BLOG_DIR, exist_ok=True)
os.makedirs(INSTA_DIR, exist_ok=True)
os.makedirs(BGM_DIR, exist_ok=True)

st.set_page_config(page_title="고효율 마케팅 자동화 - 2단계: 독립형 본문 집필기", layout="wide")

# CSS Styling (레이아웃 가독성 극대화 및 미색 톤 유지)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FAF9F6 !important;
        font-family: 'Noto Sans KR', sans-serif;
        color: #333333;
    }
    .stButton>button {
        background-color: #FF5A1F !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #E04E1A !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 90, 31, 0.3);
    }
    .card {
        background: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #FF5A1F;
    }
    .prompt-box {
        background: #F3F1EC;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #E0DCD5;
        font-size: 0.85rem;
        color: #555555;
        word-break: break-all;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

def load_api_key():
    if os.path.exists(API_KEY_PATH):
        try:
            with open(API_KEY_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except: return ""
    return ""

def save_api_key(key):
    try:
        os.makedirs(os.path.dirname(API_KEY_PATH), exist_ok=True)
        with open(API_KEY_PATH, "w", encoding="utf-8") as f:
            f.write(key.strip())
        return True
    except Exception as e:
        st.error(f"API 키 저장 실패: {e}")
        return False

if "api_key" not in st.session_state:
    st.session_state.api_key = load_api_key()

def get_latest_brief(platform):
    target = BLOG_DIR if platform == "네이버 블로그/티스토리" else INSTA_DIR
    files = glob.glob(os.path.join(target, "*.json"))
    if not files: return None, None
    files.sort(key=os.path.getmtime, reverse=True)
    try:
        with open(files[0], "r", encoding="utf-8") as f:
            return os.path.basename(files[0]), json.load(f)
    except:
        return None, None

# 구글 2026 차세대 이미지 생성 엔진 네이티브 기법 적용
def generate_blog_images(client, prompts):
    images = []
    for i, p in enumerate(prompts):
        try:
            # 1순위: 최신 최고 스펙 이미지 모델 gemini-3.1-flash-image 호출
            response = client.models.generate_content(
                model="gemini-3.1-flash-image",
                contents=[p]
            )
            img_found = False
            for part in response.parts:
                if part.inline_data:
                    img = Image.open(io.BytesIO(part.inline_data.data))
                    images.append(img)
                    img_found = True
                    break
            if not img_found:
                images.append(None)
        except Exception as e_31:
            try:
                # 2순위 백업: gemini-2.5-flash-image 호환 호출
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[p]
                )
                img_found = False
                for part in response.parts:
                    if part.inline_data:
                        img = Image.open(io.BytesIO(part.inline_data.data))
                        images.append(img)
                        img_found = True
                        break
                if not img_found:
                    images.append(None)
            except Exception as e_25:
                st.error(f"이미지 {i+1} 생성 에러: {e_25}")
                images.append(None)
    return images

def generate_independent_content(platform, target_title, target_keywords, input_mode, brief_data=None, music_time=None):
    if not st.session_state.api_key:
        st.error("Gemini API 키가 입력되지 않았습니다. 사이드바를 확인해 주세요.")
        return None
    
    client = genai.Client(api_key=st.session_state.api_key)
    model_name = "gemini-2.5-flash"
    
    outline_info = ""
    if input_mode in ["[방식 1] 자동 연동", "[방식 2] 수동 업로드"] and brief_data:
        outline_info = f"1단계 기획 초안 정보: {json.dumps(brief_data.get('outline', {}), ensure_ascii=False)}"
    else:
        outline_info = "독립형 실행 모드. 타겟 키워드와 핵심 주제를 관통하는 설득력 높은 스토리라인을 자율적으로 구성할 것."

    if platform == "네이버 블로그/티스토리":
        prompt = f"""
당신은 대한민국 상위 0.1% 카피라이터이자 마케팅 글쓰기 전문가('글천개')입니다.
전달받은 [제목]과 [키워드]를 분석하여 잠재고객의 구매 심리를 자극하는 1,800자 이상의 초고품질 블로그 원고를 작성해 주세요.

[필수 요구사항]
1. 설득 마케팅 기법(ACRSA 구조)을 완벽하게 녹여낼 것:
   - Attention(주의): 강렬한 질문과 문제 제기로 첫 3초 장악 (기계적인 문구 금지)
   - Crisis(위기감): 문제를 방치했을 때의 손실을 심리학적으로 극대화
   - Reason(이유): 이 문제의 진짜 원인과 확실한 해결의 당위성 증명
   - Story(스토리/증거): 실제 고객의 성공 사례를 극적으로 묘사하여 신뢰 구축
   - Action(행동): 강력하고 구체적인 행동(상담, 신청 등) 유도
2. 인공지능이 쓴 느낌(예: "첫째, 둘째", "결론적으로", "[도입부]", "ACRSA" 등 기계적인 딱지)을 철저히 배제하고 완벽하게 자연스러운 인간의 글로 완성할 것.
3. 본문 흐름에 최적화된 위치에 정확히 3개의 이미지 생성 가이드를 삽입해 주세요. (한곳에 몰아넣지 말 것)
   형식: 반드시 문단 중간에 `[이미지 생성 프롬프트 X: 영어로만 작성된 극사실주의적이고 트렌디한 고화질 프롬프트 내용]` 형태로 정확하게 명시해 주세요. 대괄호 안에 쉼표나 마침표가 들어가도 좋습니다.
   (예: [이미지 생성 프롬프트 1: A professional photography of a modern laptop on a clean desk, warm lighting, 8k resolution, photorealistic])
4. 마지막에는 본문과 가장 연관도가 높고 유입량이 높은 네이버/티스토리용 고효율 해시태그 7~10개를 추가해 주세요.

[정보]
제목: {target_title}
키워드: {target_keywords}
기획 구성안: {outline_info}
        """
    else:
        bgm_guide = f"선택된 발행 시간대 배경음악 안내: {music_time} 에 최적화된 음원 가이드를 마지막에 추천해 주세요." if music_time else ""
        prompt = f"""
당신은 인스타그램 트렌드를 선도하는 탑급 브랜드 마케터입니다.
전달받은 [주제]와 [키워드]를 기반으로, 가독성이 높고 감성적이면서도 정보 전달력이 우수한 '5~7장 분량의 캐러셀(슬라이드) 카드 원고'와 '피드용 롱폼 스레드 글'을 작성해 주세요.

[필수 요구사항]
1. 캐러셀 슬라이드 구성:
   - [1장] 시선을 사로잡는 강력한 훅(Hooking) 타이틀 커버
   - [2장~6장] 핵심 가치 전달 및 설득 흐름 (각 카드마다 이미지 구도 묘사 포함)
   - [7장] 최종 요약 및 팔로우/댓글 참여 유도(CTA) 클로징
2. 피드 업로드용 감성 롱폼 본문(스레드 바이브):
   - 스마트폰 화면에서 스크롤하며 읽기 편하도록 짧은 줄바꿈과 여백을 조절할 것.
   - 감성적이면서도 전문성이 느껴지는 말투 사용.
3. 각 장에 최적화된 이미지 구도를 영문 프롬프트로 설계하여 `[캐러셀_X_이미지: 영어로 작성된 인물/브랜드 지향형 이미지 프롬프트]` 형태로 명시할 것.
4. {bgm_guide}
5. 고효율 인기 해시태그 10~15개 추가.

[정보]
주제: {target_title}
키워드: {target_keywords}
기획 구성안: {outline_info}
        """

    try:
        resp = client.models.generate_content(model=model_name, contents=prompt)
        return resp.text
    except Exception as e:
        st.error(f"원고 생성 중 오류가 발생했습니다: {e}")
        return None

def main():
    st.title("🚀 고효율 마케팅 자동화 - 2단계 본문 집필기")
    
    # 사이드바 API 설정
    api_input = st.sidebar.text_input("Gemini API Key 입력", value=st.session_state.api_key, type="password")
    if st.sidebar.button("API Key 저장 및 적용"):
        if api_input and save_api_key(api_input):
            st.session_state.api_key = api_input
            st.sidebar.success("API Key가 정상 적용되었습니다.")
            
    platform = st.selectbox("집필 채널 선택", ["네이버 블로그/티스토리", "인스타그램 & 스레드"])
    input_way = st.radio("기획안 소스 가져오기", ["[방식 1] 자동 연동", "[방식 2] 수동 업로드", "[방식 3] 독립 실행"])
    
    target_title, target_keywords, brief_data = "", "", None
    
    if input_way == "[방식 1] 자동 연동":
        fn, data = get_latest_brief(platform)
        if fn and data:
            st.info(f"📂 1단계에서 생성된 최신 기획 파일이 자동 연결되었습니다: **{fn}**")
            target_title = data.get("hooking_titles", [""])[0] if data.get("hooking_titles") else data.get("target_keywords", "")
            target_keywords = ", ".join(data.get("target_keywords", [])) if isinstance(data.get("target_keywords"), list) else data.get("target_keywords", "")
            brief_data = data
        else:
            st.warning("자동 로드할 기획안 파일(JSON)을 찾지 못했습니다. 1단계를 먼저 실행해 주세요.")
            
    elif input_way == "[방식 2] 수동 업로드":
        uploaded_file = st.file_uploader("1단계 기획안 JSON 파일을 업로드하세요", type=["json"])
        if uploaded_file:
            data = json.load(uploaded_file)
            st.success("기획안 로드 완료!")
            target_title = data.get("hooking_titles", [""])[0] if data.get("hooking_titles") else data.get("target_keywords", "")
            target_keywords = ", ".join(data.get("target_keywords", [])) if isinstance(data.get("target_keywords"), list) else data.get("target_keywords", "")
            brief_data = data

    else:
        col1, col2 = st.columns(2)
        with col1:
            target_title = st.text_input("원하는 글 주제/제목 입력")
        with col2:
            target_keywords = st.text_input("핵심 타겟 키워드 (쉼표 분리)")

    music_time = None
    if platform == "인스타그램 & 스레드":
        music_time = st.radio("발행 예정 시간 선택 (예약 발행 및 자동 매칭용)", ["오전 11:00 (Morning Light.wav)", "오후 20:30 (Midnight Vinyl.wav)"])

    if st.button("🔥 마케팅 본문 및 비주얼 이미지 기획서 제작 시작"):
        if not target_title or not target_keywords:
            st.warning("글의 주제와 키워드가 명확하지 않습니다. 정보를 올바르게 입력해 주세요.")
        else:
            with st.spinner("최고급 마케팅 심리학 원고를 집필 중입니다..."):
                result = generate_independent_content(platform, target_title, target_keywords, input_way, brief_data, music_time)
                if result:
                    st.session_state.raw_output = result
                    
                    client = genai.Client(api_key=st.session_state.api_key)
                    # 대괄호 내의 긴 문장을 온전하게 파싱하도록 정규식 대폭 강화
                    if platform == "네이버 블로그/티스토리":
                        prompts = re.findall(r"\[이미지 생성 프롬프트 \d+:\s*([^\]]+)\]", result)
                        if not prompts:
                            prompts = ["A professional photography of modern office setup, clean desk, warm lighting, 8k resolution, photorealistic"] * 3
                        st.session_state.img_prompts = prompts[:3]
                        st.session_state.img_list = generate_blog_images(client, prompts[:3])
                    else:
                        prompts = re.findall(r"\[캐러셀_\d+_이미지:\s*([^\]]+)\]", result)
                        if not prompts:
                            prompts = ["An aesthetic Instagram mood visual, warm and professional style, cozy setup"] * 5
                        st.session_state.img_prompts = prompts[:5]
                        st.session_state.img_list = generate_blog_images(client, prompts[:5])
                    st.success("🎉 작성이 완료되었습니다! 아래 에디터에서 완성본을 확인하세요.")

    if "raw_output" in st.session_state:
        st.markdown("### 🖼️ 추천 삽입 이미지 가이드 & 고화질 프롬프트")
        st.write("사용자님의 완벽한 유료 API 계정을 통해 구글 최신 네이티브 그래픽 엔진이 실시간 생성한 고품질 시각 이미지입니다.")
        
        cols = st.columns(len(st.session_state.get("img_prompts", [])))
        for idx, col in enumerate(cols):
            with col:
                st.markdown(f"**이미지 {idx+1} 가이드**")
                img_list = st.session_state.get("img_list", [])
                if idx < len(img_list) and img_list[idx] is not None:
                    st.image(img_list[idx], use_container_width=True)
                    buf = io.BytesIO()
                    img_list[idx].save(buf, format="JPEG")
                    st.download_button(label=f"📥 이미지 {idx+1} 받기", data=buf.getvalue(), file_name=f"image_{idx+1}.jpg", mime="image/jpeg", key=f"dl_btn_{idx}")
                else:
                    st.error("⚠️ 최신 이미지 생성 엔진 호출 지연 또는 일시적 오류")
                
                # 누락 없이 끝까지 보존된 프롬프트 영역
                st.text_area(label=f"완성형 프롬프트 {idx+1}", value=st.session_state["img_prompts"][idx], height=100, key=f"prompt_area_{idx}")

        st.markdown("### 📄 포스팅 전체 원고 에디터 및 소스 복사")
        edited_text = st.text_area("이 텍스트 상자 안을 클릭하고 Ctrl+A 후 복사해가시면 됩니다.", value=st.session_state.raw_output, height=450)
        
        text_no_spaces = len(edited_text.replace(" ", "").replace("\n", ""))
        st.metric(label="실시간 글자 수 (공백 제외)", value=f"{text_no_spaces:,} 자")
        
        if platform == "네이버 블로그/티스토리" and text_no_spaces < 1800:
            st.warning("⚠️ 현재 글자 수가 고효율 상위 노출 기준인 1,800자보다 부족합니다. 조금 더 내용을 살찌우거나 추가 작성을 권장합니다.")
        elif platform == "네이버 블로그/티스토리":
            st.success("✅ 상위 노출에 최적화된 충분한 분량(1,800자 이상)입니다!")

        file_date = datetime.now().strftime("%Y-%m-%d")
        safe_title = re.sub(r'[\\/*?:"<>|]', "", target_title)[:10].strip()
        filename = f"{file_date}_{safe_title}_최종완성원고.txt"
        
        st.download_button(
            label="📥 완벽본 텍스트(.txt) 파일로 내려받기",
            data=edited_text,
            file_name=filename,
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
EOF
