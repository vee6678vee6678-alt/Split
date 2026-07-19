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
    /* ปรับแต่งตารางให้ดูง่ายและคมชัดบนมือถือ */
    .dataframe {
        font-size: 15px !important;
        font-family: sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Forex Multi-Sheet Data Processor")
st.subheader("ระบบแยกประเภท เรียงลำดับตัวเลขน้อย-มาก และเปลี่ยนหัวข้อเป็น 1-XX")

# ลิงก์ตาราง Google Sheet แหล่งข้อมูลใหม่
spreadsheet_id = "1Zx94QQ6GZCRws59kWD_-VH_-ZIAK2-R6ihyXwxRjhA8"

# 2. เมนูด้านซ้าย (Sidebar) ให้คลิกเลือกดูแผ่นงานทีละหน้า
st.sidebar.markdown("## 📂 เลือกแผ่นงาน")
selected_sheet = st.sidebar.radio(
    "กรุณาเลือกหน้าข้อมูลที่ต้องการดู:",
    ["Data1", "Data2", "Data3", "Data4", "Data5", "Data6", "Data7", "Data8", "Data9"]
)

@st.cache_data(ttl=60)
def load_sheet_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df_raw = pd.read_csv(url)
    return df_raw

try:
    with st.spinner(f"⏳ กำลังประมวลผลจัดเรียงตัวเลขแผ่นงาน {selected_sheet} ..."):
        df = load_sheet_data(selected_sheet)
    
    if df.empty:
        st.warning(f"⚠️ ไม่พบข้อมูลในแผ่นงาน {selected_sheet} หรือแผ่นงานว่างเปล่า")
    else:
        # เก็บ 3 คอลัมน์แรกไว้คงที่ (Date, Time, Open/Close)
        base_cols = df.iloc[:, :3].copy()
        
        # ดึงข้อมูลตัวเลขตั้งแต่คอลัมน์ที่ 4 เป็นต้นไป
        numeric_part = df.iloc[:, 3:].copy()
        
        processed_rows = []
        
        # 3. ลอจิกการปัดเศษ -> ลบค่าว่าง -> เรียงจากน้อยไปมากในแต่ละแถว
        for idx, row in numeric_part.iterrows():
            # แปลงเป็นตัวเลข, ปัดเศษเป็นจำนวนเต็ม (ไม่มีทศนิยม), และลบค่า NaN ออก
            valid_nums = pd.to_numeric(row, errors='coerce').dropna().round().astype(int).tolist()
            # จัดเรียงจากน้อยไปมาก
            valid_nums.sort()
            processed_rows.append(valid_nums)
            
        # สร้าง DataFrame ใหม่จากตัวเลขที่จัดเรียงแล้ว
        df_sorted_nums = pd.DataFrame(processed_rows)
        
        # 4. ตั้งชื่อหัวกระดาษเป็นลำดับตัวเลข 1, 2, 3, ... จนถึง XX
        new_headers = [str(i+1) for i in range(df_sorted_nums.shape[1])]
        df_sorted_nums.columns = new_headers
        
        # รวมร่างคอลัมน์หลัก A-C กับคอลัมน์ตัวเลขที่จัดระเบียบเรียบร้อยแล้ว
        final_df = pd.concat([base_cols, df_sorted_nums], axis=1)
        
        # 5. ระบบแต้มสีตามกลุ่มตัวเลข (ตัวเลขไหนเหมือนกันในหน้านั้น จะได้สีเดียวกัน)
        all_elements = df_sorted_nums.values.flatten()
        unique_elements = pd.Series(all_elements).dropna().unique()
        
        # ชุดสีพาสเทลคมชัด สบายสายตารุ่นใหญ่
        colors = [
            '#FFD1DC', '#FFEEBB', '#D4F0F0', '#CCE2CB', '#FFCBC1', 
            '#E8AEB7', '#B5E2FA', '#EDF2F4', '#F9E5D8', '#E8D7F1',
            '#D8E2DC', '#FFE5D9', '#FFCAD4', '#F4ACB7', '#D8B4F8'
        ]
        
        color_map = {}
        for i, elem in enumerate(unique_elements):
            color_map[elem] = colors[i % len(colors)]
            
        def style_cells(val):
            # ตรวจสอบและสไตล์เฉพาะช่องที่เป็นตัวเลขจำนวนเต็ม
            if pd.notna(val) and not isinstance(val, str):
                val_int = int(round(val))
                if val_int in color_map:
                    return f'background-color: {color_map[val_int]}; color: #000000; font-weight: bold; text-align: center;'
            return 'text-align: center; color: #000000;'

        st.markdown(f"### 📋 แผ่นงาน: **{selected_sheet}** (เรียงลำดับน้อย ➡️ มาก คมชัดสูง)")
        
        # บังคับระบายสีเฉพาะคอลัมน์ฝั่งขวา (1-XX)
        styled_df = final_df.style.map(style_cells, subset=new_headers)
        
        # ปรับการแสดงผลตารางให้เหมาะสม ไม่มีทศนิยม .0 กวนใจ
        st.dataframe(
            styled_df,
            height=650,
            use_container_width=True
        )
        
        st.success(f"✨ จัดเรียงช่องตัวเลขจากน้อยไปมาก และเปลี่ยนหัวข้อเป็น 1-{len(new_headers)} เรียบร้อย สวยงามครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลตาราง: {err}")
