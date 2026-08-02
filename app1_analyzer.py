import json
import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# 1. 파일이 저장될 기본 경로 설정 (맥북 문서 내 Marketing 폴더)
BASE_DIR = os.path.expanduser("~/Documents/Marketing")
BLOG_DIR = os.path.join(BASE_DIR, "blog")
INSTA_DIR = os.path.join(BASE_DIR, "instagram")

# 폴더 자동 생성 확인
os.makedirs(BLOG_DIR, exist_ok=True)
os.makedirs(INSTA_DIR, exist_ok=True)


def get_gemini_api_key(platform="blog"):
    """진단기로 확인한 정확한 폴더 구조에서 제미나이 API 키를 안전하게 가져옵니다."""
    sub_dir = "gemini api key"
    file_name = "api key.txt"
    
    if platform == "blog":
        key_path = os.path.join(BLOG_DIR, sub_dir, file_name)
    else:
        key_path = os.path.join(INSTA_DIR, sub_dir, file_name)
        
    try:
        with open(key_path, "r", encoding="utf-8-sig") as f:
            key = f.read().strip()
            key = key.replace('"', '').replace("'", "").strip()
            key = re.sub(r'[^\x00-\x7F]+', '', key)
            return key
    except FileNotFoundError:
        print(f"❌ 경고: '{key_path}' 경로에서 제미나이 키 파일을 찾을 수 없습니다.")
        return None


def fetch_overseas_trends():
    """안정성이 입증된 해외 테크 매체 공식 RSS 피드로 구성"""
    print("[1/3] 해외 AI 트렌드 수집 중...")
    trends = []
    urls = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:4]:
                summary_clean = re.sub('<[^<]+?>', '', entry.get("summary", ""))[:200]
                trends.append(
                    {
                        "title": entry.title,
                        "link": entry.link,
                        "summary": summary_clean,
                    }
                )
        except Exception as e:
            print(f"해외 매체 수집 우회 통과 ({url}): {e}")
            
    if not trends:
        trends = [
            {"title": "OpenAI releases advanced GPT-5 developments and desktop app updates.", "summary": "New desktop application models and faster API integrations for developers."},
            {"title": "Claude 3.5 Sonnet sets new benchmarks for coding and workflow automation.", "summary": "Anthropic updates models with better logic reasoning and task flow control."}
        ]
    return trends


