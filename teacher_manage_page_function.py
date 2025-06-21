import streamlit as st, pandas as pd, googlesheet_manage as gm, gspread, time, io, datetime

def start_password():
    try:
        worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_system_manage'], "登入帳密")
        if worksheet.cell(2, 2).value == None:
            password = hash_password("pass")
            worksheet.update_cell(2, 1, "user")
            worksheet.update_cell(2, 2, password)
            worksheet.update_cell(2, 3, password)
    except Exception as e:
        st.error(f"讀取補考系統資料管理檔案失敗: {e}")

def hash_password(password: str) -> str:
    return st.session_state['pwd_context'].hash(password)

def load_admin_credentials_from_sheet(username: str) -> dict:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username")
    ADMIN_PASSWORD = st.secrets.get("admin", {}).get("password")
    
    try:
        worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_system_manage'], "登入帳密")
        account_data = worksheet.get_all_values()  # 讀取整個工作表，以二維列表儲存
        PRE_PASSWORD_HASH_COLUMN = 3 # 更動紀錄
        PASSWORD_HASH_COLUMN = 2 # 密碼
        USERNAME_COLUMN = 1 # 帳號

        if username == ADMIN_USERNAME: # 如果是 admin 帳號，則直接返回預設密碼
            return {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD, "pre_password": True}
        else:
            for row in account_data: # 逐一提取google sheet的列(row為一維列表)
                # 查詢每一列內的元素個數，並檢查該列第一個元素是否為登入帳號
                if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == username:
                    if row[PASSWORD_HASH_COLUMN - 1] == row[PRE_PASSWORD_HASH_COLUMN - 1]:
                        return {"username": row[USERNAME_COLUMN - 1], "password": row[PASSWORD_HASH_COLUMN - 1], "pre_password": True}
                    else:
                        return {"username": row[USERNAME_COLUMN - 1], "password": row[PASSWORD_HASH_COLUMN - 1], "pre_password": False}

            return False
    except Exception as e:
        st.error(f"讀取補考系統資料管理檔案失敗: {e}")
        time.sleep(2)
        return None
    
def verify_password(username, plain_password: str, hashed_password: str) -> bool:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username")
    ADMIN_PASSWORD = st.secrets.get("admin", {}).get("password")
    try:
        if plain_password == ADMIN_PASSWORD and username == ADMIN_USERNAME: # 如果是 admin 帳號，則直接返回 True
            return True
        return st.session_state['pwd_context'].verify(plain_password, hashed_password) #hashed_password：雲端的密碼
    except ValueError:
        return False

def default(next_page):
    st.session_state['current_page'] = next_page
    st.session_state['selected_view_type'] = 'retest_data'
    st.session_state['selected_grade'] = "1"
    st.session_state['student_data'] = None
    st.session_state['selected_class'] = "1"
    st.session_state['name_input_value'] = ""
    st.session_state['seat_number_input_value'] = 1
    st.session_state['student_data'] = None
    st.session_state['account_management_page'] = '更改密碼'

