# Streamlit Lab

## 실행 방법

```powershell
cd C:\Users\user\Desktop\streamlit\streamlit
pip install -r requirements.txt
streamlit run app.py
```

AI 챗봇을 사용하려면 실행 전에 `OPENAI_API_KEY` 환경 변수를 설정하거나 앱의 입력창에 직접 키를 입력하세요.

## 주식·뉴스 보고서와 SMTP 메일

왼쪽 메뉴의 **주식·뉴스 보고서**에서 티커와 분석 기간을 선택하면 Yahoo Finance 가격 데이터와 Google News RSS 헤드라인을 기반으로 보고서를 생성합니다. 생성된 보고서는 화면에서 SMTP 서버, 계정, 앱 비밀번호, 수신자를 입력해 메일로 보낼 수 있습니다.

Gmail은 일반 비밀번호 대신 [앱 비밀번호](https://support.google.com/accounts/answer/185833)를 사용하세요. 입력값은 파일에 저장되지 않습니다.
