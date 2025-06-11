import os
import time
import re
import csv
import random
import datetime
from io import BytesIO
from difflib import SequenceMatcher

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from PIL import ImageGrab
import pyautogui
import pyperclip
import keyboard
import requests
import pandas as pd
import FinanceDataReader as fdr
from tqdm import tqdm
import google.generativeai as genai

# ⬇️ 환경변수 로딩
load_dotenv()
NAVER_ID = os.getenv("NAVER_ID")
NAVER_PW = os.getenv("NAVER_PW")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# ✅ 주제 이미지 불러오기
def image_url(query):
    url = f"https://api.unsplash.com/search/photos?page={random.randint(1, 3)}&query={query}"
    headers = {'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'}
    response = requests.get(url, headers=headers)
    try:
        return response.json()['results'][0]['urls']['regular']
    except:
        return None

# ✅ 기업명 유사도 비교
def extract_company_name(title, company_list):
    max_similarity = 0.15
    most_similar = None
    for company in company_list:
        similarity = SequenceMatcher(None, title, company).ratio()
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar = company
    return most_similar

# ✅ 기사 중복 제거 및 차트 캡처
def remove_duplicate_articles(news_data, company_list, df_krx):
    seen = set()
    unique_articles = []
    numbering = 0
    codes = []

    for data in news_data:
        title = data[0]
        company = extract_company_name(title, company_list)
        try:
            code = df_krx[df_krx['Name'] == company]['Code'].values[0]
        except:
            continue

        if company and company not in seen:
            seen.add(company)
            unique_articles.append(data)
            codes.append(code)

            url = f"https://finance.naver.com/item/fchart.naver?code={code}"
            driver = webdriver.Chrome()
            driver.maximize_window()
            driver.get(url)
            time.sleep(2)

            pyautogui.moveTo(1913, 1020, duration=1)
            pyautogui.click(clicks=5)
            chart_element = driver.find_element(By.XPATH, '//*[@id="content"]/div[2]/cq-context/div[2]')
            chart_element.screenshot(f"dailychart_{numbering}_final.png")
            driver.quit()

            numbering += 1

    return unique_articles

# ✅ Gemini를 이용한 뉴스 요약
def summarize_articles_with_gemini(articles):
    summaries = []
    for article in tqdm(articles):
        prompt = f"""
다음은 주식 뉴스 기사입니다. 존댓말로 길게 풀이해 주세요:
"{article[2]}"
"""
        response = model.generate_content(prompt)
        summaries.append(response.text.strip())
    return summaries

# ✅ 뉴스 수집
def get_news_data():
    url = "https://search.naver.com/search.naver?where=news&query=%ED%8A%B9%EC%A7%95%EC%A3%BC&pd=1&nso=so:dd,p:1w"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    news_data = []

    for item in soup.find_all('li', class_='bx'):
        title_tag = item.find('a', class_='news_tit')
        if not title_tag: continue
        title = title_tag.get('title')
        href = title_tag.get('href')

        summary_tag = item.find('div', class_='dsc_wrap')
        summary = summary_tag.get_text(strip=True) if summary_tag else ''

        time_tag = item.find('span', class_='info')
        if time_tag and '1일 전' not in time_tag.get_text():
            news_data.append((title, href, summary))
    return news_data

# ✅ 네이버 블로그 자동 로그인 및 포스팅
def post_to_naver_blog(articles, summaries):
    site_url = "https://nid.naver.com/nidlogin.login"
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(site_url)
    time.sleep(5)

    pyperclip.copy(NAVER_ID)
    driver.find_element(By.NAME, 'id').send_keys(Keys.CONTROL, 'v')
    pyperclip.copy(NAVER_PW)
    driver.find_element(By.NAME, 'pw').send_keys(Keys.CONTROL, 'v')
    driver.find_element(By.ID, "log.login").click()
    time.sleep(5)

    # 블로그 접근
    driver.get("https://blog.naver.com")
    time.sleep(5)
    driver.find_element(By.CLASS_NAME, 'btn_check').click()
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="root"]/header/div[2]/button/i').click()
    time.sleep(2)
    driver.find_elements(By.CLASS_NAME, 'icon___T7KP')[4].click()
    time.sleep(5)

    # 글 제목 작성
    now = datetime.datetime.now()
    today = now.strftime("%m/%d")
    title = f"[{today}] 국내 테마주 & 특징주"
    driver.find_element(By.XPATH, '//*[@id="se_component_wrapper"]/div[1]/div/div[3]/div/div/div/div/textarea').send_keys(title)

    # 첫 문단 + 이미지
    pyautogui.moveTo(27, 205); pyautogui.click()
    time.sleep(1)
    pyautogui.moveTo(74, 205); pyautogui.click()
    time.sleep(1)
    pyautogui.moveTo(85, 777); pyautogui.click()
    pyautogui.moveTo(259, 286); pyautogui.doubleClick()
    pyautogui.moveTo(293, 972); pyautogui.click()
    keyboard.write("unsplash_images_theme.jpg")
    pyautogui.press("enter")
    time.sleep(3)

    # 본문 입력
    for i, (article, summary) in enumerate(zip(articles, summaries), 1):
        comment_field = driver.find_element(By.XPATH, f'//*[@id="se_component_wrapper"]/div[{i*3}]/div/div/div/div[2]/div/div/div/div')
        comment_field.send_keys(f"{i}. {article[0]}\n{article[1]}")
        time.sleep(1)

        # 이미지 첨부
        pyautogui.moveTo(27, 150); pyautogui.click()
        pyautogui.moveTo(74, 150); pyautogui.click()
        pyautogui.moveTo(85, 777); pyautogui.click()
        pyautogui.moveTo(259, 286); pyautogui.doubleClick()
        pyautogui.moveTo(293, 972); pyautogui.click()
        image_name = f"dailychart_{i-1}_final.png"
        keyboard.write(image_name)
        pyautogui.press("enter")
        time.sleep(2)

        # 요약 추가
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        pyperclip.copy(summary)
        pyautogui.hotkey("ctrl", "v")
        pyautogui.hotkey("enter")

    driver.quit()

# ✅ 메인 실행 로직
if __name__ == "__main__":
    print("📌 뉴스 수집 중...")
    news_data = get_news_data()

    print("📌 상장 기업 목록 로딩...")
    df_krx = fdr.StockListing("KRX")
    company_list = df_krx["Name"].tolist()

    print("📌 중복 기사 필터링 및 차트 캡처 중...")
    unique_articles = remove_duplicate_articles(news_data, company_list, df_krx)

    print("📌 Gemini로 요약 중...")
    summaries = summarize_articles_with_gemini(unique_articles)

    print("📌 네이버 블로그 자동 포스팅 중...")
    post_to_naver_blog(unique_articles, summaries)
