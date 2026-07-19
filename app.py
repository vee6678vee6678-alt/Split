import streamlit as st
import pandas as pd
import numpy as np

# 1. ตั้งค่าหน้าเว็บกว้างเต็มจอและปรับสไตล์ธีมสว่าง คมชัดสูง
st.set_page_config(layout="wide", page_title="Forex Multi-Sheet Analyzer")

st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    h1, h2, h3, p, span, label {
        color: #000000 !important;
        font-weight: bold !important;
    }
    /* ปรับแต่งตารางให้ดูง่ายบนมือถือ */
    .dataframe {
        font-size: 14px !important;
        font-family: sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Forex Multi-Sheet Data Processor")
st.subheader("ระบบแยกประเภทและแต้มสีข้อมูลอัตโนมัติ แผ่นงาน Data1 - Data9")

# ลิงก์ตาราง Google Sheet แหล่งข้อมูลใหม่ที่คุณวีรพันธ์ส่งมา
spreadsheet_id = "1Zx94QQ6GZCRws59kWD_-VH_-ZIAK2-R6ihyXwxRjhA8"

# 2. สร้างเมนูด้านซ้าย (Sidebar) ให้คลิกเลือกดูแผ่นงานทีละหน้าได้ง่ายๆ
st.sidebar.markdown("## 📂 เลือกแผ่นงาน")
selected_sheet = st.sidebar.radio(
    "กรุณาเลือกหน้าข้อมูลที่ต้องการดู:",
    ["Data1", "Data2", "Data3", "Data4", "Data5", "Data6", "Data7", "Data8", "Data9"]
)

@st.cache_data(ttl=60)  # ระบบจำค่าช่วยให้โหลดหน้าเปลี่ยนชีทได้เร็วขึ้นใน 1 วินาที
def load_sheet_data(sheet_name):
    # เปลี่ยนลิงก์ให้ดึงข้อมูลแยกตามชื่อชีทที่กดเลือก
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df_raw = pd.read_csv(url)
    return df_raw

try:
    with st.spinner(f"⏳ กำลังสายตรงดึงข้อมูลสดจากแผ่นงาน {selected_sheet} ..."):
        df = load_sheet_data(selected_sheet)
    
    if df.empty:
        st.warning(f"⚠️ ไม่พบข้อมูลในแผ่นงาน {selected_sheet} หรือแผ่นงานว่างเปล่า")
    else:
        # 3. ลอจิกการสร้างจานสี (Color Palette) เพื่อแต้มสีตัวเลขที่ซ้ำกัน
        # ดึงตัวเลขทั้งหมดตั้งแต่คอลัมน์ที่ 4 เป็นต้นไป (Column D ถึงคอลัมน์สุดท้าย) มาหาค่าที่ไม่ซ้ำ
        numeric_cols = df.columns[3:]
        all_elements = df[numeric_cols].values.flatten()
        # กรองเอาเฉพาะข้อมูลที่ไม่ใช่ค่าว่างหรือ NaN
        unique_elements = pd.Series(all_elements).dropna().unique()
        
        # สร้างเฉดสีพาสเทลจางๆ สบายตา ไม่ฉูดฉาด เพื่อให้คุณวีรพันธ์อ่านตัวหนังสือสีดำข้างในได้ชัดๆ
        colors = [
            '#FFD1DC', '#FFEEBB', '#D4F0F0', '#CCE2CB', '#FFCBC1', 
            '#E8AEB7', '#B5E2FA', '#EDF2F4', '#F9E5D8', '#E8D7F1',
            '#D8E2DC', '#FFE5D9', '#FFCAD4', '#F4ACB7', '#D8B4F8'
        ]
        
        # จับคู่ตัวเลขกับสี (ถ้าตัวเลขเหมือนกันจะได้สีเดียวกัน)
        color_map = {}
        for i, elem in enumerate(unique_elements):
            color_map[elem] = colors[i % len(colors)]
            
        # ฟังก์ชันสไตล์ลิ่งเพื่อระบายสีลงช่องตารางในฝั่งขวา
        def style_cells(val):
            if val in color_map:
                return f'background-color: {color_map[val]}; color: #000000; font-weight: bold; text-align: center;'
            return 'text-align: center; color: #000000;'

        st.markdown(f"### 📋 แสดงผลข้อมูลแผ่นงาน: **{selected_sheet}** (คอลัมน์ A-C ล็อกอยู่กับที่)")
        
        # 4. เรนเดอร์แสดงผลตารางแบบพรีเมียม คมชัดสูง ปรับสีแยกประเภทตามเงื่อนไข
        styled_df = df.style.applymap(style_cells, subset=numeric_cols)
        
        # แสดงตารางบนแดชบอร์ด ขยายเต็มหน้าจอ
        st.dataframe(
            styled_df,
            height=650,
            use_container_width=True
        )
        
        st.success(f"✨ ประมวลผลและแยกประเภทตัวเลขด้วยสีของหน้า {selected_sheet} เรียบร้อยแล้วครับ!")

except Exception as err:
    st.error(f"❌ ระบบไม่สามารถเข้าถึงแผ่นงานได้: {err}")
    st.info("💡 คำแนะนำ: ตรวจสอบให้แน่ใจว่าได้เปิดแชร์ลิงก์ Google Sheet นี้เป็น 'ทุกคนที่มีลิงก์มีสิทธิ์อ่าน' (Anyone with the link can view) เรียบร้อยแล้วในตั้งค่าของ Google Drive ครับ")
