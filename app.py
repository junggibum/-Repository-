import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# ⏱️ [기능 1] 스피드 업: 10초(10000ms)마다 대시보드 자동 새로고침
count = st_autorefresh(interval=10000, limit=1000, key="data_refresh")

st.set_page_config(page_title="나만의 투자 대시보드", page_icon="📈", layout="wide")
st.title(f"📊 통합 투자 대시보드 (v1.7 - 풀옵션 가동 중 🚀) - {count}회 갱신됨")
st.markdown("---")

col1, col2 = st.columns(2)

# ====== [왼쪽 화면: 미국 주식 장기 투자] ======
with col1:
    st.header("🇺🇸 미국 주식: 장기 배당 & 가치")
    st.subheader("🌍 글로벌 매크로 지표")
    
    m1, m2 = st.columns(2)
    try:
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        tnx = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]
        m1.metric("VIX (공포지수)", f"{vix:.2f}", "안정" if vix < 20 else "경계", delta_color="inverse")
        m2.metric("미 10년물 국채금리", f"{tnx:.2f}%")
    except:
        st.caption("매크로 지표 로딩 중...")
        
    st.markdown("---")
    st.subheader("보유 종목: JEPQ")
    
    my_shares = 130.837411
    try:
        jepq = yf.Ticker("JEPQ")
        current_price = jepq.history(period="1d")['Close'].iloc[-1]
        total_value = my_shares * current_price
        st.metric(label="내 JEPQ 총 평가 금액", value=f"${total_value:,.2f}")
    except:
        pass
    
    st.markdown("---")
    st.subheader("🧐 개별 기업 펀더멘털 & 뉴스")
    target_ticker = st.text_input("미국 주식 티커 입력 (예: AAPL, MSFT)", "AAPL").upper()
    
    if target_ticker:
        try:
            target_stock = yf.Ticker(target_ticker)
            info = target_stock.info
            
            roe = (info.get('returnOnEquity') or 0) * 100
            per = info.get('trailingPE') or 0
            
            s1, s2 = st.columns(2)
            s1.metric("ROE (>15% 합격)", f"{roe:.1f}%")
            s2.metric("PER (<20 합격)", f"{per:.1f}")
        except Exception:
            st.error("데이터를 찾을 수 없습니다.")

# ====== [오른쪽 화면: 국내 주식 단기 매매] ======
with col2:
    st.header("🇰🇷 국내 주식: 단타 Top 10 레이더")
    
    # 🚨 [기능 3] 타겟팅 알림: 내가 주시하는 종목 설정
    my_target = st.text_input("🚨 집중 감시할 단타 관심 종목 (예: SK하이닉스)", "SK하이닉스")
    
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
                name = cols[1].text.strip()
                volume = cols[5].text.strip()
                
                # 타겟 종목이 거래량 Top 10에 뜨면 사이렌 울리기!
                if name == my_target:
                    name = f"🚨 {name} (포착!)"
                    st.toast(f"[{my_target}] 거래량 폭발! Top 10 진입!", icon="🚨")
                    
                kr_data.append({"종목명": name, "당일 거래량": volume})
                if len(kr_data) == 10: break
                    
        if kr_data:
            df_kr = pd.DataFrame(kr_data)
            st.dataframe(df_kr, use_container_width=True, hide_index=True)
            st.caption("⏱️ 이 화면은 10초마다 자동으로 갱신됩니다. 아무것도 누르지 마세요!")
            
    except Exception as e:
        st.error(f"오류: {e}")