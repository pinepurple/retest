#後臺處理的相關函數

import streamlit as st
import pandas as pd
import googlesheet_process as gp
import gspread
import time
import io

def upload_retest_list_page():
    st.title("上傳補考名單")
    gc_client = gp.get_gspread_client()
    st.info("請上傳補考名單的 Excel 檔案，檔案格式必須為 .xlsx。")

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input', index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    grade = st.session_state.get("grade_input")
    uploaded_file = st.file_uploader("選擇一個 .xlsx 檔案", type=["xlsx"], key='upload_retest_excel_uploader')

    if st.button("確認上傳", key="upload_retest"):
        if uploaded_file is None:
            st.info("請先上傳一個 Excel 檔案。")
            return False
        try:
            try: # 嘗試讀取 Excel 文件，明確指定引擎和工作表
                    df = pd.read_excel(uploaded_file, engine='openpyxl', sheet_name=grade)
            except FileNotFoundError:
                st.error("上傳失敗：找不到指定的 Excel 檔案。")
                return False
            except pd.errors.EmptyDataError:
                st.error("上傳失敗：Excel 檔案為空。")
                return False
            except pd.errors.ParserError:
                st.error("上傳失敗：無法解析 Excel 檔案。請確認檔案格式正確。")
                st.exception(e)
                return False
            except ValueError:
                st.error("上傳失敗：請確認工作表名稱為 1 、2 、 3。")
                return False
            except Exception as e:
                st.error(f"讀取 Excel 檔案時發生未預期的錯誤：{e}")
                st.exception(e)
                return False

            expected_columns = ["班級", "座號", "科目", "必選修", "成績"] # 定義預期欄位，用於數據驗證
            if not all(col in df.columns for col in expected_columns): # 驗證 Excel 檔案是否包含所有必要的欄位
                missing_cols = [col for col in expected_columns if col not in df.columns]
                st.error(f"上傳失敗：Excel 檔案缺少必要的欄位。缺少欄位：{', '.join(missing_cols)}")
                st.warning(f"請確保檔案包含所有預期欄位：{', '.join(expected_columns)}")
                return False

            try: # 獲取目標工作表
                worksheet = gp.get_google_sheet_worksheet(gc_client, "補考名單", grade)
            except Exception as e:
                st.error(f"無法取得 Google Sheet 工作表 '補考名單 - {grade}'，請確認試算表名稱和工作表名稱是否正確，或服務帳戶權限。")
                st.exception(e)
                return False

            status_message_placeholder = st.empty()
            status_message_placeholder.info(f"正在清空 {grade} 年級補考名單並上傳資料中...")
        
            try: # 清空現有資料
                worksheet.clear()
            except gspread.exceptions.APIError as e:
                status_message_placeholder.error(f"清空 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。")
                st.exception(e)
                return False
            except Exception as e:
                status_message_placeholder.error(f"清空 Google Sheet 時發生未預期的錯誤：{e}。")
                st.exception(e)
                return False

            # 將 DataFrame 轉換為列表的列表 (包含標頭行)，以便 gspread 進行更新
            data_to_upload = [df.columns.tolist()] + df.values.tolist()
            try:
                worksheet.update(values=data_to_upload)
                status_message_placeholder.success(f"{grade} 年級補考名單已成功更新！共上傳 {len(df)} 筆資料。")
                time.sleep(2)
                st.rerun()
            except gspread.exceptions.APIError as e:
                status_message_placeholder.error(f"更新 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。")
                st.exception(e)
                return False
            except Exception as e:
                status_message_placeholder.error(f"更新 Google Sheet 時發生未預期的錯誤：{e}")
                st.exception(e)
                return False

        except Exception as e:
            st.error(f"上傳補考名單時發生錯誤：{e}")
            st.exception(e)
            return False
    display_cloud_data(grade,sheet_name="補考名單")

