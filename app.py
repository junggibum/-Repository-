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

# ==========================================
# 백그라운드 데이터 수집 (캐싱 적용: 1시간 유지)
# ==========================================
@st.cache_data(ttl=3600)
def load_screener_data(tickers):
    results = []
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
            
            results.append({
                "종목명": info.get('shortName', ticker),
                "티커": ticker,
                "섹터": info.get('sector', 'N/A'),
                "현재가": round(current_price, 2),
                "ROE (%)": round(roe, 2),
                "FCF (억$)": round(fcf / 100000000, 2) if fcf else 0, # 편의상 억 달러로 변환
                "RSI": round(current_rsi, 2),
                "52주 최저가 대비 (%)": round(price_pos, 2),
            })
        except:
            continue
            
    return pd.DataFrame(results)

# 관찰할 주식 유니버스 (제약, 소비재, 배당, 테크 턴어라운드 후보군 등)
universe_tickers = [
    "JNJ", "PFE", "KO", "PG", "V", "MA", "RXRX", "JEPQ", 
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
    "UNH", "ABBV", "PEP", "WMT", "MCD"
]

st.header("⚙️ 실시간 자동화 스크리너")
st.caption("설정한 기준에 부합하는 종목만 자동으로 필터링되어 나타납니다.")

# 데이터 로딩 (캐시 덕분에 두 번째부터는 즉시 로딩됨)
with st.spinner("유니버스 데이터를 업데이트하는 중입니다..."):
    df = load_screener_data(universe_tickers)

# ==========================================
# 사용자 맞춤형 필터링 UI
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟢 워런 버핏 필터 (해자/재무)")
    min_roe = st.slider("최소 ROE (%)", min_value=0, max_value=50, value=15, step=5)
    require_fcf = st.checkbox("잉여현금흐름(FCF) 흑자 기업만 보기", value=True)

with col2:
    st.subheader("🔵 코스톨라니 필터 (심리/과매도)")
    max_rsi = st.slider("최대 RSI (과매도 기준)", min_value=10, max_value=100, value=40, step=5)
    max_price_pos = st.slider("52주 바닥 대비 위치 (%)", min_value=0, max_value=100, value=30, step=5)

# ==========================================
# 조건에 맞는 데이터 필터링 및 출력
# ==========================================
# 필터 적용
filtered_df = df[
    (df['ROE (%)'] >= min_roe) &
    (df['RSI'] <= max_rsi) &
    (df['52주 최저가 대비 (%)'] <= max_price_pos)
]

if require_fcf:
    filtered_df = filtered_df[filtered_df['FCF (억$)'] > 0]

# 결과 출력
st.markdown(f"### 🎯 조건 검색 결과: {len(filtered_df)} 종목 포착")

if not filtered_df.empty:
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
else:
    st.info("현재 설정한 가치 및 과매도 기준을 모두 만족하는 종목이 없습니다. 시장이 과열권이거나 조건이 너무 엄격할 수 있습니다.")