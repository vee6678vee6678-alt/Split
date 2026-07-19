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
    .header-box {
        background-color: #F8F9FA;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #00a087;
        margin-bottom: 15px;
        font-size: 18px !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Forex Multi-Sheet Data Processor")
st.subheader("ระบบดึงค่า Code/Date จากแถวแรก + จัดล็อกพิกัดข้อมูลเริ่มที่ Row 2")

# ลิงก์ตาราง Google Sheet แหล่งข้อมูลใหม่
spreadsheet_id = "1Zx94QQ6GZCRws59kWD_-VH_-ZIAK2-R6ihyXwxRjhA8"

# 2. เมนูด้านซ้าย (Sidebar) รองรับ Data1 - Data10
st.sidebar.markdown("## 📂 เลือกแผ่นงาน")
selected_sheet = st.sidebar.radio(
    "กรุณาเลือกหน้าข้อมูลที่ต้องการดู:",
    ["Data1", "Data2", "Data3", "Data4", "Data5", "Data6", "Data7", "Data8", "Data9", "Data10"]
)

@st.cache_data(ttl=5) # โหลดสดอัปเดตไวใน 5 วินาที
def load_sheet_data_raw(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    # ดึงแบบไม่ให้มีหัวตาราง เพื่อจับแถวที่ 1 และแถวที่ 2 แยกกันเองตามสั่ง
    df_raw = pd.read_csv(url, header=None)
    return df_raw

# ฟังก์ชันแปลงชื่อวันภาษาอังกฤษในตารางให้เป็นภาษาไทยที่ถูกต้องอิงตามปฏิทินจริง
def get_thai_day_name(date_str):
    if pd.isna(date_str) or str(date_str).strip() == "" or str(date_str).lower() == "nan":
        return "ไม่ระบุวันที่"
    try:
        d_cleaned = str(date_str).strip().replace('-', '/')
        for fmt in ('%d/%m/%Y', '%Y/%m/%d', '%d/%m/%y'):
            try:
                dt = datetime.strptime(d_cleaned, fmt)
                day_names = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
                return f"{dt.strftime('%d/%m/%Y')} {day_names[dt.weekday()]} "
            except ValueError:
                continue
        return str(date_str)
    except:
        return str(date_str)

try:
    with st.spinner(f"⏳ กำลังประมวลผลแยกโครงสร้างข้อมูล {selected_sheet} ..."):
        df_all = load_sheet_data_raw(selected_sheet)
    
    if df_all.empty:
        st.warning(f"⚠️ ไม่พบข้อมูลในแผ่นงาน {selected_sheet}")
    else:
        # 3. 🚨 ลอจิกขั้นเทพ ดึงค่า Code และ Date จากแถวแรกสุด (Row 1)
        row_one = df_all.iloc[0]
        
        # ช่อง B1 (index 1) คือค่า Code
        c_val = row_one.iloc[1] if len(row_one) > 1 else "ไม่มีข้อมูล"
        # ช่อง D1 (index 3) คือค่า Date
        d_val = row_one.iloc[3] if len(row_one) > 3 else "ไม่มีข้อมูล"
        
        # จัดรูปแบบข้อความตัวเลข Code
        if pd.notna(c_val) and str(c_val).strip() != "" and str(c_val).lower() != "nan":
            try:
                code_text = str(int(float(c_val)))
            except:
                code_text = str(c_val)
        else:
            code_text = "ไม่ระบุ"
            
        date_text = get_thai_day_name(d_val)

        # 🚨 โชว์ป้ายหัวข้อสวยงาม คมชัดสูง อ่านข้อมูลจากแถวแรกแม่นยำ 100%
        st.markdown(f"""
        <div class="header-box">
            📋 แผ่นงาน: {selected_sheet} &nbsp;&nbsp;|&nbsp;&nbsp; Code = {code_text} &nbsp;&nbsp;|&nbsp;&nbsp; Date = {date_text}
        </div>
        """, unsafe_allow_html=True)

        # 4. 🚨 ขยับเลื่อนตัดข้อมูลให้เริ่มอ่านตั้งแต่ แถวที่ 2 (Row 2) เป็นต้นไป
        df = df_all.iloc[1:].reset_index(drop=True)

        # ตั้งชื่อคอลัมน์มาตรฐานชั่วคราวให้ระบบทำงานต่อ
        col_names = ['Col_A', 'Col_B', 'Time_Col_C'] + [f'Raw_{i}' for i in range(df.shape[1] - 3)]
        df.columns = col_names
        
        # จัดเรียงลำดับเวลาในคอลัมน์ C จากน้อยไปมาก
        df['time_object'] = df['Time_Col_C'].apply(parse_time_string if 'parse_time_string' in locals() else lambda x: datetime.strptime(str(x).replace('.', ':').strip(), '%H:%M') if pd.notna(x) else None)
        df = df.sort_values(by='time_object').reset_index(drop=True)
        df = df.drop(columns=['time_object'])
        
        base_cols = df.iloc[:, :3].copy()
        
        # ลอจิกเช็กดักจับ "เวลากระโดด" ในคอลัมน์ C (ห่างเกิน 30 นาที)
        gap_indices = set()
        for idx in range(1, len(base_cols)):
            def quick_parse(t):
                if pd.isna(t): return None
                try: return datetime.strptime(str(t).replace('.', ':').strip(), '%H:%M')
                except: return None
            prev_time_obj = quick_parse(base_cols.loc[idx-1, 'Time_Col_C'])
            curr_time_obj = quick_parse(base_cols.loc[idx, 'Time_Col_C'])
            
            if prev_time_obj and curr_time_obj:
                time_diff = (curr_time_obj - prev_time_obj).total_seconds() / 60.0
                if time_diff < 0: time_diff += 1440
                if time_diff > 30.5: 
                    gap_indices.add(idx)

        # ดึงข้อมูลส่วนที่เป็นตัวเลขฝั่งขวามาจัดพิกัดลงล็อกหัวข้อจริง
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
        
        # 5. ระบบสีพาสเทลแยกกลุ่มตัวเลข
        colors = [
            '#FFD1DC', '#FFEEBB', '#D4F0F0', '#CCE2CB', '#FFCBC1', 
            '#E8AEB7', '#B5E2FA', '#EDF2F4', '#F9E5D8', '#E8D7F1',
            '#D8E2DC', '#FFE5D9', '#FFCAD4', '#F4ACB7', '#D8B4F8'
        ]
        
        color_map = {}
        for i, elem in enumerate(unique_sorted_nums):
            color_map[elem] = colors[i % len(colors)]
            
        def style_entire_table(row):
            styles = [''] * len(row)
            row_idx = row.name
            
            if row_idx in gap_indices:
                styles[2] = 'background-color: #E0F7FA; color: #006064; font-weight: bold; text-align: center;'
            else:
                styles[2] = 'text-align: center; color: #000000;'
                
            styles[0] = 'text-align: center; color: #000000;'
            styles[1] = 'text-align: center; color: #000000;'
            
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

        styled_df = final_df.style.apply(style_entire_table, axis=1)
        
        # ล็อกความกว้างช่องตัวเลขฝั่งขวาให้แคบและฟิตพอดีช่องละ 55 พิกเซล
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
        
        st.success(f"✨ สำเร็จ! อ่านหัวข้อแถว 1 และดึงตารางข้อมูลเริ่มที่ Row 2 เรียบร้อย สมบูรณ์แบบที่สุดครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลตาราง: {err}")
