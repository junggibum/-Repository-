import streamlit as st
import yfinance as yf
import pandas as pd

# 기술적 지표 계산 함수 (RSI)
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 특정 티커의 최근 가격과 변동폭을 가져오는 함수
def get_macro_metric(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if len(data) >= 2:
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            delta = current_price - prev_price
            delta_percent = (delta / prev_price) * 100
            return current_price, delta, delta_percent
        return None, None, None
    except:
        return None, None, None

st.set_page_config(layout="wide", page_title="투자 대시보드 v3.0")
st.title("💡 가치 & 심리 통합 투자 대시보드 v3.0")
st.markdown("🎯 **포트폴리오 목표:** 미국 주식 20% 수익 (장기) / 국내 주식 30% 수익 (단기)")

st.divider()

# ==========================================
# 1. 매크로 지표 전광판 (코스톨라니 나침반)
# ==========================================
st.header("🌍 글로벌 매크로 지표 (시장의 온도 읽기)")
st.caption("대중의 심리와 유동성의 방향을 파악하여 투자 비중을 조절하세요.")

col1, col2, col3 = st.columns(3)

with col1:
    vix_price, vix_delta, vix_pct = get_macro_metric("^VIX")
    if vix_price:
        # VIX는 오르면 공포(빨간색/역방향 주의), 내리면 안정(초록색)
        st.metric(label="😱 VIX (공포지수)", 
                  value=f"{vix_price:.2f}", 
                  delta=f"{vix_delta:.2f} ({vix_pct:.2f}%)",
                  delta_color="inverse")

with col2:
    tnx_price, tnx_delta, tnx_pct = get_macro_metric("^TNX")
    if tnx_price:
        st.metric(label="🏦 미국 국채 10년물 금리 (%)", 
                  value=f"{tnx_price:.3f}%", 
                  delta=f"{tnx_delta:.3f}bp ({tnx_pct:.2f}%)",
                  delta_color="inverse")

with col3:
    dxy_price, dxy_delta, dxy_pct = get_macro_metric("DX-Y.NYB")
    if dxy_price:
        st.metric(label="💵 달러 인덱스 (자금 흐름)", 
                  value=f"{dxy_price:.2f}", 
                  delta=f"{dxy_delta:.2f} ({dxy_pct:.2f}%)",
                  delta_color="inverse")

st.divider()

# ==========================================
# 2. 개별 종목 스캐너 (워런 버핏 & 코스톨라니)
# ==========================================
st.header("🔎 관심 종목 스캐너 (저평가 가치주 발굴)")

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
                hist = stock.history(period="6mo")
                
                if hist.empty:
                    continue
                    
                hist['RSI'] = calculate_rsi(hist)
                current_price = hist['Close'].iloc[-1]
                current_rsi = hist['RSI'].iloc[-1]
                
                high_52w = info.get('fiftyTwoWeekHigh', hist['Close'].max())
                low_52w = info.get('fiftyTwoWeekLow', hist['Close'].min())
                price_pos = (current_price - low_52w) / (high_52w - low_52w) * 100 if high_52w != low_52w else 50
                
                roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
                fcf = info.get('freeCashflow', 0)
                pe_ratio = info.get('trailingPE', 0)
                
                buffett_score = "🟢 합격" if roe >= 15 and fcf > 0 else "🔴 주의"
                kostolany_score = "🟢 매수 기회" if current_rsi <= 30 or price_pos <= 20 else "🟡 관망"
                
                results.append({
                    "종목명": info.get('shortName', ticker),
                    "티커": ticker,
                    "현재가": round(current_price, 2),
                    "ROE (%)": round(roe, 2),
                    "PER": round(pe_ratio, 2) if pe_ratio else "N/A",
                    "RSI": round(current_rsi, 2),
                    "52주 바닥 대비 (%)": round(price_pos, 2),
                    "버핏 (해자)": buffett_score,
                    "코스톨라니 (심리)": kostolany_score
                })
            except Exception as e:
                pass # 에러 발생 시 조용히 패스 (실제 환경에서는 로깅 필요)
                
    if results:
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True)