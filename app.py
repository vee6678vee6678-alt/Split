
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
st.subheader("ระบบแยกช่องตามค่าตัวเลขจริง (ล็อกตำแหน่งตรงตามหัวคอลัมน์ ไม่ติดกัน)")

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
    with st.spinner(f"⏳ กำลังประมวลผลจัดล็อกพิกัดตัวเลขแผ่นงาน {selected_sheet} ..."):
        df = load_sheet_data(selected_sheet)
    
    if df.empty:
        st.warning(f"⚠️ ไม่พบข้อมูลในแผ่นงาน {selected_sheet} หรือแผ่นงานว่างเปล่า")
    else:
        # เก็บ 3 คอลัมน์แรกไว้คงที่ (Date, Time, Open/Close)
        base_cols = df.iloc[:, :3].copy()
        
        # ดึงข้อมูลส่วนที่เป็นตัวเลขฝั่งขวามาหาค่าตัวเลขทั้งหมดที่มีในชีทนี้
        numeric_part = df.iloc[:, 3:].copy()
        
        # กรองแปลงค่าให้เป็นตัวเลขจำนวนเต็ม และหาค่าที่ไม่ซ้ำ (Unique Numbers)
        all_nums = pd.to_numeric(numeric_part.values.flatten(), errors='coerce')
        all_nums = pd.Series(all_nums).dropna().round().astype(int)
        
        # นำตัวเลขทั้งหมดมาเรียงลำดับจากน้อยไปมาก เพื่อใช้ทำเป็นหัวคอลัมน์ดิ่งลงมา
        unique_sorted_nums = sorted(all_nums.unique())
        
        # แปลงเป็นข้อความเพื่อใช้เป็นชื่อหัวคอลัมน์ในตารางใหม่
        num_headers = [str(n) for n in unique_sorted_nums]
        
        # สร้างตารางเปล่า ๆ รอไว้สำหรับเติมตัวเลขให้ตรงช่อง
        processed_matrix = []
        
        # 3. ลอจิกการล็อกพิกัด: วิ่งดูทีละแถว ถ้าแถวนั้นมีเลขตรงกับหัวคอลัมน์ไหน ให้เอาเลขนั้นไปหยอดลงช่องนั้น
        for idx, row in numeric_part.iterrows():
            # ดึงเลขในแถวนั้นมาปัดเศษและทำเป็นเซ็ตเพื่อเช็กความไว
            row_nums = pd.to_numeric(row, errors='coerce').dropna().round().astype(int).tolist()
            row_set = set(row_nums)
            
            new_row = []
            for n in unique_sorted_nums:
                if n in row_set:
                    new_row.append(n) # ถ้าแถวนั้นมีเลขนี้ ให้ใส่เลขนี้ลงไปในช่อง
                else:
                    new_row.append("") # ถ้าไม่มี ให้ปล่อยเป็นช่องว่าง
            processed_matrix.append(new_row)
            
        # สร้าง DataFrame ส่วนตัวเลขตามพิกัดหัวข้อตัวเลขจริง
        df_positioned_nums = pd.DataFrame(processed_matrix, columns=num_headers)
        
        # รวมร่าง 3 คอลัมน์แรก เข้ากับตารางตัวเลขล็อกพิกัด
        final_df = pd.concat([base_cols, df_positioned_nums], axis=1)
        
        # 4. ระบบแต่งแต้มสีตามกลุ่มตัวเลข (เลขตัวเดียวกันดิ่งลงมาแถวไหนก็สีเดียวกันทั้งหมด)
        colors = [
            '#FFD1DC', '#FFEEBB', '#D4F0F0', '#CCE2CB', '#FFCBC1', 
            '#E8AEB7', '#B5E2FA', '#EDF2F4', '#F9E5D8', '#E8D7F1',
            '#D8E2DC', '#FFE5D9', '#FFCAD4', '#F4ACB7', '#D8B4F8'
        ]
        
        color_map = {}
        for i, elem in enumerate(unique_sorted_nums):
            color_map[elem] = colors[i % len(colors)]
            
        def style_cells(val):
            # ตรวจสอบว่าช่องนั้นไม่ใช่ช่องว่าง และมีค่าตรงในระบบสี
            if val != "" and pd.notna(val) and not isinstance(val, str):
                try:
                    val_int = int(val)
                    if val_int in color_map:
                        return f'background-color: {color_map[val_int]}; color: #000000; font-weight: bold; text-align: center;'
                except:
                    pass
            return 'text-align: center; color: #000000;'

        st.markdown(f"### 📋 แผ่นงาน: **{selected_sheet}** (ล็อกช่องตรงตามค่าหัวข้อตัวเลขอย่างแม่นยำ)")
        
        # บังคับระบายสีสไตล์เฉพาะช่องที่มีตัวเลข
        styled_df = final_df.style.map(style_cells, subset=num_headers)
        
        # แสดงตารางผลลัพธ์แบบคลีน ๆ ไม่มีทศนิยมกวนใจ
        st.dataframe(
            styled_df,
            height=650,
            use_container_width=True
        )
        
        st.success(f"✨ แยกช่องตรงหลักเรียบร้อย! หัวคอลัมน์รันตามค่าเลขจริง ตัวเลขจะล็อกตรงช่องของมันเองไม่ติดกันแล้วครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลตาราง: {err}")