def clear_retest_list_page():
    st.title("清空補考名單")
    gc_client = gp.get_gspread_client()

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input', index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    grade = st.session_state.get("grade_input")

    try:
        try: # 獲取目標工作表
            worksheet = gp.get_google_sheet_worksheet(gc_client, "補考名單", grade)
        except Exception as e:
            st.error(f"無法取得 Google Sheet 工作表 '補考名單 - {grade}'，請確認試算表名稱和工作表名稱是否正確，或服務帳戶權限。")
            st.exception(e)
            return False

        if st.button(f"確認清空 {grade} 年級補考名單", key=f"clear_btn_{grade}"):
            try:
                all_data = worksheet.get_all_values() # 獲取所有資料，包括標題列，以判斷範圍                
                if not all_data or len(all_data) <= 1: # 如果工作表為空或只有標題列，則無需清空
                    st.info(f"{grade} 年級補考名單目前沒有資料需要清空 (只有標題或為空)。")
                    return True

                header_row = all_data[0]
                num_cols = len(header_row) # 根據標題列的長度來決定要清空的欄位數
                last_row_with_data = len(all_data) # 確定實際有資料的最後一行 (包含標題)                
                start_cell_a1 = gspread.utils.rowcol_to_a1(2, 1) # 定義要清空的範圍(A2)
                end_cell_a1 = gspread.utils.rowcol_to_a1(last_row_with_data, num_cols)
                range_to_clear = f"{start_cell_a1}:{end_cell_a1}"
                rows_to_clear_count = last_row_with_data - 1 # 建立一個空的二維列表來填充該範圍
                empty_data_to_fill = [[''] * num_cols for _ in range(rows_to_clear_count)]
                worksheet.update(values=empty_data_to_fill, range_name=range_to_clear)
                st.success(f"{grade} 年級補考名單中的資料已成功清空。")
                time.sleep(2)
                st.rerun()

            except gspread.exceptions.APIError as e:
                st.error(f"清空 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。")
                st.exception(e)
                return False

            except Exception as e:
                st.error(f"清空 Google Sheet 時發生未預期的錯誤：{e}。")
                st.exception(e)
                return False
    except Exception as e:
        st.error(f"清空補考名單時發生錯誤：{e}")
        st.exception(e)
        return False
    display_cloud_data(grade,sheet_name="補考名單")

    return False # 按鈕未被點擊時返回 False

