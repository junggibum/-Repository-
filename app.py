import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# 10초마다 자동 새로고침 가동
st_autorefresh(interval=10000, limit=1000, key="data_refresh")

st.set_page_config(page_title="나만의 투자 대시보드 v2.0", page_icon="🚀", layout="wide")
st.title("🚀 야수의 심장 투자 대시보드 (v2.0 - 미국 주식 집중 모드)")
st.markdown("---")

col1, col2 = st.columns(2)

# ====== [왼쪽 화면: 1단계 & 2단계 미래 섹터 및 기업 엄선] ======
with col1:
    st.header("🎯 1단계: 미래 주도 섹터 모니터링")
    st.write("공격적 수익(20%+)을 위해 돈이 몰리는 미래 섹터의 최근 추세를 확인합니다.")
    
    # 주요 미래 성장 섹터 ETF 리스트
    sector_etfs = {
        "AI & 반도체 (SOXX)": "SOXX",
        "빅테크 성장주 (QQQ)": "QQQ",
        "바이오테크 혁신 (IBB)": "IBB",
        "정밀 의학/유전학 (ARKG)": "ARKG"
    }
    
    sector_data = []
    for name, ticker in sector_etfs.items():
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period="5d") # 최근 5일 추이
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                chg = ((price - prev_price) / prev_price) * 100
                sector_data.append({"섹터 (ETF)": name, "현재가": f"${price:.2f}", "전일대비": f"{chg:+.2f}%"})
        except:
            continue
            
    if sector_data:
        st.dataframe(pd.DataFrame(sector_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.header("🧐 2단계: 공격적 성장주 + 버핏 필터")
    st.write("미래 섹터 기업 중 **'폭발적 성장성'**과 **'버핏의 재무 안정성'**을 동시 검증합니다.")
    
    target_ticker = st.text_input("검증할 미국 기술주/바이오 티커 입력 (예: NVDA, PLTR, AMZN)", "NVDA").upper()
    
    if target_ticker:
        try:
            stock = yf.Ticker(target_ticker)
            info = stock.info
            
            # 공격적 성장주의 핵심: 매출 성장률 (Revenue Growth)
            rev_growth = (info.get('revenueGrowth') or 0) * 100
            # 버핏의 핵심: ROE 및 부채비율
            roe = (info.get('returnOnEquity') or 0) * 100
            debt = info.get('debtToEquity') or 0
            
            # 공격적 버핏 기준 채점
            g_pass = rev_growth >= 20  # 매출성장률 연 20% 이상 (공격)
            r_pass = roe >= 15         # ROE 15% 이상 (버핏)
            d_pass = 0 < debt <= 80    # 부채비율 80% 이하 (성장주 감안 완화)
            
            s1, s2, s3 = st.columns(3)
            s1.metric("매출 성장률 (기준: >20%)", f"{rev_growth:.1f}%", "합격" if g_pass else "미달", delta_color="normal" if g_pass else "inverse")
            s2.metric("자기자본이익률 ROE (>15%)", f"{roe:.1f}%", "합격" if r_pass else "미달", delta_color="normal" if r_pass else "inverse")
            s3.metric("부채비율 (기준: <80%)", f"{debt:.1f}%", "합격" if d_pass else "미달", delta_color="normal" if d_pass else "inverse")
            
            if g_pass and r_pass and d_pass:
                st.success(f"🔥 **{target_ticker}** 은(는) 버핏의 안전망을 통과한 초고속 주도주입니다! 포트폴리오 편입 적극 검토.")
            else:
                st.warning(f"⚠️ **{target_ticker}** 은(는) 일부 공격적 가치 기준에 미달합니다. 신중한 접근이 필요합니다.")
                
            # 최신 뉴스 연동
            st.write(f"**📰 {target_ticker} 핵심 이슈**")
            news = stock.news
            for i in range(min(2, len(news))):
                st.markdown(f"- [{news[i]['title']}]({news[i]['link']})")
        except:
            st.error("종목 데이터를 불러올 수 없습니다.")

# ====== [오른쪽 화면: 3단계 내 포트폴리오 구성 및 국내 레이더] ======
with col2:
    st.header("📊 3단계: 연 목표 20%+ 포트폴리오 시뮬레이션")
    st.write("안정적인 JEPQ와 고성장 야수주들의 비중을 조절하여 황금 비율을 찾습니다.")
    
    # 슬라이더로 비중 조절 조작
    growth_weight = st.slider("고성장 공격형 주식(예: 엔비디아 등) 비중 (%)", 0, 100, 70)
    jepq_weight = 100 - growth_weight
    
    st.write(f"현재 설정된 포트폴리오 비율: **성장주 {growth_weight}% : JEPQ {jepq_weight}%**")
    
    # 자산 배분 시각화 표
    portfolio_df = pd.DataFrame({
        "자산 분류": ["공격형 고성장주 (수익 담당)", "방어형 고배당주 (현금 흐름 담당)"],
        "해당 종목 예시": [target_ticker, "JEPQ (130.83주 보유 중)"],
        "목표 비중": [f"{growth_weight}%", f"{jepq_weight}%"],
        "기대 역할": ["연 20~30% 주가 슈팅 타겟", "월배당을 통한 하방 방어 및 재투자 재원"]
    })
    st.table(portfolio_df)
    
    st.markdown("---")
    st.subheader("🇰🇷 국내 주식: 단타 레이더 (대기 모드)")
    
    # 네이버 크롤링 코드는 유지하되 하단에 깔끔하게 배치
    url = "https://finance.naver.com/sise/sise_quant.naver"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'type_2'})
        kr_data = []
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 10:
                kr_data.append({"종목명": cols[1].text.strip(), "당일 거래량": cols[5].text.strip()})
                if len(kr_data) == 5: break # 대기 모드이므로 5개만 간결하게 표시
        st.dataframe(pd.DataFrame(kr_data), use_container_width=True, hide_index=True)
    except:
        pass