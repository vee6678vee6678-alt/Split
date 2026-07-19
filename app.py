import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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
st.subheader("ระบบแยกช่องตามค่าจริง + ดักจับแจ้งเตือน 'เวลากระโดด' (เวอร์ชันไฮไลต์สีฟ้าอ่อน คมชัดสูง)")

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

def parse_time_string(t_str):
    if pd.isna(t_str):
        return None
    t_str = str(t_str).replace('.', ':').strip()
    for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p'):
        try:
            return datetime.strptime(t_str, fmt)
        except ValueError:
            continue
    return None

try:
    with st.spinner(f"⏳ กำลังประมวลผลจัดเวลาและบีบช่องฟิตเปรี๊ยะ {selected_sheet} ..."):
        df = load_sheet_data(selected_sheet)
    
    if df.empty:
        st.warning(f"⚠️ ไม่พบข้อมูลในแผ่นงาน {selected_sheet} หรือแผ่นงานว่างเปล่า")
    else:
        # 3. ล็อกชื่อคอลัมน์และจัดเรียงแถวตามเวลาจริงเพื่อป้องกันบั๊กเวลากระโดด
        col_names = list(df.columns)
        col_names[0] = 'Col_A'
        col_names[1] = 'Col_B'
        col_names[2] = 'Time_Col_C'
        df.columns = col_names
        
        # จัดเรียงลำดับเวลาจริงให้ถูกต้องก่อนการคำนวณช่องว่างของเวลา
        df['time_object'] = df['Time_Col_C'].apply(parse_time_string)
        df = df.sort_values(by='time_object').reset_index(drop=True)
        df = df.drop(columns=['time_object'])
        
        base_cols = df.iloc[:, :3].copy()
        
        # 4. ลอจิกเช็ก "เวลากระโดด" จากตารางที่จัดเรียงเวลาเรียบร้อยแล้ว
        gap_indices = set()
        for idx in range(1, len(base_cols)):
            prev_time_obj = parse_time_string(base_cols.loc[idx-1, 'Time_Col_C'])
            curr_time_obj = parse_time_string(base_cols.loc[idx, 'Time_Col_C'])
            
            if prev_time_obj and curr_time_obj:
                time_diff = (curr_time_obj - prev_time_obj).total_seconds() / 60.0
                if time_diff < 0:
                    time_diff += 1440 
                
                # ถ้าห่างกันเกิน 30 นาที สั่งล็อกตำแหน่งแถวนั้นทันที
                if time_diff > 30.5: 
                    gap_indices.add(idx)

        # ดึงข้อมูลส่วนตัวเลขฝั่งขวามาจัดล็อกพิกัดตรงช่อง
        numeric_part = df.iloc[:, 3:].copy()
        all_nums = pd.to_numeric(numeric_part.values.flatten(), errors='coerce')
        all_nums = pd.Series(all_nums).dropna().round().astype(int)
        unique_sorted_nums = sorted(all_nums.unique())
        num_headers = [str(n) for n in unique_sorted_nums]
        
        processed_matrix = []
        for idx, row in numeric_part.iterrows():
            row_nums = pd.to_numeric(row, errors='coerce').dropna().round().astype(int).tolist()
            row_set = set(row_nums)
            
            new_row = []
            for n in unique_sorted_nums:
                if n in row_set:
                    new_row.append(n)
                else:
                    new_row.append("")
            processed_matrix.append(new_row)
            
        df_positioned_nums = pd.DataFrame(processed_matrix, columns=num_headers)
        final_df = pd.concat([base_cols, df_positioned_nums], axis=1)
        
        # 5. ระบบสีแยกประเภทกลุ่มตัวเลข
        colors = [
            '#FFD1DC', '#FFEEBB', '#D4F0F0', '#CCE2CB', '#FFCBC1', 
            '#E8AEB7', '#B5E2FA', '#EDF2F4', '#F9E5D8', '#E8D7F1',
            '#D8E2DC', '#FFE5D9', '#FFCAD4', '#F4ACB7', '#D8B4F8'
        ]
        
        color_map = {}
        for i, elem in enumerate(unique_sorted_nums):
            color_map[elem] = colors[i % len(colors)]
            
        # ฟังก์ชันระบายสีเงื่อนไขรายแถว
        def style_entire_table(row):
            styles = [''] * len(row)
            row_idx = row.name
            
            # ไฮไลต์คอลัมน์ C ด้วยสีฟ้าอ่อนเมื่อเวลากระโดด
            if row_idx in gap_indices:
                styles[2] = 'background-color: #E0F7FA; color: #006064; font-weight: bold; text-align: center;'
            else:
                styles[2] = 'text-align: center; color: #000000;'
                
            styles[0] = 'text-align: center; color: #000000;'
            styles[1] = 'text-align: center; color: #000000;'
            
            # แต้มสีฝั่งคอลัมน์ตัวเลขขวาตามประเภท
            for c_idx in range(3, len(row)):
                val = row.iloc[c_idx]
                if val != "" and pd.notna(val) and not isinstance(val, str):
                    val_int = int(val)
                    if val_int in color_map:
                        styles[c_idx] = f'background-color: {color_map[val_int]}; color: #000000; font-weight: bold; text-align: center;'
                    else:
                        styles[c_idx] = 'text-align: center; color: #000000;'
                else:
                    styles[c_idx] = 'text-align: center; color: #000000;'
                    
            return styles

        st.markdown(f"### 📋 แผ่นงาน: **{selected_sheet}** (จัดเรียงเวลาถูกต้อง + คอลัมน์ C สีฟ้าอ่อน = ตรวจพบเวลากระโดด)")
        
        # 🚨 แก้ไขจุดบั๊ก: รันระบบสไตล์แบบรวมศูนย์ผ่าน apply รายแถว (ไม่ต้องพึ่งพา .map() ซ้ำซ้อน)
        styled_df = final_df.style.apply(style_entire_table, axis=1)
        
        col_configurations = {}
        for header in num_headers:
            col_configurations[header] = st.column_config.Column(
                header,
                width=55,
                help=f"ช่องข้อมูลหมายเลข {header}"
            )
            
        st.dataframe(
            styled_df,
            height=650,
            use_container_width=False,
            column_config=col_configurations
        )
        
        st.success(f"✨ แก้ไขระบบเรนเดอร์ตารางเรียบร้อย หน้าตากระชับและไฮไลต์สีฟ้าอ่อนทำงานสมบูรณ์แบบครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลตาราง: {err}")
