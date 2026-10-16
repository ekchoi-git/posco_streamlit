import os
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage
from email.utils import getaddresses
from html import escape
from urllib.parse import quote_plus
from xml.etree import ElementTree

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


st.set_page_config(
    page_title="Streamlit Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def make_data(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days = pd.date_range(end=date.today(), periods=30)
    return pd.DataFrame(
        {
            "날짜": days,
            "방문자": rng.integers(800, 1800, len(days)),
            "가입자": rng.integers(80, 320, len(days)),
            "전환율": rng.uniform(4.5, 12.5, len(days)).round(1),
        }
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker: str, period: str) -> pd.DataFrame:
    """Yahoo Finance에서 최근 가격 데이터를 가져옵니다."""
    import yfinance as yf

    history = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if history.empty:
        raise ValueError("가격 데이터를 찾지 못했습니다. 거래소 접미사가 필요한지 확인해 주세요.")
    history = history.reset_index()
    history["Date"] = pd.to_datetime(history["Date"]).dt.tz_localize(None)
    return history


@st.cache_data(ttl=900, show_spinner=False)
def fetch_stock_news(ticker: str) -> list[dict[str, str]]:
    """Google News RSS에서 티커 관련 최신 헤드라인을 가져옵니다."""
    query = quote_plus(f"{ticker} stock")
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    response = requests.get(url, timeout=10, headers={"User-Agent": "Streamlit-Lab/1.0"})
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    articles = []
    for item in root.findall("./channel/item")[:5]:
        articles.append(
            {
                "title": item.findtext("title", "제목 없음"),
                "link": item.findtext("link", ""),
                "published": item.findtext("pubDate", "날짜 정보 없음"),
            }
        )
    return articles


def build_stock_report(ticker: str, history: pd.DataFrame, news: list[dict[str, str]]) -> str:
    closes = history["Close"].astype(float)
    latest = closes.iloc[-1]
    first = closes.iloc[0]
    period_return = ((latest / first) - 1) * 100
    high = history["High"].max()
    low = history["Low"].min()
    average_volume = history["Volume"].mean()
    ma20 = closes.tail(20).mean()
    ma_signal = "상회" if latest >= ma20 else "하회"
    direction = "상승" if period_return >= 0 else "하락"
    end_date = history["Date"].iloc[-1].date().isoformat()

    report = [
        f"[{ticker}] 주식·뉴스 요약 보고서",
        f"작성 기준: {end_date}",
        "",
        "1. 가격 요약",
        f"- 최근 종가: {latest:,.2f}",
        f"- 분석 기간 수익률: {period_return:+.2f}% ({direction})",
        f"- 기간 고가 / 저가: {high:,.2f} / {low:,.2f}",
        f"- 20일 이동평균: {ma20:,.2f} (최근 종가가 이동평균 {ma_signal})",
        f"- 일평균 거래량: {average_volume:,.0f}",
        "",
        "2. 뉴스 헤드라인",
    ]
    if news:
        report.extend(f"- {article['title']} ({article['published']})" for article in news)
    else:
        report.append("- 조회된 최신 뉴스가 없습니다.")
    report.extend(
        [
            "",
            "3. 유의사항",
            "- 이 보고서는 공개 가격 데이터와 뉴스 헤드라인을 기계적으로 요약한 정보이며 투자 조언이 아닙니다.",
            "- 투자 결정 전 기업 공시, 원문 기사 및 전문가 의견을 별도로 확인해 주세요.",
        ]
    )
    return "\n".join(report)


def send_report_email(
    host: str,
    port: int,
    security_mode: str,
    sender: str,
    app_password: str,
    recipients: str,
    subject: str,
    report: str,
) -> None:
    recipient_list = [address for _, address in getaddresses([recipients]) if address]
    if not recipient_list:
        raise ValueError("올바른 수신자 이메일 주소를 입력해 주세요.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipient_list)
    message.set_content(report)

    context = ssl.create_default_context()
    if security_mode == "SSL/TLS":
        with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
            server.login(sender, app_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender, app_password)
            server.send_message(message)


def home_page():
    st.title("🧪 Streamlit Lab")
    st.caption("기초 위젯부터 데이터 시각화와 AI 챗봇까지 한 곳에서 살펴보세요.")

    left, right = st.columns([1.4, 1], gap="large")
    with left:
        st.markdown(
            """
            ### 반가워요!

            이 사이트는 폴더 안의 Streamlit 실습 예제를 하나의 대시보드로 재구성한 학습용 앱입니다.
            왼쪽 메뉴에서 원하는 실습을 선택하고, 위젯을 직접 조작해 보세요.
            """
        )
        st.info("💡 사이드바에서 페이지를 선택하면 실습 화면이 열립니다.")
    with right:
        st.metric("실습 페이지", "4개", "+1 통합")
        st.metric("핵심 컴포넌트", "15+", "위젯 · 차트 · 상태관리")

    st.divider()
    st.subheader("오늘의 미리보기")
    df = make_data()
    a, b, c = st.columns(3)
    a.metric("최근 방문자", f"{df['방문자'].iloc[-1]:,}명", f"{df['방문자'].pct_change().iloc[-1] * 100:.1f}%")
    b.metric("최근 가입자", f"{df['가입자'].iloc[-1]:,}명", f"{df['가입자'].pct_change().iloc[-1] * 100:.1f}%")
    c.metric("평균 전환율", f"{df['전환율'].mean():.1f}%", "최근 30일")
    st.area_chart(df.set_index("날짜")["방문자"])


def input_page():
    st.title("📝 입력 위젯 실습")
    st.caption("사용자의 입력을 받고 결과를 즉시 화면에 반영합니다.")
    with st.form("profile_form"):
        name = st.text_input("이름", placeholder="홍길동")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("나이", min_value=0, max_value=120, value=20)
            selected_date = st.date_input("날짜", value=date.today())
        with col2:
            option = st.selectbox("관심 분야", ["데이터 분석", "웹 앱", "AI", "자동화"])
            tools = st.multiselect("사용해 본 도구", ["Python", "Pandas", "Plotly", "OpenAI"])
        bio = st.text_area("한 줄 소개", max_chars=120)
        agree = st.checkbox("실습 결과를 확인했습니다")
        submitted = st.form_submit_button("결과 확인", type="primary")
    if submitted:
        if not name:
            st.warning("이름을 입력해 주세요.")
        elif not agree:
            st.warning("확인 체크박스를 선택해 주세요.")
        else:
            st.success(f"{name}님, {selected_date} 기준 입력이 저장되었습니다!")
            st.json({"이름": name, "나이": age, "관심 분야": option, "도구": tools, "소개": bio})


def data_page():
    st.title("📊 데이터 시각화")
    st.caption("샘플 방문 데이터를 필터링하고 다양한 차트로 확인합니다.")
    df = make_data()
    min_day, max_day = st.slider(
        "조회 기간",
        min_value=df["날짜"].min().date(),
        max_value=df["날짜"].max().date(),
        value=(df["날짜"].min().date(), df["날짜"].max().date()),
    )
    filtered = df[df["날짜"].dt.date.between(min_day, max_day)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.line(filtered, x="날짜", y="방문자", markers=True, title="일별 방문자"), use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(filtered, x="날짜", y="가입자", title="일별 가입자", color="가입자"), use_container_width=True)


def chatbot_page():
    st.title("💬 AI 챗봇")
    st.caption("OpenAI API 키를 입력하면 대화형 챗봇을 사용할 수 있습니다.")
    api_key = st.text_input("OpenAI API 키", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        st.info("API 키가 없어도 페이지는 열립니다. 키를 입력하면 대화를 시작할 수 있어요.")
        return
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        st.error("openai 패키지가 설치되지 않았습니다. requirements.txt를 설치해 주세요.")
        return
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("무엇이든 물어보세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
            ).choices[0].message.content
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})


def stock_report_page():
    st.title("📈 주식·뉴스 보고서")
    st.caption("Yahoo Finance 가격 데이터와 Google News RSS 헤드라인을 바탕으로 정형 보고서를 생성합니다.")

    with st.form("stock_query_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker = st.text_input("티커", value="AAPL", help="예: AAPL, MSFT, 005930.KS")
        with col2:
            period_label = st.selectbox("분석 기간", ["1개월", "3개월", "6개월", "1년"], index=1)
        generate = st.form_submit_button("보고서 생성", type="primary")

    if generate:
        ticker = ticker.strip().upper()
        if not ticker:
            st.warning("티커를 입력해 주세요.")
        else:
            periods = {"1개월": "1mo", "3개월": "3mo", "6개월": "6mo", "1년": "1y"}
            try:
                with st.spinner("가격 데이터와 뉴스를 수집하고 있습니다..."):
                    history = fetch_stock_data(ticker, periods[period_label])
                    try:
                        news = fetch_stock_news(ticker)
                    except requests.RequestException:
                        news = []
                    report = build_stock_report(ticker, history, news)
                st.session_state.stock_report = report
                st.session_state.stock_ticker = ticker
                st.session_state.stock_history = history
                st.session_state.stock_news = news
            except Exception as error:
                st.error(f"보고서를 생성하지 못했습니다: {error}")

    report = st.session_state.get("stock_report")
    if not report:
        st.info("티커와 분석 기간을 선택한 뒤 ‘보고서 생성’을 눌러 주세요.")
        return

    history = st.session_state.stock_history
    news = st.session_state.stock_news
    chart = px.line(history, x="Date", y="Close", title=f"{st.session_state.stock_ticker} 종가 추이")
    st.plotly_chart(chart, use_container_width=True)
    st.subheader("생성된 보고서")
    st.text_area("보고서 내용", value=report, height=360, label_visibility="collapsed")
    if news:
        with st.expander("수집한 뉴스 원문 보기"):
            for article in news:
                st.markdown(f"- [{escape(article['title'])}]({article['link']})  ")
                st.caption(article["published"])

    st.divider()
    st.subheader("✉️ SMTP로 보고서 보내기")
    st.caption("계정과 앱 비밀번호는 이 브라우저 세션에서 전송 시에만 사용하며 파일이나 코드에 저장하지 않습니다.")
    with st.form("smtp_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            smtp_host = st.text_input("SMTP 서버", value="smtp.gmail.com")
            smtp_port = st.number_input("포트", min_value=1, max_value=65535, value=587, step=1)
            security_mode = st.selectbox("보안 방식", ["STARTTLS", "SSL/TLS"])
        with col2:
            sender = st.text_input("보내는 계정 이메일")
            app_password = st.text_input("앱 비밀번호", type="password", help="일반 비밀번호가 아닌 메일 제공업체의 앱 비밀번호를 사용하세요.")
            recipients = st.text_input("받는 사람", help="여러 명은 쉼표로 구분하세요.")
        send = st.form_submit_button("보고서 메일 보내기", type="primary")

    if send:
        if not all([smtp_host, sender, app_password, recipients]):
            st.warning("SMTP 서버, 보내는 계정, 앱 비밀번호, 받는 사람을 모두 입력해 주세요.")
        else:
            try:
                send_report_email(
                    smtp_host.strip(),
                    int(smtp_port),
                    security_mode,
                    sender.strip(),
                    app_password,
                    recipients.strip(),
                    f"[{st.session_state.stock_ticker}] 주식·뉴스 요약 보고서",
                    report,
                )
                st.success("보고서 메일을 전송했습니다.")
            except (OSError, smtplib.SMTPException, ValueError) as error:
                st.error(f"메일을 전송하지 못했습니다: {error}")


with st.sidebar:
    st.title("🧪 Streamlit Lab")
    st.caption("실습 통합 대시보드")
    page = st.radio("메뉴", ["홈", "입력 위젯", "데이터 시각화", "주식·뉴스 보고서", "AI 챗봇"], label_visibility="collapsed")
    st.divider()
    st.caption("원본 실습 파일: 1~5.streamlit.py")

if page == "홈":
    home_page()
elif page == "입력 위젯":
    input_page()
elif page == "데이터 시각화":
    data_page()
elif page == "주식·뉴스 보고서":
    stock_report_page()
else:
    chatbot_page()
