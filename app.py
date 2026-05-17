import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 기술적 지표 계산을 위한 함수 (RSI)
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

st.set_page_config(layout="wide")
st.title("💡 가치 & 심리 통합 투자 대시보드")
st.subheader("🎯 포트폴리오 목표: 미국 주식 20% / 국내 주식 단타 30% 수익률")

# 스크리닝할 종목 티커 기본값 세팅 (대형 제약/소비재 및 성장주, 국내 종목 포함)
default_tickers = "JNJ, PFE, KO, RXRX, JEPQ, 068270.KS"
ticker_input = st.text_input("분석할 티커를 입력하세요 (쉼표로 구분):", default_tickers)
tickers = [t.strip() for t in ticker_input.split(",")]

if st.button("종목 스캐닝 시작"):
    results = []
    
    with st.spinner("데이터를 불러오고 분석하는 중입니다..."):
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # 최근 6개월 데이터 로드 (코스톨라니 지표용)
                hist = stock.history(period="6mo")
                if hist.empty:
                    continue
                    
                hist['RSI'] = calculate_rsi(hist)
                current_price = hist['Close'].iloc[-1]
                current_rsi = hist['RSI'].iloc[-1]
                
                # 52주 최고/최저가 대비 현재 위치 계산
                high_52w = info.get('fiftyTwoWeekHigh', hist['Close'].max())
                low_52w = info.get('fiftyTwoWeekLow', hist['Close'].min())
                price_pos = (current_price - low_52w) / (high_52w - low_52w) * 100 if high_52w != low_52w else 50
                
                # 1. 워런 버핏 지표 (경제적 해자 & 밸류에이션)
                roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
                fcf = info.get('freeCashflow', 0)
                pe_ratio = info.get('trailingPE', 0)
                
                buffett_score = "🟢 합격" if roe >= 15 and fcf > 0 else "🔴 주의"
                
                # 2. 코스톨라니 지표 (소외 국면 & 과매도)
                # RSI 30 이하이거나, 주가가 52주 신저가 근처(하위 20%)일 때 소외 국면으로 판단
                kostolany_score = "🟢 매수 기회(소외)" if current_rsi <= 30 or price_pos <= 20 else "🟡 관망"
                
                results.append({
                    "종목명": info.get('shortName', ticker),
                    "티커": ticker,
                    "현재가": round(current_price, 2),
                    "ROE (%)": round(roe, 2),
                    "PER": round(pe_ratio, 2) if pe_ratio else "N/A",
                    "RSI (14일)": round(current_rsi, 2),
                    "52주 최저가 대비 위치(%)": round(price_pos, 2),
                    "버핏 평가 (펀더멘털)": buffett_score,
                    "코스톨라니 평가 (심리/가격)": kostolany_score
                })
                
            except Exception as e:
                st.error(f"{ticker} 데이터 처리 중 오류 발생: {e}")
                
    if results:
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True)
        
        st.info("""
        **해석 가이드:**
        * **버핏 평가:** ROE가 15% 이상이고 잉여현금흐름이 플러스인 튼튼한 기업을 찾습니다.
        * **코스톨라니 평가:** RSI 지표가 30 이하이거나 52주 바닥권에 머물러 대중의 관심이 식어버린 종목을 포착합니다.
        * **최적의 타겟:** 두 가지 평가에서 모두 '🟢' 불이 들어온 종목이 최우선 관찰 대상입니다.
        """)
        pass