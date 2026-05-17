import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 페이지 기본 설정
st.set_page_config(layout="wide", page_title="나스닥 100 장기투자 스크리너")

# ==========================================
# 1. 핵심 분석 함수들
# ==========================================

# RSI(상대강도지수) 계산 함수
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 나스닥 100 티커 목록 자동 수집 (위키피디아)
@st.cache_data(ttl=86400) # 24시간에 한 번만 실행
def get_nasdaq_100_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        tables = pd.read_html(url)
        for table in tables:
            if 'Ticker' in table.columns:
                # 불필요한 공백 제거 및 리스트 변환
                return [ticker.strip() for ticker in table['Ticker'].tolist()]
    except Exception as e:
        st.error("티커 목록을 가져오는 데 실패했습니다.")
        # 실패 시 주요 대형주 위주로 백업 리스트 반환
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "PEP", "COST"]

# ==========================================
# 2. 데이터 수집 및 캐싱 (가장 무거운 작업)
# ==========================================

@st.cache_data(ttl=3600) # 1시간 동안 데이터 캐시 유지 (속도 최적화)
def load_and_analyze_data(tickers):
    results = []
    
    # 진행 상황을 보여주기 위한 프로그레스 바
    progress_text = "나스닥 100 종목 데이터를 수집하고 분석 중입니다. (최초 1회 약 1~2분 소요)"
    my_bar = st.progress(0, text=progress_text)
    
    total_tickers = len(tickers)
    
    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="6mo")
            
            if hist.empty:
                continue
                
            # 기술적 지표 및 가격 위치 계산
            hist['RSI'] = calculate_rsi(hist)
            current_price = hist['Close'].iloc[-1]
            current_rsi = hist['RSI'].iloc[-1]
            
            high_52w = info.get('fiftyTwoWeekHigh', hist['Close'].max())
            low_52w = info.get('fiftyTwoWeekLow', hist['Close'].min())
            
            # 52주 바닥 대비 얼마나 올랐는지 (%)
            if high_52w != low_52w:
                price_pos = (current_price - low_52w) / low_52w * 100
            else:
                price_pos = 0
                
            # 재무 지표 추출
            roe = info.get('returnOnEquity', 0)
            roe = roe * 100 if roe is not None else 0
            
            fcf = info.get('freeCashflow', 0)
            fcf = fcf if fcf is not None else 0
            
            results.append({
                "티커": ticker,
                "기업명": info.get('shortName', ticker),
                "섹터": info.get('sector', 'N/A'),
                "현재가 ($)": round(current_price, 2),
                "ROE (%)": round(roe, 2),
                "FCF (억$)": round(fcf / 100000000, 2), # 보기 쉽게 억 달러 단위로 변환
                "RSI (14일)": round(current_rsi, 2),
                "52주 바닥 대비 상승률 (%)": round(price_pos, 2)
            })
            
        except:
            pass # 일부 상장폐지되거나 오류나는 티커는 무시
            
        # 프로그레스 바 업데이트
        my_bar.progress((i + 1) / total_tickers, text=f"{progress_text} ({i+1}/{total_tickers})")
        
    my_bar.empty() # 완료 후 프로그레스 바 삭제
    return pd.DataFrame(results)

# ==========================================
# 3. 대시보드 UI 및 필터링 로직
# ==========================================

st.title("🦅 나스닥 100 장기투자 스크리너")
st.markdown("**워런 버핏의 경제적 해자(재무)**와 **코스톨라니의 달걀 이론(과매도 심리)**을 결합하여 나스닥 최우량주 중 진흙 속의 진주를 찾습니다.")
st.divider()

# 데이터 로드
tickers = get_nasdaq_100_tickers()
df = load_and_analyze_data(tickers)

# 필터 UI 레이아웃 구성
st.subheader("⚙️ 스크리닝 조건 설정")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🟢 버핏 필터 (안전마진 & 해자)")
    min_roe = st.slider("최소 ROE (%)", min_value=0, max_value=50, value=15, step=5, 
                        help="기업이 자본을 얼마나 효율적으로 굴리는지 나타냅니다. 보통 15% 이상이면 훌륭한 비즈니스 모델로 평가합니다.")
    require_fcf = st.toggle("FCF(잉여현금흐름) 흑자 기업만 보기", value=True, 
                            help="배당이나 재투자에 쓸 수 있는 진짜 현금이 회사에 들어오고 있는지 확인합니다.")

with col2:
    st.markdown("#### 🔵 코스톨라니 필터 (공포 심리 & 바닥 확인)")
    max_rsi = st.slider("최대 RSI (과매도 지표)", min_value=10, max_value=100, value=40, step=5, 
                        help="30 이하면 극단적인 과매도(대중의 공포) 구간을 의미합니다.")
    max_price_pos = st.slider("52주 바닥 대비 최대 상승률 (%)", min_value=0, max_value=100, value=30, step=5, 
                              help="현재 주가가 52주 최저가로부터 얼마나 떨어져 있는지 설정합니다. 낮을수록 바닥에 가깝습니다.")

# 데이터 필터링 적용
filtered_df = df[
    (df['ROE (%)'] >= min_roe) &
    (df['RSI (14일)'] <= max_rsi) &
    (df['52주 바닥 대비 상승률 (%)'] <= max_price_pos)
]

if require_fcf:
    filtered_df = filtered_df[filtered_df['FCF (억$)'] > 0]

# 결과 출력
st.divider()
st.markdown(f"### 🎯 스크리닝 결과: 총 **{len(filtered_df)}** 종목 포착")

if not filtered_df.empty:
    # 인덱스 숨기고 테이블 출력
    st.dataframe(
        filtered_df.style.format({
            "현재가 ($)": "{:,.2f}",
            "ROE (%)": "{:.1f}%",
            "FCF (억$)": "{:,.1f}",
            "RSI (14일)": "{:.1f}",
            "52주 바닥 대비 상승률 (%)": "{:.1f}%"
        }),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("💡 현재 설정한 가치 및 과매도 기준을 모두 만족하는 종목이 없습니다. 시장이 전체적으로 과열권이거나 조건이 너무 엄격할 수 있습니다. 슬라이더를 조정해 보세요.")