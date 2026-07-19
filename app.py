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
st.subheader("ระบบแยกช่องตามค่าจริง + ดักจับแจ้งเตือน 'เวลากระโดด' พร้อมแสดง Code และวันที่")

# ลิงก์ตาราง Google Sheet แหล่งข้อมูลใหม่
spreadsheet_id = "1Zx94QQ6GZCRws59kWD_-VH_-ZIAK2-R6ihyXwxRjhA8"

# 2. เมนูด้านซ้าย (Sidebar) ขยายหน้าเมนูรองรับ Data1 - Data10 ตามสั่ง
st.sidebar.markdown("## 📂 เลือกแผ่นงาน")
selected_sheet = st.sidebar.radio(
    "กรุณาเลือกหน้าข้อมูลที่ต้องการดู:",
    ["Data1", "Data2", "Data3", "Data4", "Data5", "Data6", "Data7", "Data8", "Data9", "Data10"]
)

# ฟังก์ชันดึงข้อมูลสดจากแผ่นงานข้อมูล
@st.cache_data(ttl=60)
def load_sheet_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df_raw = pd.read_csv(url, header=None)
    return df_raw

# ฟังก์ชันดึงข้อมูลสดจากชีทชื่อ "Code" เพื่อเอามาทำหัวตาราง
@st.cache_data(ttl=60)
def load_code_sheet():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet=Code"
        df_code = pd.read_csv(url)
        return df_code
    except:
        return None

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

# ฟังก์ชันแปลงชื่อวันภาษาอังกฤษให้เป็นภาษาไทยสวย ๆ
def get_thai_day_name(date_str):
    try:
        # รองรับรูปแบบวันที่หลากหลายจาก Google Sheet
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                dt = datetime.strptime(str(date_str).strip(), fmt)
                day_names = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
                return f"{dt.strftime('%d/%m/%Y')} {day_names[dt.weekday()]} "
            except ValueError:
                continue
        return str(date_str)
    except:
        return str(date_str)

try:
    with st.spinner(f"⏳ กำลังประมวลผลข้อมูลสดแผ่นงาน {selected_sheet} ..."):
        df = load_sheet_data(selected_sheet)
        df_code_info = load_code_sheet()
    
    if df.empty:
        st.warning(f"⚠️ ไม่พบข้อมูลในแผ่นงาน {selected_sheet} หรือแผ่นงานว่างเปล่า")
    else:
        # 3. ลอจิกการดึงและสร้างข้อความหัวตาราง (Code & Date Header)
        code_text = "ไม่พบข้อมูล"
        date_text = "ไม่พบข้อมูล"
        
        if df_code_info is not None and not df_code_info.empty:
            # ปรับหัวตารางชีท Code ให้เป็นพิมพ์เล็ก-ใหญ่ตามมาตรฐานเพื่อง่ายต่อการค้นหา
            df_code_info.columns = [str(c).strip().lower() for c in df_code_info.columns]
            
            # ค้นหาแถวที่คอลัมน์แรกระบุชื่อแผ่นงานตรงกับที่เลือก (เช่น data1, data2)
            sheet_keyword = selected_sheet.lower()
            match_row = df_code_info[df_code_info.iloc[:, 0].astype(str).str.strip().str.lower() == sheet_keyword]
            
            if not match_row.empty:
                # ดึงค่าจากคอลัมน์ code และ date (ถ้าไม่มีให้เช็กจากตำแหน่งคอลัมน์ที่ 2 และ 3 แทน)
                c_val = match_row['code'].values[0] if 'code' in match_row.columns else match_row.iloc[0, 1]
                d_val = match_row['date'].values[0] if 'date' in match_row.columns else match_row.iloc[0, 2]
                
                code_text = str(int(float(c_val))) if pd.notna(c_val) and isinstance(c_val, (int, float)) else str(c_val)
                date_text = get_thai_day_name(d_val)

        # 🚨 จุดโชว์ผลลัพธ์ความงามบนหัวตารางตามสั่งเป๊ะ ๆ
        st.markdown(f"""
        <div class="header-box">
            📋 แผ่นงาน: {selected_sheet} &nbsp;&nbsp;|&nbsp;&nbsp; Code = {code_text} &nbsp;&nbsp;|&nbsp;&nbsp; Date = {date_text}
        </div>
        """, unsafe_allow_html=True)

        # 4. กำหนดชื่อคอลัมน์มาตรฐานชั่วคราวให้ระบบนำไปทำงานต่อ
        col_names = ['Col_A', 'Col_B', 'Time_Col_C'] + [f'Raw_{i}' for i in range(df.shape[1] - 3)]
        df.columns = col_names
        
        # จัดเรียงลำดับเวลาในคอลัมน์ C จากน้อยไปมาก
        df['time_object'] = df['Time_Col_C'].apply(parse_time_string)
        df = df.sort_values(by='time_object').reset_index(drop=True)
        df = df.drop(columns=['time_object'])
        
        base_cols = df.iloc[:, :3].copy()
        
        # ลอจิกเช็กดักจับ "เวลากระโดด" ในคอลัมน์ C (ห่างเกิน 30 นาที)
        gap_indices = set()
        for idx in range(1, len(base_cols)):
            prev_time_obj = parse_time_string(base_cols.loc[idx-1, 'Time_Col_C'])
            curr_time_obj = parse_time_string(base_cols.loc[idx, 'Time_Col_C'])
            
            if prev_time_obj and curr_time_obj:
                time_diff = (curr_time_obj - prev_time_obj).total_seconds() / 60.0
                if time_diff < 0:
                    time_diff += 1440 
                
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
            
            # แต้มสีฟ้าอ่อนพาสเทลเมื่อตรวจเจอเวลากระโดดข้ามช่วง
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

        # รันระบบสีผ่าน apply รายแถว
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
        
        st.success(f"✨ ซิงค์ข้อมูลกับชีท Code และอัปเดตหัวกระดาษของหน้า {selected_sheet} สวยงาม เรียบร้อยครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลตาราง: {err}")
