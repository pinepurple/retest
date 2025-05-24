#後臺處理的相關函數

import streamlit as st
import pandas as pd
import googlesheet_process as gp
import gspread
import time
import io
import datetime

def upload_retest_list_page():
    st.title("上傳補考名單")
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
                worksheet = gp.get_google_sheet_worksheet("補考名單", grade)
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
            worksheet = gp.get_google_sheet_worksheet("補考名單", grade)
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
    st.subheader(f"歡迎，管理員 {st.session_state['account']}！")

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

    col5, col6 = st.columns(2)
    with col5:
        if st.button("補考系統開放時間", key="nav_time_set", use_container_width=True):
            st.session_state['current_page'] = 'time_set'
            st.rerun()
    with col6:
        if st.button("帳號管理", key="nav_change_password", use_container_width=True):
            st.session_state['current_page'] = 'change_password'
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

    col7, col8 = st.columns(2)
    with col7:
        if st.button(f"查看 {view_grade} 年級補考名單", key=f"view_retest_list_btn_{view_grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'retest_list' # 設定為查看補考名單
            st.rerun() 
    with col8:
        if st.button(f"查看 {view_grade} 年級補考者報名資料", key=f"view_registrants_data_btn_{view_grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'registrants_data' # 設定為查看報名資料
            st.rerun()

    if st.session_state['selected_view_type'] == 'retest_list': sheet_to_view = "補考名單"
    else: sheet_to_view = "補考者報名資料"
    display_cloud_data(st.session_state['selected_view_grade'],sheet_to_view)
    
    st.markdown("---")
    if st.button("登出系統", key="logout_button"):
        st.session_state['admin_logged_in'] = False
        st.session_state['current_page'] = 'login' # 重設頁面到登入頁
        st.info("您已登出。")
        time.sleep(1) # 短暫延遲讓訊息顯示
        st.rerun()

def download_retest_registrants_data_page():
    st.title("下載補考者報名資料")
    registrants_spreadsheet_name = "補考者報名資料"

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
        registrants_worksheet = gp.get_google_sheet_worksheet(registrants_spreadsheet_name, download_grade)
        data = registrants_worksheet.get_all_values()
        info.empty()

        if data:
            df_registrants = pd.DataFrame(data[1:], columns=data[0]) # 將第一行作為欄位名稱，其餘作為資料
            st.dataframe(df_registrants, hide_index=True)
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
    try:
        info = st.info(f"正在從 Google Sheet 獲取 {view_grade} 工作表，來自{sheet_name}檔")
        worksheet = gp.get_google_sheet_worksheet(sheet_name, view_grade)
        data = worksheet.get_all_values()
        info.empty()

        if data:
            df_retest = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df_retest, hide_index=True)
        else:
            st.warning(f"{view_grade} 工作表中沒有找到資料。錯誤檔案：{sheet_name}")
    except Exception as e:
        st.error(f"查看 {view_grade} 發生錯誤。錯誤檔案：{sheet_name}。錯誤訊息：{e}")
        st.exception(e)

def time_set():
    st.title("補考系統開放時間設定")
    info = st.info("預設當日為開始日期，結束日期為一週後。")
    st.session_state['success_info'] = None

    display_cloud_data("補考系統開放時間",sheet_name="補考系統資料管理")
    start_date = st.date_input("開始日期", datetime.date.today())
    start_time = st.time_input("開始時間", datetime.time(8, 0))
    end_date = st.date_input("結束日期", datetime.date.today() + datetime.timedelta(days=7))  # 預設一週後
    end_time = st.time_input("結束時間", datetime.time(17, 0))

    col1, col2 = st.columns([1, 1], gap="small")
    with col1:
        if st.button("儲存設定", use_container_width=True):
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_datetime = datetime.datetime.combine(end_date, end_time)

            if start_datetime <= end_datetime: 
                st.session_state['success_info'] = True
                sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "補考系統開放時間")
                sheet.update_cell(2, 1, start_datetime.strftime("%Y-%m-%d %H:%M:%S"))
                sheet.update_cell(2, 2, end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            else: 
                st.session_state['success_info'] = False
    with col2:
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
    
    if st.session_state['success_info'] == True:
        info = st.success("報名時間設定已儲存！")
        time.sleep(1.5)
        info.empty()
        st.session_state['success_info'] = None
        st.rerun()
    elif st.session_state['success_info'] == False:
        info = st.warning("初始時間不能大於結束時間！")
        time.sleep(1.5)
        info.empty()
        st.session_state['success_info'] = None
        st.rerun()

def retest_seat():
    st.title("生成補考考生座位表")

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

def verify_password_page(pwd_context):
    st.title("更改/新增帳號密碼")
    st.info("預設帳號：user；預設密碼：pass ")
    username = st.session_state['account']

    password = st.text_input("密碼", type="password", key="verify_password_input")

    if st.button("驗證", key="preunverify"):
        log_in_data = load_admin_credentials_from_sheet(st.session_state['account'])

        if log_in_data and verify_password(pwd_context, username, password, log_in_data["password"]):
            success = st.success("驗證成功！")
            time.sleep(1)
            success.empty() # 清空訊息
            st.session_state['change_password_page'] = "verify"
            st.rerun()
        else: 
            error = st.error("帳號或密碼錯誤，請重新驗證。")
            time.sleep(2)
            error.empty()

    st.warning("請先驗證當前帳號密碼。")

def account_management_page(pwd_context):
    st.title("帳號管理")
    st.info("預設帳號：user；預設密碼：pass ")

    display_cloud_data("登入帳密",sheet_name="補考系統資料管理")
    account_management_list = ["更改密碼", "新增帳號", "刪除帳號"]

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        account_management_state = st.selectbox('帳號密碼管理功能', options = account_management_list, index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if account_management_state != st.session_state['account_management_page']:
        if account_management_state == "更改密碼":
            st.session_state['account_management_page'] = "更改密碼"
            st.rerun()
        elif account_management_state == "新增帳號":
            st.session_state['account_management_page'] = "新增帳號"
            st.rerun()
        elif account_management_state == "刪除帳號":
            st.session_state['account_management_page'] = "刪除帳號"
            st.rerun()

    if st.session_state['account_management_page'] == "更改密碼":
        change_password(pwd_context)
    elif st.session_state['account_management_page'] == "新增帳號":
        add_user_account(pwd_context)
    elif st.session_state['account_management_page'] == "刪除帳號":
        delete_user_account()

def hash_password(pwd_context, password: str) -> str:
    return pwd_context.hash(password)

def verify_password(pwd_context, username, plain_password: str, hashed_password: str) -> bool:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username", "admin_user")
    ADMIN_PASSWORD = st.secrets.get("admin", {}).get("password", "admin_pass")
    try:
        if plain_password == ADMIN_PASSWORD and username == ADMIN_USERNAME: # 如果是 admin 帳號，則直接返回 True
            return True
        return pwd_context.verify(plain_password, hashed_password) #hashed_password：雲端的密碼
    except ValueError:
        return False
    
def start_password(pwd_context):
    try:
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        password = hash_password(pwd_context, "pass")
        if sheet.cell(2, 2).value == None:
            sheet.update_cell(2, 1, "user")
            sheet.update_cell(2, 2, password)
            sheet.update_cell(2, 3, password)
    except Exception as e:
        st.error(f"讀取補考系統資料管理檔案失敗: {e}")

def load_admin_credentials_from_sheet(username: str) -> dict:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username", "admin_user")
    ADMIN_PASSWORD = st.secrets.get("admin", {}).get("password", "admin_pass")
    
    try:
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        data = sheet.get_all_values()  # 讀取整個工作表
        PRE_PASSWORD_HASH_COLUMN = 3
        PASSWORD_HASH_COLUMN = 2
        USERNAME_COLUMN = 1

        if username == ADMIN_USERNAME: # 如果是 admin 帳號，則直接返回預設密碼
            return {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        else:
            for row in data:
                if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == username:
                    if row[PASSWORD_HASH_COLUMN - 1] == row[PRE_PASSWORD_HASH_COLUMN - 1]:
                        return {"username": row[USERNAME_COLUMN - 1], "password": row[PASSWORD_HASH_COLUMN - 1], "pre_password": True}
                    else:
                        return {"username": row[USERNAME_COLUMN - 1], "password": row[PASSWORD_HASH_COLUMN - 1], "pre_password": False}
        
            error = st.error(f"找不到帳號")
            time.sleep(2)
            error.empty()
            return None  # 找不到帳號
    except Exception as e:
        error = st.error(f"讀取補考系統資料管理檔案失敗: {e}")
        time.sleep(2)
        error.empty()
        return None

def save_admin_password_to_sheet(username: str, new_password_hash: str) -> bool:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username", "admin_user")
    usernames = st.session_state['account']
    try:
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        data = sheet.get_all_values() #返回列表
        PASSWORD_HASH_COLUMN = 2
        USERNAME_COLUMN = 1

        for i, row in enumerate(data):
            if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == username:
                sheet.update_cell(i + 1, PASSWORD_HASH_COLUMN, new_password_hash)  # 更新密碼雜湊值
                if usernames != ADMIN_USERNAME:
                    sheet.update_cell(i + 1, PASSWORD_HASH_COLUMN + 1, new_password_hash)
                return True
        return False  # 找不到帳號
    except Exception as e:
        st.error(f"儲存管理員密碼失敗: {e}")
        return False
    
def change_password(pwd_context):
    st.header("更改密碼")
    
    username = st.session_state['account']
    is_ADMIN_USERNAME = False

    if username == st.secrets['admin']['username']:
        st.warning("請注意：無法更改 admin 帳號的密碼")
        display_cloud_data("登入帳密",sheet_name="補考系統資料管理")
        username  = st.text_input("輸入更動帳號", key="account _input")
        is_ADMIN_USERNAME = True

    new_password = st.text_input("輸入新密碼", type="password", key="new_password_input")
    confirm_new_password = st.text_input("確認新密碼", type="password", key="confirm_new_password_input")

    if st.button("確認更改密碼", key="change_password_submit"):
        if not new_password or not confirm_new_password:
            st.error("請填寫所有密碼欄位。")
            return  # 結束函式執行
        if new_password != confirm_new_password:
            st.error("新密碼與確認密碼不符，請重新輸入。")
            return
        if len(new_password) < 8:  # 提高密碼長度要求
            st.error("新密碼長度至少需要 8 個字元。")
            return

        # 密碼複雜度檢查
        import re
        if not re.search(r"[A-Z]", new_password) or not re.search(r"[0-9]", new_password) or not re.search(r"[!@#$%^&*]", new_password):
            st.error("新密碼必須包含大寫字母、數字和特殊字元。")
            return

        try:
            new_password_hash = hash_password(pwd_context, new_password)
            if save_admin_password_to_sheet(username, new_password_hash):
                if is_ADMIN_USERNAME == False:
                    st.success("密碼已成功更改！請使用新密碼重新登入。")
                    st.session_state['admin_logged_in'] = False
                    st.session_state['current_page'] = 'login'
                    time.sleep(1)
                    st.rerun()
                else:
                    st.success(f"{username}帳號的密碼已成功更改！")
                    time.sleep(2)
                    st.session_state['current_page'] = 'home'
                    st.rerun()
            else:
                if is_ADMIN_USERNAME == True: error = st.error("保存新密碼失敗，admin不能更改帳密。")
                else: st.error("保存新密碼失敗，請重試。")
                time.sleep(2)
                error.empty()
        except Exception as e:
            st.error(f"發生錯誤：{e}")

def add_user_account(pwd_context):
    import re

    st.header("新增帳號")

    new_username = st.text_input("請輸入新的使用者名稱", key="add_clear_username")
    new_password = st.text_input("請輸入新密碼", type="password", key="add_clear_password")
    confirm_new_password = st.text_input("確認新密碼", type="password", key="add_clear_confirm_password")

    if st.button("新增帳號"):
        if not new_username or not new_password or not confirm_new_password:
            st.error("請填寫所有必填欄位。")
            return
        if new_password != confirm_new_password:
            st.error("新密碼與確認密碼不符，請重新輸入。")
            return
        if len(new_password) < 8:
            st.error("新密碼長度至少需要 8 個字元。")
            return
        if not re.search(r"[A-Z]", new_password) or not re.search(r"[0-9]", new_password) or not re.search(r"[!@#$%^&*]", new_password):
            st.error("新密碼必須包含大寫字母、數字和特殊字元。")
            return
        
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        data = sheet.get_all_values()  # 讀取整個工作表
        PASSWORD_HASH_COLUMN = 2
        USERNAME_COLUMN = 1

        if new_username == st.secrets['admin']['username']: # 如果是 admin 帳號，則直接返回預設密碼
            st.error("不能使用 admin 帳號名稱，請使用其他名稱。")
            return
        else:
            for row in data:
                if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == new_username:
                    st.error(f"使用者名稱 '{new_username}' 已存在，請使用其他名稱。")
                    return
        try:
            hashed_password = hash_password(pwd_context, new_password)
            if sheet.append_row([new_username, hashed_password, hashed_password]):
                st.success(f"帳號 '{new_username}' 新增成功！")
                time.sleep(2)
                st.session_state['current_page'] = 'home'
                st.rerun()
            else:
                st.error("新增帳號失敗，請重試。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")

def delete_user_account():
    usernames = []

    st.header("刪除帳號")

    sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
    data = sheet.get_all_values()  # 讀取整個工作表
    USERNAME_COLUMN = 1
    
    for row in data:
        # 避免刪除預設帳號和當前登入的帳號及欄名稱(使用者名稱)
        if row[USERNAME_COLUMN - 1] != "user" and row[USERNAME_COLUMN - 1] != st.session_state['account'] and row[USERNAME_COLUMN - 1] != "使用者名稱":
            usernames.append(row[USERNAME_COLUMN - 1]) # 將所有使用者名稱加入列表

    username_to_delete = st.selectbox("請選擇要刪除的帳號", usernames)

    if st.button(f"確定刪除帳號 '{username_to_delete}'", icon="⚠️", key=f"confirm_delete_{username_to_delete}"):
        try:
            if gp.delete_user_from_sheet(username_to_delete, "補考系統資料管理", "登入帳密", 1):
                st.success(f"帳號 '{username_to_delete}' 已成功刪除！")
                time.sleep(2)
                st.rerun()
            else:
                st.error("刪除帳號失敗，請重試。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")

    if st.session_state['account'] == st.secrets['admin']['username']:
        st.warning(f"請注意：無法刪除 {st.secrets['admin']['username']} 、 user 帳號。")
    else:
        st.warning("請注意：無法刪除 user 及當前登入的帳號。")

def first_change_password(pwd_context):
    change_password(pwd_context)
    st.info("您使用預設密碼登入，請更改您的密碼。")