def fetch_domestic_keywords():
    """네이버 검색결과 분석을 통한 국내 핵심 반응 키워드 수집"""
    print("[2/3] 국내 검색 및 블로그 트렌드 분석 중...")
    domestic_data = []
    target_keywords = ["AI 자동화", "바이브코딩", "노코드 웹사이트", "Claude 업무자동화"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for keyword in target_keywords:
        url = f"https://search.naver.com/search.naver?query={keyword}"
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            related_terms = [
                tag.text for tag in soup.select(".related_srch .tit")[:5]
            ]
            blog_titles = [
                tag.text for tag in soup.select(".api_txt_lines.total_tit")[:3]
            ]
            domestic_data.append(
                {
                    "keyword": keyword,
                    "related_terms": related_terms,
                    "blog_titles": blog_titles,
                }
            )
        except Exception as e:
            print(f"국내 수집 통과 ({keyword}): {e}")
            
    if not domestic_data:
        domestic_data = [{"keyword": "AI 자동화", "related_terms": ["AI 업무효율", "업무자동화 툴"], "blog_titles": ["AI로 하루 1시간 아끼는 방법"]}]
    return domestic_data


def analyze_and_plan(overseas_data, domestic_data, platform="blog"):
    """수집된 데이터를 바탕으로 제미나이 2.5 프로를 이용하여 고품질 마케팅 기획서 작성"""
    print(f"[3/3] Gemini 2.5 Pro 분석 및 고품질 {platform.upper()} 기획서 작성 중...")

    api_key = get_gemini_api_key(platform)
    if not api_key:
        print(f"❌ {platform.upper()}용 Gemini API 키가 없어 분석을 건너뜁니다.")
        return None
        
    # 구글 최신 google-genai 공식 SDK 방식으로 클라이언트 초기화
    client = genai.Client(api_key=api_key)

    if platform == "blog":
        platform_instructions = """
        [블로그 기획 기준]:
        - 'outline'은 '글천개' 마케팅 글쓰기 공식인 [1단계: 강력한 독자 문제 제기] -> [2단계: 깊은 감정적 공감] -> [3단계: 명확하고 쉬운 해결책 제시] -> [4단계: 행동 유도(CTA)]에 맞게 설계하세요.
        - 블로그 독자들이 이탈하지 않고 끝까지 정독할 수 있도록 세밀하고 짜임새 있는 뼈대를 잡아야 합니다.
        """
    else:
        platform_instructions = """
        [인스타그램/스레드 기획 기준]:
        - 캐러셀(Carousel, 카드뉴스) 형식으로 총 5~7장 분량의 텍스트 레이아웃을 기획하세요.
        - 아주 콤팩트하고 강렬한 문장, 한눈에 들어오는 가독성, 그리고 저장/공유를 유도하는 강력한 CTA가 핵심입니다.
        - 'outline'의 각 단계를 카드뉴스 1장~7장의 텍스트로 바로 활용할 수 있도록 짧고 후킹하게 설계하세요.
        """

    prompt = f"""
    당신은 대한민국 최고의 마케팅 전문가이자 카피라이터입니다.
    아래 데이터를 철저히 분석하여 국내 시장에서 무조건 터질 수 있는 '황금 키워드' 1개를 선정하고 기획서를 작성해 주세요.
    {platform_instructions}

    [해외 트렌드 소스]
    {json.dumps(overseas_data, ensure_ascii=False, indent=2)}

    [국내 반응 데이터]
    {json.dumps(domestic_data, ensure_ascii=False, indent=2)}

    요구사항:
    - 반드시 아래의 JSON 형식으로만 완벽하게 답변하세요. 코드 블록(```json ```)을 포함하지 마십시오.
    - 'image_prompt'는 제미나이(Gemini) 이미지 생성 모델에서 사용할 수 있는 사실적이고 직관적인 영문 프롬프트로 작성하세요.

    JSON 출력 포맷:
    {{
        "main_keyword": "선정된 오늘 최고의 타겟 키워드",
        "hooking_titles": [
            "후킹 타이틀 후보 1",
            "후킹 타이틀 후보 2",
            "후킹 타이틀 후보 3"
        ],
        "outline": {{
            "step1_problem": "독자의 가려운 곳을 찌르는 문제 제기 (카드뉴스 1-2장 분량)",
            "step2_empathy": "격하게 공감할 수 있는 현실적인 상황 묘사 (카드뉴스 3장 분량)",
            "step3_solution": "오늘 다룰 AI 자동화 해결책 핵심 제안 (카드뉴스 4-5장 분량)",
            "step4_cta": "추가 정보를 찾거나 팔로우를 유도하는 강력한 문구 (카드뉴스 마지막장 분량)"
        }},
        "image_prompt": "Futuristic high-tech working space, realistic details, high quality illustration."
    }}
    """

    # 제미나이 2.5 프로 전용 호출 세팅
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        response_text = response.text.strip()
        
        response_text = re.sub(r"```json\s*", "", response_text)
        response_text = re.sub(r"\s*```", "", response_text)
        
        return json.loads(response_text)
    except Exception as e:
        print(f"❌ Gemini 2.5 Pro 호출 실패 ({platform}): {e}")
        return {}


if __name__ == "__main__":
    print("=================== [앱 1] 수집 및 분석 시작 ===================")

    # 1. 원천 데이터 수집 (한 번만 실행해서 두 플랫폼에 공유)
    overseas = fetch_overseas_trends()
    domestic = fetch_domestic_keywords()

    # 2. 블로그용 분석 및 파일 저장
    blog_plan = analyze_and_plan(overseas, domestic, platform="blog")
    if blog_plan:
        blog_file = os.path.join(BLOG_DIR, "today_topic.json")
        with open(blog_file, "w", encoding="utf-8") as f:
            json.dump(blog_plan, f, ensure_ascii=False, indent=4)
        print(f"✔ 블로그 기획 완료 -> {blog_file}")

    # 3. 인스타그램용 분석 및 파일 저장
    insta_plan = analyze_and_plan(overseas, domestic, platform="instagram")
    if insta_plan:
        insta_file = os.path.join(INSTA_DIR, "today_topic_insta.json")
        with open(insta_file, "w", encoding="utf-8") as f:
            json.dump(insta_plan, f, ensure_ascii=False, indent=4)
        print(f"✔ 인스타그램 기획 완료 -> {insta_file}")

    print("\n=================== [앱 1] 프로세스 종료 ===================")
