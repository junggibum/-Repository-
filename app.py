import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from datetime import datetime

# 1. 최상단 배치 고정 (Streamlit 필수 규칙)
st.set_page_config(page_title="The Arsenal v3.0", page_icon="🚀", layout="wide")

# ⏱️ 10초마다 자동 새로고침 가동
st_autorefresh(interval=10000, limit=1000, key="data_refresh")

# 사이드바: 텔레그램 알림 설정 (개념적 인터페이스)
with st.sidebar:
    st.header("🚨 실시간 알림 센터")
    st.toggle("텔레그램 알림 활성화", value=False)
    st.text_input("Bot Token (비공개)", type="password")
    st.info("알림 조건: 거래량 2배 폭발 or 52주 신고가 돌파")

st.title("🚀 통합 투자 무기: The Arsenal v3.0")
st.markdown("---")

col1, col2 = st.columns([1.2, 0.8])

# ====== [왼쪽: 미국 주식 성장주 엔진] ======
with col1:
    st.header("🇺🇸 US Growth & Chart")
    
    ticker_input = st.text_input("검증할 티커 입력 (예: NVDA, TSLA, PLTR)", "NVDA").upper()
    
    if ticker_input:
        try:
            stock = yf.Ticker(ticker_input)
            
            # 1. 캔들스틱 차트 구현 (Plotly)
            hist = stock.history(period="60d")
            
            if not hist.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    name="주가"
                )])
                
                # 이동평균선 추가 (20일) - 데이터가 충분할 때만 계산
                if len(hist) >= 20:
                    hist['MA20'] = hist['Close'].rolling(window=20).mean()
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['MA20'], line=dict(color='orange', width=2), name="MA20"))
                
                fig.update_layout(title=f"{ticker_input} 60일 캔들 차트", template="plotly_dark", height=450, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"{ticker_input}의 주가 데이터를 찾을 수 없습니다.")

            # 2. 실적 발표일 카운트다운 (안정성 강화)
            try:
                cal = stock.calendar
                if cal is not None and not cal.empty:
                    # 데이터 구조에 따라 'Earnings Date' 키 추출 방식 대응
                    if 'Earnings Date' in cal.index:
                        next_earnings = cal.loc['Earnings Date'].iloc[0]
                    else:
                        next_earnings = cal.iloc[0, 0]
                        
                    # datetime 객체인지 확인 후 연산
                    if isinstance(next_earnings, datetime):
                        days_left = (next_earnings.date() - datetime.now().date()).days
                        st.info(f"📅 다음 실적 발표 예정일: **{next_earnings.date()}** (약 {days_left}일 남음)")
                    else:
                        st.info(f"📅 다음 실적 발표 예정일: **{next_earnings}**")
                else:
                    st.caption("실적 발표일 정보를 가져올 수 없습니다.")
            except Exception:
                st.caption("실적 발표 일정 로딩 실패 (yfinance API 제한)")

            # 3. 공격적 성장 필터
            info = stock.info
            roe = (info.get('returnOnEquity') or 0) * 100
            rev_growth = (info.get('revenueGrowth') or 0) * 100
            
            f1, f2 = st.columns(2)
            f1.metric("ROE (버핏 기준 15%+)", f"{roe:.1f}%", delta=f"{roe-15:.1f}%")
            f2.metric("매출 성장률 (공격 기준 20%+)", f"{rev_growth:.1f}%", delta=f"{rev_growth-20:.1f}%")
            
        except Exception as e:
            st.error(f"데이터 오류: {ticker_input} 정보를 확인할 수 없습니다. (에러: {e})")

# ====== [오른쪽: 국내 주식 수급 & 테마] ======
with col2:
    st.header("🇰🇷 KR Momentum Radar")
    
    # 1. 네이버 증권 테마 상위 스캐너
    st.subheader("🔥 당일 주도 테마 (Top 5)")
    theme_url = "https://finance.naver.com/sise/theme.naver"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(theme_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        themes = soup.find_all('td', {'class': 'col_type1'})
        changes = soup.find_all('td', {'class': 'col_type2'})
        
        theme_list = []
        for i in range(min(5, len(themes))):
            name = themes[i].text.strip()
            change = changes[i].text.strip()
            theme_list.append({"테마명": name, "상승률": change})
            
        if theme_list:
            st.table(pd.DataFrame(theme_list))
        else:
            st.caption("현재 파싱 가능한 테마 데이터가 없습니다.")
    except Exception:
        st.caption("테마 데이터를 불러오는 중 오류 발생")

    st.markdown("---")
    
    # 2. 실시간 거래량 레이더 + 알림 로직
    st.subheader("🚀 실시간 거래량 Top 10")
    my_target = st.text_input("🚨 집중 감시 종목 (예: SK하이닉스)", "SK하이닉스")
    
    url = "https://finance.naver.com/sise/sise_quant.naver"
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'type_2'})
        
        kr_data = []
        if table:
            # 빈 행이나 구분선 제외, 실제 데이터 행만 필터링하기 위해 'no' 클래스 검사 등 활용 가능
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                # 데이터가 확실히 있는 행만 타겟팅 (종목명과 거래량 인덱스 안정성 확보)
                if len(cols) >= 6 and cols[1].find('a'): 
                    name = cols[1].text.strip()
                    volume = cols[5].text.strip()
                    
                    # 타겟 종목 포착 시 토스트 알림
                    if name == my_target:
                        st.toast(f"🚩 감시 종목 [{my_target}] 거래량 상위 진입!", icon="🚩")
                        name = f"🚨 {name}"
                    
                    kr_data.append({"종목명": name, "거래량": volume})
                    if len(kr_data) == 10: 
                        break
            
            if kr_data:
                st.dataframe(pd.DataFrame(kr_data), use_container_width=True, hide_index=True)
            else:
                st.caption("거래량 데이터를 찾을 수 없습니다.")
        else:
            st.error("테이블 구조를 로드하지 못했습니다.")
    except Exception as e:
        st.error(f"거래량 데이터를 가져오지 못했습니다. ({e})")

    st.markdown("---")
    
    # 3. 매크로 미니 보드
    st.subheader("🌍 매크로 퀵체크")
    try:
        vix_hist = yf.Ticker("^VIX").history(period="2d")
        if not vix_hist.empty:
            vix = vix_hist['Close'].iloc[-1]
            st.metric("VIX 지수 (20미만 안정)", f"{vix:.2f}", delta="-안정" if vix < 20 else "+경계", delta_color="inverse")
        else:
            st.caption("VIX 지수를 가져올 수 없습니다.")
    except Exception: 
        st.caption("VIX 데이터를 불러오는 중 오류 발생")