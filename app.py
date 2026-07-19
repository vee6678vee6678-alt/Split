import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
st.subheader("ระบบแยกช่องตามค่าจริง + ดักจับแจ้งเตือน 'เวลากระโดด' ในคอลัมน์ C อัตโนมัติ")

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

# ฟังก์ชันแปลงข้อความเวลา (เช่น 7:30, 07.30, 10:00) ให้เป็นออบเจกต์เวลาเพื่อใช้คำนวณคำนวณค่าต่าง
def parse_time_string(t_str):
    if pd.isna(t_str):
        return None
    t_str = str(t_str).replace('.', ':').strip() # เปลี่ยนจุดเป็นทวิภาคให้เป็นรูปแบบสากล
    for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p'):
        try:
            return datetime.strptime(t_str, fmt)
        except ValueError:
            continue
    return None

try:
    with st.spinner(f"⏳ กำลังประมวลผลจัดล็อกพิกัดและตรวจสอบเวลากระโดด {selected_sheet} ..."):
        df = load_sheet_data(selected_sheet)
    
    if df.empty:
        st.warning(f"⚠️ ไม่พบข้อมูลในแผ่นงาน {selected_sheet} หรือแผ่นงานว่างเปล่า")
    else:
        # เก็บ 3 คอลัมน์แรกไว้คงที่ (Date, Time, Open/Close)
        # ตั้งชื่อคอลัมน์แรก ๆ ให้ชัดเจนเพื่อง่ายต่อการอ้างอิง
        col_names = list(df.columns)
        col_names[0] = 'Col_A'
        col_names[1] = 'Col_B'
        col_names[2] = 'Time_Col_C' # ล็อกชื่อคอลัมน์ C ว่าเป็นคอลัมน์เวลา
        df.columns = col_names
        
        base_cols = df.iloc[:, :3].copy()
        
        # 3. ลоจิกคำนวณตรวจสอบ "เวลากระโดด" ในคอลัมน์ C
        gap_indices = set() # เก็บตำแหน่งแถวที่เวลาโดด
        
        for idx in range(1, len(base_cols)):
            prev_time_obj = parse_time_string(base_cols.loc[idx-1, 'Time_Col_C'])
            curr_time_obj = parse_time_string(base_cols.loc[idx, 'Time_Col_C'])
            
            if prev_time_obj and curr_time_obj:
                # คำนวณความต่างของเวลาเป็นนาที
                time_diff = (curr_time_obj - prev_time_obj).total_seconds() / 60.0
                
                # ถ้าข้ามวันเวลาอาจติดลบ ให้บวกกลับ 24 ชั่วโมง
                if time_diff < 0:
                    time_diff += 1440 
                
                # ถ้าเวลาห่างกันมากกว่า 30 นาที แสดงว่า "เวลากระโดด" เด้งล็อกตำแหน่งทันที
                if time_diff > 30.5: 
                    gap_indices.add(idx)

        # ดึงข้อมูลส่วนที่เป็นตัวเลขฝั่งขวามาหาค่าตัวเลขทั้งหมดที่มีในชีทนี้
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
        
        # รวมร่าง 3 คอลัมน์แรก เข้ากับตารางตัวเลขล็อกพิกัด
        final_df = pd.concat([base_cols, df_positioned_nums], axis=1)
        
        # 4. ระบบแต่งแต้มสีแยกแยะ
        colors = [
            '#FFD1DC', '#FFEEBB', '#D4F0F0', '#CCE2CB', '#FFCBC1', 
            '#E8AEB7', '#B5E2FA', '#EDF2F4', '#F9E5D8', '#E8D7F1',
            '#D8E2DC', '#FFE5D9', '#FFCAD4', '#F4ACB7', '#D8B4F8'
        ]
        
        color_map = {}
        for i, elem in enumerate(unique_sorted_nums):
            color_map[elem] = colors[i % len(colors)]
            
        # ฟังก์ชันหลักในการพ่นสีลงตารางแบบผสมเงื่อนไข
        def style_entire_table(row):
            styles = [''] * len(row)
            row_idx = row.name
            
            # เงื่อนไขที่ 1: ตรวจเช็กคอลัมน์ C (ดัชนีตำแหน่งที่ 2) ถ้าเวลากระโดด ให้พ่นสีแดงชมพูเด่นๆ แจ้งเตือน
            if row_idx in gap_indices:
                styles[2] = 'background-color: #FFB3BA; color: #D32F2F; font-weight: bold; text-align: center;'
            else:
                styles[2] = 'text-align: center; color: #000000;'
                
            # สไตล์คอลัมน์ A และ B ให้ตรงกลางสวยงามปกติ
            styles[0] = 'text-align: center; color: #000000;'
            styles[1] = 'text-align: center; color: #000000;'
            
            # เงื่อนไขที่ 2: แต้มสีคอลัมน์ตัวเลขฝั่งขวาตามกลุ่มประเภท
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

        st.markdown(f"### 📋 แผ่นงาน: **{selected_sheet}** (คอลัมน์ C สีชมพูแดง = ตรวจพบเวลากระโดดข้ามช่อง)")
        
        # เปิดใช้งานการตรวจสอบระบายสีแบบรายแถว (axis=1)
        styled_df = final_df.style.apply(style_entire_table, axis=1)
        
        # ล็อกความกว้างช่องตัวเลขฝั่งขวาให้กระชับ
        col_configurations = {}
        for header in num_headers:
            col_configurations[header] = st.column_config.Column(
                header,
                width=55,
                help=f"ช่องข้อมูลหมายเลข {header}"
            )
            
        # แสดงผลตารางแบบบีบช่องฟิตเปรี๊ยะ ไม่ยืดขยายขวาเอง
        st.dataframe(
            styled_df,
            height=650,
            use_container_width=False,
            column_config=col_configurations
        )
        
        st.success(f"✨ เปิดระบบดักจับเวลากระโดดในหน้า {selected_sheet} เรียบร้อย! หากมีการข้ามช่วงเวลา ช่องนั้นจะไฮไลต์เตือนภัยให้ทันทีครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลตาราง: {err}")
