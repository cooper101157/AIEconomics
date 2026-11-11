import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai

# 1. 網頁頁面設定
st.set_page_config(page_title="Gemini CPI 與總經深度分析預測", layout="wide")
st.title("🌐 Gemini CPI 深度分析與總經預測儀表板")

# 2. 側邊欄設定
st.sidebar.header("⚙️ 設定與金鑰")
# 直接將您的 FRED API Key 帶入 value 中，老師打開網頁就會自動載入
fred_api_key = st.sidebar.text_input("請輸入 FRED API Key:", value="50eba7127681d7af46ea19dd3b4112005", type="password")
gemini_api_key = st.sidebar.text_input("請輸入 Gemini API Key (AI 分析用):", type="password")

st.sidebar.divider()
st.sidebar.header("📊 報告參數設定")
data_years = st.sidebar.selectbox("選擇歷史數據觀察範圍", ["近 3 年", "近 5 年", "近 10 年"], index=1)
start_year = "2023-01-01" if data_years == "近 3 年" else ("2021-01-01" if data_years == "近 5 年" else "2016-01-01")

# 3. 透過 FRED API 取得多維度經濟數據 (CPI, 核心 CPI, 失業率, 利率)
@st.cache_data
def load_economic_data(api_key, start_date):
    if not api_key:
        return None
    try:
        series_dict = {
            'CPI': 'CPIAUCSL',         # 消費者物價指數
            'Core_CPI': 'CPILFESL',    # 核心消費者物價指數
            'Unemployment': 'UNRATE',  # 失業率
            'Fed_Rate': 'FEDFUNDS'     # 聯邦基金利率
        }
        
        merged_df = pd.DataFrame()
        
        for name, series_id in series_dict.items():
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json"
            res = requests.get(url)
            data = res.json()
            
            if "observations" in data:
                df = pd.DataFrame(data["observations"])[['date', 'value']]
                df[name] = pd.to_numeric(df['value'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'])
                df = df.dropna().set_index('date')[[name]]
                
                if merged_df.empty:
                    merged_df = df
                else:
                    merged_df = merged_df.join(df, how='outer')
                    
        merged_df = merged_df[merged_df.index >= start_date].dropna()
        # 計算 CPI 與 核心 CPI 的年增率 (YoY)
        merged_df['CPI_YoY'] = merged_df['CPI'].pct_change(12) * 100
        merged_df['Core_CPI_YoY'] = merged_df['Core_CPI'].pct_change(12) * 100
        
        return merged_df
    except Exception as e:
        st.error(f"取得 FRED 總經數據失敗: {e}")
        return None

econ_df = load_economic_data(fred_api_key, start_year)

# 4. 主要內容與關鍵數據展示
if econ_df is not None and not econ_df.empty:
    latest = econ_df.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新 CPI 年增率", f"{latest.get('CPI_YoY', 0):.2f}%")
    col2.metric("最新核心 CPI 年增率", f"{latest.get('Core_CPI_YoY', 0):.2f}%")
    col3.metric("美國失業率", f"{latest.get('Unemployment', 0):.2f}%")
    col4.metric("聯邦基金利率", f"{latest.get('Fed_Rate', 0):.2f}%")

    st.subheader("📈 通膨指標走勢 (CPI YoY vs 核心 CPI YoY)")
    st.line_chart(econ_df[['CPI_YoY', 'Core_CPI_YoY']])

    st.subheader("📉 就業與利率環境聯動圖")
    st.line_chart(econ_df[['Unemployment', 'Fed_Rate']])
else:
    st.warning("請在左側側邊欄輸入有效的 FRED API Key 以載入完整總經與 CPI 數據。")

# 5. Gemini AI 深度總經與 CPI 預測報告區塊
st.divider()
st.subheader("🤖 Gemini 深度總經與 CPI 預測AI報告")

if st.button("生成全面 CPI 與總經分析報告"):
    if not gemini_api_key:
        st.error("請先輸入 Gemini API Key！")
    elif econ_df is None or econ_df.empty:
        st.error("缺少經濟數據，無法執行分析。")
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 提供最近 12 個月的豐富數據給 Gemini 進行深度分析
            recent_data = econ_df.tail(12).to_string()
            
            prompt = f"""你是一位頂尖的華爾街總體經濟學家與資深數據分析師。請根據以下包含美國最新 CPI、核心 CPI、失業率及聯邦基金利率的近一年數據：
{recent_data}

請產出一份結構完整、專業且豐富的深度總經分析報告，包含以下五大區塊：
1. **當前通膨情勢解讀**：深入分析總體 CPI 與核心 CPI 的最新表現與黏著度。
2. **就業市場與貨幣政策連動**：結合失業率與聯邦基金利率，評估當前利率水準對經濟與通膨的抑制效果。
3. **未來 3 至 6 個月 CPI 趨勢預測**：給出具體的通膨走勢預估與轉折點判斷。
4. **潛在風險因子**：列舉可能干擾通膨與經濟走勢的 3 個關鍵全球風險。
5. **資產配置與市場影響建議**：針對債券、股市與總經投資人提出專業的操作指引。"""
            
            with st.spinner("Gemini 正在調用多維度數據並撰寫深度經濟分析報告..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Gemini API 調用失敗: {e}")