def home_page():
    st.title("補考資料管理系統：首頁")
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
        if st.button("清空表單資料", key="nav_claen_registrants", use_container_width=True):
            st.session_state['current_page'] = 'claen_registrants'
            st.rerun()
    with col4:
        if st.button("生成考生座位表", key="nav_retest_seat", use_container_width=True):
            st.session_state['current_page'] = 'retest_seat'
            st.rerun()

    col5, col6 = st.columns(2)
    with col5:
        if st.button("補考系統開放時間", key="nav_time_set", use_container_width=True):
            st.session_state['current_page'] = 'time_set'
            st.rerun()
    with col6:
        if st.button("手動新增補考學生", key="nav_add_retester", use_container_width=True):
            st.session_state['current_page'] = 'add_retester'
            st.rerun()

    col7, col8 = st.columns(2)
    with col7:
        if st.button("年度資料管理", key="nav_year_data_manage", use_container_width=True):
            st.session_state['current_page'] = 'year_data_manage'
            st.rerun()
    with col8:
        if st.button("帳號管理", key="nav_change_password", use_container_width=True):
            st.session_state['current_page'] = 'account_manage_unverify'
            st.rerun()

    st.markdown("---")
    st.header("查看雲端資料")

    view_grade = st.selectbox('選擇查看年級', options=["1", "2", "3"], key='view_data_grade_select', index=0)
    if st.session_state.get('view_data_grade_select') != st.session_state['selected_grade']: # 如果 selectbox 的值改變了，更新 session state 並觸發重新渲染
        st.session_state['selected_grade'] = st.session_state.get('view_data_grade_select')
        st.rerun() # 重新渲染以顯示新的年級資料

    col9, col10 = st.columns(2)
    with col9:
        if st.button(f"查看 {view_grade} 年級補考名單", key=f"view_retest_list_btn_{view_grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'retest_list' # 設定為查看補考名單
            st.rerun() 
    with col10:
        if st.button(f"查看 {view_grade} 年級補考者報名資料", key=f"view_registrants_data_btn_{view_grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'registrants_data' # 設定為查看報名資料
            st.rerun()

    if st.session_state['selected_view_type'] == 'retest_list': worksheet = f"{view_grade}年級補考名單"
    else: worksheet = f"{view_grade}年級報名資料"
    gm.display_cloud_data(st.session_state['cloud_retest_data_manage'], worksheet)
    
    st.markdown("---")
    if st.button("登出", key="logout_button"):
        default('login')
        st.info("您已登出。")
        time.sleep(1)
        st.rerun()

def upload_retest_list_page():
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("上傳補考名單")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    info = st.empty()

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.selectbox('選擇操作年級', options=st.session_state['grade_list'], key='grade_input', index=st.session_state['grade_list'].index(st.session_state['selected_grade']))
        st.session_state['selected_grade'] = st.session_state.get('grade_input')
        grade = st.session_state['selected_grade']
    with col2:
        st.selectbox('選擇上傳檔案類型', options=['xlsx','csv'], key='file_type_input', index=0)

    gm.display_cloud_data(st.session_state['cloud_retest_data_manage'], grade + '年級補考名單')
    
    # 上傳檔案錯誤時，有1132補考名單(高三)(公告)0502.xlsx application/vnd.openxmlformats-officedocument.spreadsheetml.sheet files are not allowed.錯誤訊息
    uploaded_file = st.file_uploader(f"選擇一個 {st.session_state['file_type_input']} 檔案", type=[st.session_state['file_type_input']])

    col3, col4 = st.columns([0.05, 0.95], gap="small")
    with col3:
        auto = st.checkbox("自動分析", label_visibility="hidden", value=True)
    with col4:
        st.button("確認上傳", key="upload_retest")

    if auto and st.session_state['file_type_input'] == 'csv':
        info.info(f'1. 已勾選：系統將以內容資料的第一筆數據作為上傳雲端工作表的依據。\n2. 請確認上傳的補考名單為 Excel 檔案，附檔名為 {st.session_state['file_type_input']}。\n3. csv 檔沒有工作表之分，勾選後仍無法同時上傳多個工作表。\n\n註：若需同時上傳多個工作表，請將上傳檔案類型選擇為 xlsx 檔。')
    elif auto and st.session_state['file_type_input'] == 'xlsx':
        info.info(f'1. 已勾選：系統將以工作表的第一筆數據作為上傳雲端工作表的依據，並上傳前三個工作表。\n2. 請確認上傳的補考名單為 Excel 檔案，附檔名為 {st.session_state['file_type_input']}。')
    else:
        info.info(f'1. 僅上傳第一個工作表資料，請特別注意所選年級。\n2. 請確認上傳的補考名單為 Excel 檔案，附檔名為 {st.session_state['file_type_input']}。')

    if st.session_state['upload_retest']:
        if auto:
            return_data = gm.upload_to_google_sheet(auto, ['1','2','3'], uploaded_file, st.session_state['file_type_input'])
        else:
            return_data = gm.upload_to_google_sheet(auto, [grade], uploaded_file, st.session_state['file_type_input'])
        info.warning(return_data)
        time.sleep(1)
        st.rerun()

def clear_retest_list_page():
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("清空表單資料")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.selectbox('選擇操作年級', options=st.session_state['grade_list'], key='grade_input', index=st.session_state['grade_list'].index(st.session_state['selected_grade']))
    st.session_state['selected_grade'] = st.session_state.get('grade_input')
    grade = st.session_state['selected_grade']

    col3, col4 = st.columns(2)
    with col3:
        if st.button(f"查看 {grade} 年級補考名單", key=f"view_retest_list_btn_{grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'retest_list' # 設定為查看補考名單
            st.rerun() 
    with col4:
        if st.button(f"查看 {grade} 年級報名資料", key=f"view_registrants_data_btn_{grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'registrants_data' # 設定為查看報名資料
            st.rerun()

    if st.session_state['selected_view_type'] == 'retest_list': worksheet = f"{grade}年級補考名單"
    else: worksheet = f"{grade}年級報名資料"
    gm.display_cloud_data(st.session_state['cloud_retest_data_manage'], worksheet)

    if st.button(f"確認清空 {worksheet} 工作表資料", key=f"clear_btn_{grade}"):
        try: # 獲取目標工作表
            worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_data_manage'], worksheet)
        except Exception as e:
            st.error(f"無法取得 Google Sheet 工作表 '{worksheet.title}'，請確認試算表名稱和工作表名稱是否正確，或服務帳戶權限。")
            st.exception(e)
            return False
        if gm.clear_google_sheet_data(worksheet):
            st.success(f"工作表 '{worksheet.title}' 的資料已成功清空。")
            time.sleep(1)
            st.rerun()

def download_retest_registrants_data_page():
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("下載補考報名資料")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.selectbox('選擇下載年級', options=st.session_state['grade_list'], key='grade_input', index=st.session_state['grade_list'].index(st.session_state['selected_grade']))
    st.session_state['selected_grade'] = st.session_state.get('grade_input')
    grade = st.session_state['selected_grade']

    try:
        info = st.info(f"正在從 Google Sheet 獲取 {grade} 年級報名資料...")
        worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_data_manage'], grade + '年級報名資料') # 獲取補考者報名資料的工作表
        data = worksheet.get_all_values()
        info.empty()

        if data:
            df_registrants = pd.DataFrame(data[1:], columns=data[0]) # 將第一行作為欄位名稱，其餘作為資料
            st.dataframe(df_registrants, hide_index=True)

            col3, col4 = st.columns([1, 1], gap="small")
            with col3:
                csv_data = df_registrants.to_csv(index=False).encode('utf-8-sig') # utf-8-sig 支援中文，Excel 可直接開啟
                st.download_button(
                    label=f"下載 {grade} 年級補考報名資料 (CSV)",
                    data=csv_data,
                    file_name=f"補考報名資料_{grade}年級.csv",
                    mime="text/csv",
                    key=f"download_csv_btn_{grade}",
                    use_container_width=True
                )
            with col4:
                output = io.BytesIO()
                
                # 使用 ExcelWriter 將 DataFrame 寫入記憶體中的 Excel 檔案
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_registrants.to_excel(writer, index=False, sheet_name=f"{grade}年級報名資料")
                xlsx_data = output.getvalue()
                
                st.download_button(
                    label=f"下載 {grade} 年級補考報名資料 (xlsx)",
                    data=xlsx_data,
                    file_name=f"補考者報名資料_{grade}年級.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", # Excel 的 MIME 類型
                    key=f"download_xlsx_btn_{grade}",
                    use_container_width=True
                )
        else:
            st.warning(f"{grade} 年級補考報名資料中沒有找到資料。")

    except Exception as e:
        st.error(f"下載 {grade} 年級補考者報名資料時發生錯誤：{e}")
        st.exception(e)

    st.info("1. 下載的檔案會儲存在本地端的預設下載資料夾中。\n2. 檔案內的時間欄位若為井字號，請將該欄拉寬便能正常顯示。")

def time_set():
    st.session_state['info'] = None
    
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("補考系統開放時間設定")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.info("預設當日為開始日期，結束日期為一週後。")

    gm.display_cloud_data(st.session_state['cloud_retest_system_manage'], "補考系統開放時間")
    start_date = st.date_input("開始日期", datetime.date.today())
    start_time = st.time_input("開始時間", datetime.time(8, 0))
    end_date = st.date_input("結束日期", datetime.date.today() + datetime.timedelta(days=7))  # 預設一週後
    end_time = st.time_input("結束時間", datetime.time(17, 0))

    worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_system_manage'], "補考系統開放時間")

    col3, col4 = st.columns([1, 1], gap="small")
    with col3:
        if st.button("不限時間", use_container_width=True):
            worksheet.update_cell(2, 1, "不限時間")
            worksheet.update_cell(2, 2, "不限時間")
            st.session_state['info'] = "補考系統開放時間已設定為不限時間！"
    with col4:
        if st.button("儲存設定", use_container_width=True):
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_datetime = datetime.datetime.combine(end_date, end_time)

            if start_datetime <= end_datetime:
                st.session_state['info'] = "報名時間設定已儲存！"
                worksheet.update_cell(2, 1, start_datetime.strftime("%Y-%m-%d %H:%M:%S"))
                worksheet.update_cell(2, 2, end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            else: 
                st.session_state['info'] = "初始時間不能大於結束時間！"
    
    if st.session_state['info'] != None:
        st.info(st.session_state['info'])
        time.sleep(1)
        st.session_state['info'] = None
        st.rerun()

def retest_seat():
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("生成考生座位表")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    grade = st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input')

    worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_data_manage'], grade + '年級報名資料') # 獲取補考者報名資料的工作表
    data = worksheet.col_values(3) #取C欄(報名資料中的科目)值
    data = list(set(data)) #消除重複值
    data.remove('補考科目')

    suject = st.selectbox('選擇有被報名的科目', options=data, key='suject_input')
    gm.display_cloud_data(st.session_state['cloud_retest_data_manage'], grade + '年級補考名單')

def year_data_manage():
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("年度資料管理")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    grade = st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input')
    gm.display_cloud_data(st.session_state['cloud_retest_data_manage'], grade + '年級補考名單')

def add_retester():    
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
         st.title("手動新增補考學生")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    col = st.columns([1, 1], gap="small")
    with col[0]:
        st.selectbox('年級',
            options=st.session_state['grade_list'],
            key='grade_input_add_retester',
            index=st.session_state['grade_list'].index(st.session_state['selected_grade'])
        )
        st.session_state['selected_grade'] = st.session_state['grade_input_add_retester']
        grade = st.session_state['selected_grade']
    with col[1]:
        st.selectbox('班級',
            options=st.session_state['class_list'],
            key='class_name_input_add_retester',
            index=st.session_state['class_list'].index(st.session_state['selected_class'])
        )
        st.session_state['selected_class'] = st.session_state['class_name_input_add_retester']
        class_name = st.session_state['selected_class']

    st.text_input('姓名', key='name_input', value=st.session_state['name_input_value'])
    st.session_state['name_input_value'] = st.session_state['name_input']
    name = st.session_state['name_input_value']

    st.number_input('座號', min_value=1, step=1, key='seat_number_input', value=st.session_state['seat_number_input_value'])
    st.session_state['seat_number_input_value'] = st.session_state['seat_number_input']
    seat_number = st.session_state['seat_number_input_value']

    if st.button("查詢"):
        if not name:
            st.error("請輸入學生姓名。")
            return

        st.session_state['student_data'] = None
        gm.find_student_in_sheet(grade, class_name, seat_number, name)

    if st.session_state['student_data'] is not None:
        if gm.student_sign_up():
            st.success('已報名成功！')
            time.sleep(1)
            default('add_retester')
            st.rerun()

def verify_password_page():
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("帳號管理")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.info("預設帳號：user；預設密碼：pass ")

    username = st.session_state['account']
    password = st.text_input("密碼", type="password", key="verify_password_input")

    if st.button("驗證", key="preunverify"):
        log_in_data = load_admin_credentials_from_sheet(username)

        if log_in_data and verify_password(username, password, log_in_data["password"]):
            st.success("驗證成功！")
            time.sleep(1)
            default('account_manage_verify')
            st.rerun()
        else: 
            st.error("帳號或密碼錯誤，請重新驗證。")

    st.warning("請先驗證當前帳號密碼。")

def account_management_page():
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("帳號管理")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            default('home')
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.info("每次帳號或密碼完成變更後，將會自動跳轉到首頁。")

    gm.display_cloud_data(st.session_state['cloud_retest_system_manage'], "登入帳密")
    account_management_state = st.selectbox('帳號密碼管理功能', options=["更改密碼", "新增帳號", "刪除帳號"], key='account_management_state')
    
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
        change_password(False) # False: 判斷是否為第一次登入而更改密碼，若是，顯示提示語
    elif st.session_state['account_management_page'] == "新增帳號":
        add_user_account()
    elif st.session_state['account_management_page'] == "刪除帳號":
        delete_user_account()

def change_password(first_login): # first_login:判斷是否為第一次登入而更改密碼，若是，顯示提示語
    st.header("更改密碼")
    
    username = st.session_state['account']
    worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_system_manage'], "登入帳密")
    data = worksheet.get_all_values()  # 讀取整個工作表
    usernames = []
    usernames_index = []
    USERNAME_COLUMN = 1

    if username == st.secrets['admin']['username']:
        st.warning("請注意：無法更改 admin 帳號的密碼")

        for i, row in enumerate(data):
            # 取得除了預設帳號和當前登入的帳號及欄名稱(使用者名稱)的所有資料
            if row[USERNAME_COLUMN - 1] != "使用者名稱":
                usernames.append(row[USERNAME_COLUMN - 1]) # 將所有使用者名稱加入列表
                usernames_index.append(i + 1) # 將所有使用者名稱的索引加入列表

        username = st.selectbox("請選擇要更動的帳號", usernames)
    else:
        for i, row in enumerate(data):
            if row[USERNAME_COLUMN - 1] != "使用者名稱" and row[USERNAME_COLUMN - 1] == username:
                usernames.append(row[USERNAME_COLUMN - 1])
                usernames_index.append(i + 1)

    new_password = st.text_input("輸入新密碼", type="password", key="new_password_input")
    confirm_new_password = st.text_input("確認新密碼", type="password", key="confirm_new_password_input")

    if st.button("確認更改密碼", key="change_password"):
        if not new_password or not confirm_new_password:
            st.error("請填寫所有密碼欄位。")
            return
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
        if st.secrets['admin']['username'] == username:
            st.error("保存新密碼失敗，admin不能更改帳密。")
            time.sleep(1)
            return

        try:
            new_password_hash = hash_password(new_password)

            if st.secrets['admin']['username'] != st.session_state['account']:
                data_list = [username, new_password_hash, new_password_hash, usernames_index[usernames.index(username)]]
            else:
                data_list = [username, new_password_hash, usernames_index[usernames.index(username)]]

            if gm.save_to_google_sheet(data_list, st.session_state['cloud_retest_system_manage'], "登入帳密"):                
                if st.secrets['admin']['username'] != st.session_state['account']:
                    st.success("密碼已成功更改！請使用新密碼重新登入。")
                    time.sleep(1)
                    default('login')
                    st.rerun()
                else:
                    st.success(f"{username} 帳號的密碼已成功更改！即將返回首頁。")
                    time.sleep(1)
                    default('home')
                    st.rerun()
            else:
                st.error("保存新密碼失敗，請確認帳號是否存在或其他錯誤。")
                time.sleep(1)
        except Exception as e:
            st.error(f"發生錯誤：{e}")
    if first_login != False: st.info(first_login)

def add_user_account():
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

        import re
        if not re.search(r"[A-Z]", new_password) or not re.search(r"[0-9]", new_password) or not re.search(r"[!@#$%^&*]", new_password):
            st.error("新密碼必須包含大寫字母、數字和特殊字元。")
            return
        
        worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_system_manage'], "登入帳密")
        data = worksheet.get_all_values()  # 讀取整個工作表
        PASSWORD_HASH_COLUMN = 2
        USERNAME_COLUMN = 1

        if new_username == st.secrets['admin']['username']:
            st.error("不能使用 admin 帳號名稱，請使用其他名稱。")
            return
        else:
            for row in data:
                if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == new_username:
                    st.error(f"使用者名稱 '{new_username}' 已存在，請使用其他名稱。")
                    return
        try:
            hashed_password = hash_password(new_password)
            if worksheet.append_row([new_username, hashed_password, hashed_password]):
                st.success(f"帳號 '{new_username}' 新增成功！即將返回首頁。")
                time.sleep(1)
                default('home')
                st.rerun()
            else:
                st.error("新增帳號失敗，請重試。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")

def delete_user_account():
    st.header("刪除帳號")

    worksheet = gm.open_google_sheet_worksheet(st.session_state['cloud_retest_system_manage'], "登入帳密")
    data = worksheet.get_all_values()  # 讀取整個工作表

    USERNAME_COLUMN = 1
    usernames = []
    usernames_index = []
    for i, row in enumerate(data):
        # 取得除了預設帳號和當前登入的帳號及欄名稱(使用者名稱)的所有資料
        if row[USERNAME_COLUMN - 1] != "user" and row[USERNAME_COLUMN - 1] != st.session_state['account'] and row[USERNAME_COLUMN - 1] != "使用者名稱":
            usernames.append(row[USERNAME_COLUMN - 1]) # 將所有使用者名稱加入列表
            usernames_index.append(i)

    username_to_delete = st.selectbox("請選擇要刪除的帳號", usernames)
    confirm_password = st.text_input(f"驗證帳號 {username_to_delete} 的密碼", type="password")

    if st.button(f"確定刪除帳號 '{username_to_delete}'", icon="⚠️", key=f"confirm_delete_{username_to_delete}"):
        try:
            try:
                is_correct_password = verify_password(username_to_delete, confirm_password, data[usernames_index[usernames.index(username_to_delete)]][2])
                if is_correct_password != False:
                    if gm.delete_user_from_sheet(username_to_delete, worksheet, USERNAME_COLUMN):
                        st.success(f"帳號 '{username_to_delete}' 已成功刪除！")
                        time.sleep(1)
                        default('home')
                        st.rerun()
                else:
                    st.error("密碼錯誤，請重新驗證密碼。")
                    return
            except Exception as e:
                st.error(f"驗證密碼時發生錯誤：{e}")
        except Exception as e:
            st.error(f"發生錯誤：{e}")

    if st.session_state['account'] == st.secrets['admin']['username']:
        st.warning(f"請注意：無法刪除 {st.secrets['admin']['username']} 、 user 帳號。")
    else:
        st.warning("請注意：無法刪除 user 及當前登入的帳號。")