def home_page():
    st.title("後臺管理系統：首頁")
    st.subheader("歡迎，管理員！")

    st.header("管理功能")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("上傳補考名單", key="nav_upload_retest", use_container_width=True):
            st.session_state['current_page'] = 'upload_retest_list'
            st.rerun()
    with col2:
        if st.button("下載補考者報名資料", key="nav_download_registrants", use_container_width=True):
            st.session_state['current_page'] = 'download_registrants_data'
            st.rerun()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("清空補考名單", key="nav_claen_registrants", use_container_width=True):
            st.session_state['current_page'] = 'sidebar_claen_registrants'
            st.rerun()
    with col4:
        if st.button("生成補考考生座位表", key="nav_retest_seat", use_container_width=True):
            st.session_state['current_page'] = 'retest_seat'
            st.rerun()

    st.markdown("---")
    st.header("查看雲端資料")

    # 選擇查看資料的年級
    if 'selected_view_type' not in st.session_state:
        st.session_state['selected_view_type'] = 'retest_list' # 預設顯示補考名單
    if 'selected_view_grade' not in st.session_state:
        st.session_state['selected_view_grade'] = "1"

    view_grade = st.selectbox('選擇查看年級', options=["1", "2", "3"], key='view_data_grade_select', index=0)
    if st.session_state.get('view_data_grade_select') != st.session_state['selected_view_grade']: # 如果 selectbox 的值改變了，更新 session state 並觸發重新渲染
        st.session_state['selected_view_grade'] = st.session_state.get('view_data_grade_select')
        st.rerun() # 重新渲染以顯示新的年級資料

    col5, col6 = st.columns(2)
    with col5:
        if st.button(f"查看 {view_grade} 年級補考名單", key=f"view_retest_list_btn_{view_grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'retest_list' # 設定為查看補考名單
            st.rerun() 
    with col6:
        if st.button(f"查看 {view_grade} 年級補考者報名資料", key=f"view_registrants_data_btn_{view_grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'registrants_data' # 設定為查看報名資料
            st.rerun()

    if st.session_state['selected_view_type'] == 'retest_list': sheet_to_view = "補考名單"
    else: sheet_to_view = "補考者報名資料"
    display_cloud_data(st.session_state['selected_view_grade'],sheet_to_view)

    st.markdown("---")
    col7, col8 = st.columns(2)
    with col7:
        if st.button("更改帳號密碼", key="nav_change_password", use_container_width=True):
            st.session_state['current_page'] = 'change_password'
            st.rerun()
    with col8:
        if st.button("登出系統", key="logout_button", use_container_width=True):
            st.session_state['admin_logged_in'] = False
            st.session_state['current_page'] = 'login' # 重設頁面到登入頁
            st.info("您已登出。")
            time.sleep(1) # 短暫延遲讓訊息顯示
            st.rerun()

def download_retest_registrants_data_page():
    st.title("下載補考者報名資料")
    registrants_spreadsheet_name = "補考者報名資料"
    gc_client = gp.get_gspread_client()

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        download_grade = st.selectbox('選擇下載年級', options=["1", "2", "3"], key='download_grade_select', index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    try:
        info = st.info(f"正在從 Google Sheet 獲取 {download_grade} 年級補考者報名資料...")
        registrants_worksheet = gp.get_google_sheet_worksheet(gc_client, registrants_spreadsheet_name, download_grade)
        data = registrants_worksheet.get_all_values()
        info.empty()

        if data:
            df_registrants = pd.DataFrame(data[1:], columns=data[0]) # 將第一行作為欄位名稱，其餘作為資料
            st.dataframe(df_registrants)
            # 提供下載按鈕
            col3, col4 = st.columns([1, 1], gap="small")
            with col3:
                csv_data = df_registrants.to_csv(index=False).encode('utf-8-sig') # utf-8-sig 支援中文，Excel 可直接開啟
                st.download_button(
                    label=f"下載 {download_grade} 年級補考者報名資料 (CSV)",
                    data=csv_data,
                    file_name=f"補考者報名資料_{download_grade}年級.csv",
                    mime="text/csv",
                    key=f"download_csv_btn_{download_grade}",
                    use_container_width=True
                )
            with col4:
                output = io.BytesIO()
                
                # 使用 ExcelWriter 將 DataFrame 寫入記憶體中的 Excel 檔案
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_registrants.to_excel(writer, index=False, sheet_name=f"{download_grade}年級報名資料")
                xlsx_data = output.getvalue()
                
                st.download_button(
                    label=f"下載 {download_grade} 年級補考者報名資料 (xlsx)",
                    data=xlsx_data,
                    file_name=f"補考者報名資料_{download_grade}年級.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", # Excel 的 MIME 類型
                    key=f"download_xlsx_btn_{download_grade}",
                    use_container_width=True
                )
        else:
            st.warning(f"{download_grade} 年級補考者報名資料中沒有找到資料。")

    except Exception as e:
        st.error(f"下載 {download_grade} 年級補考者報名資料時發生錯誤：{e}")
        st.exception(e)
    st.info("1. 下載的檔案會儲存在本地端的預設下載資料夾中。\n2. 檔案內的時間欄位若為井字號，請將該欄拉寬便能正常顯示。")

def display_cloud_data(view_grade,sheet_name="補考名單"):
    gc_client = gp.get_gspread_client()

    try:
        info = st.info(f"正在從 Google Sheet 獲取 {view_grade} 年級{sheet_name}")
        worksheet = gp.get_google_sheet_worksheet(gc_client, sheet_name, view_grade)
        data = worksheet.get_all_values()
        info.empty()

        if data:
            df_retest = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df_retest)
        else:
            st.warning(f"{view_grade} 年級{sheet_name}中沒有找到資料。")
    except Exception as e:
        st.error(f"查看 {view_grade} 年級{sheet_name}時發生錯誤：{e}")
        st.exception(e)

def retest_seat():
    st.title("生成補考考生座位表")
    gc_client = gp.get_gspread_client()

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        grade = st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input')
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    display_cloud_data(grade,sheet_name="補考者報名資料")