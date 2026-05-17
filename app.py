import streamlit as st
import yfinance as yf

st.divider()
st.header("⚖️ 포트폴리오 5:5 바벨 전략 리밸런싱")
st.markdown("안정적인 배당(JEPQ)과 성장주(개별 종목)의 비중을 5:5로 맞추기 위한 투자금 계산기입니다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🛡️ 배당 방어 포트폴리오 (JEPQ)")
    
    # 1. JEPQ 실시간 가격 불러오기 및 자산 계산
    jepq_shares = st.number_input("현재 보유 중인 JEPQ 수량 (주)", value=130.837411, step=1.0, format="%.6f")
    
    try:
        jepq_ticker = yf.Ticker("JEPQ")
        jepq_current_price = jepq_ticker.history(period="1d")['Close'].iloc[-1]
    except:
        jepq_current_price = 54.00 # 에러 시 임시 기본값
        
    st.metric(label="JEPQ 현재가", value=f"${jepq_current_price:.2f}")
    
    jepq_total_value = jepq_shares * jepq_current_price
    st.success(f"**JEPQ 총 평가액: ${jepq_total_value:,.2f}**")

with col2:
    st.subheader("⚔️ 가치 성장 포트폴리오 (개별주)")
    
    # 2. 5:5 비율을 위한 필요 자금 계산
    target_stock_value = jepq_total_value
    st.info(f"**5:5 비율을 위해 필요한 주식 매수 자금: ${target_stock_value:,.2f}**")
    
    # 3. 투자할 종목 수에 따른 자금 분배
    stock_count = st.slider("투자할 개별 주식 종목 수", min_value=1, max_value=5, value=3)
    allocated_per_stock = target_stock_value / stock_count
    
    st.markdown(f"종목당 할당 금액: **${allocated_per_stock:,.2f}**")
    
    # 4. 종목별 매수 가능 수량 계산기
    st.markdown("#### 🛒 매수 시뮬레이터")
    for i in range(stock_count):
        sub_col1, sub_col2 = st.columns([1, 2])
        with sub_col1:
            buy_ticker = st.text_input(f"종목 {i+1} 티커", value=["AAPL", "GOOGL", "RXRX", "MSFT", "TSLA"][i], key=f"ticker_{i}")
        with sub_col2:
            try:
                if buy_ticker:
                    buy_price = yf.Ticker(buy_ticker).history(period="1d")['Close'].iloc[-1]
                    buy_shares = allocated_per_stock / buy_price
                    st.write(f"현재가: **${buy_price:.2f}** ➔ **{buy_shares:.2f}주** 매수 가능")
            except:
                st.write("가격을 불러올 수 없습니다.")

st.divider()
st.metric(label="💰 목표 총 자산 규모 (JEPQ + 개별주)", value=f"${(jepq_total_value * 2):,.2f}")