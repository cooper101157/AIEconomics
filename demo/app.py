import streamlit as st
import pandas as pd
from pandas_datareader import data as pdr
import google.generativeai as genai

# 1. 網頁頁面設定
st.set_page_config(page_title="Gemini CPI 分析與預測", layout="wide")
st.title("🌐 Gemini CPI 分析與預測儀表板")

# 2. 側邊欄設定
st.sidebar.header("⚙️ 設定與金鑰")
fred_api_key = st.sidebar.text_input("請輸入 FRED API Key:", type="password")
gemini_api_key = st.sidebar.text_input("請輸入 Gemini API Key (CPI 分析用):", type="password")

# 3. FRED CPI 數據擷取
@st.cache_data
def load_cpi_data(api_key):
    if not api_key:
        return None
    try:
        df = pdr.DataReader('CPIAUCSL', 'fred', start='2015-01-01', api_key=api_key)
        df.columns = ['CPI']
        df['YoY_Change'] = df['CPI'].pct_change(12) * 100
        return df
    except Exception as e:
        st.error(f"取得 FRED 數據失敗: {e}")
        return None

cpi_df = load_cpi_data(fred_api_key)

# 4. 主要內容與關鍵數據展示
if cpi_df is not None:
    latest_cpi = cpi_df['CPI'].iloc[-1]
    latest_yoy = cpi_df['YoY_Change'].iloc[-1]
    
    col1, col2 = st.columns(2)
    col1.metric("最新 CPI 物價指數", f"{latest_cpi:.2f}")
    col2.metric("CPI 通膨年增率 (YoY)", f"{latest_yoy:.2f}%")

    st.subheader("📈 歷史 CPI 走勢與通膨變化")
    st.line_chart(cpi_df[['CPI', 'YoY_Change']])
else:
    st.warning("請在左側側邊欄輸入有效的 FRED API Key 以載入最新 CPI 數據。")

# 5. Gemini AI CPI 分析與預測區塊
st.divider()
st.subheader("🤖 Gemini CPI 分析與未來的趨勢預測")

if st.button("執行 Gemini CPI 智能分析"):
    if not gemini_api_key:
        st.error("請先輸入 Gemini API Key！")
    elif cpi_df is None:
        st.error("缺少 CPI 數據，無法執行分析。")
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            recent_data = cpi_df.tail(6).to_string()
            
            # 確保這裡的三重引號完整包覆
            prompt = f"""你是一位專業的總體經濟分析師。請根據以下最新的美國 CPI 數據：
{recent_data}

請提供以下詳細分析報告：
1. 當前 CPI 通膨趨勢解讀
2. 對央行貨幣政策的潛在影響
3. 未來 3 至 6 個月的 CPI 趨勢預測與主要風險因子"""
            
            with st.spinner("Gemini 正在分析 CPI 數據與預測趨勢..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Gemini API 調用失敗: {e}")
