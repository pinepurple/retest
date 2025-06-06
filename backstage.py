import streamlit as st
import time
import backstage_function as bf
from passlib.context import CryptContext

# --- 主應用程式流程控制 ---
def main_app():
    st.set_page_config(page_title="後台管理系統", page_icon="lock") # 為後台應用程式設定獨立的頁面配置

    # 初始化管理員登入狀態
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'login' # 預設起始頁面為登入頁
    if 'change_password_page' not in st.session_state:
        st.session_state['change_password_page'] = 'unverify'
    if 'account_management_page' not in st.session_state:
        st.session_state['account_management_page'] = '更改密碼'
    if 'account' not in st.session_state:
        st.session_state['account'] = st.secrets.get("admin", {}).get("username", "admin_user") # 預設帳號為 admin_user
    if 'selected_view_type' not in st.session_state:
        st.session_state['selected_view_type'] = 'retest_list' # 預設顯示補考名單
    if 'selected_view_grade' not in st.session_state:
        st.session_state['selected_view_grade'] = "1"
    # 初始化 retest_seat page
    if 'classroom_layout' not in st.session_state:
        st.session_state['classroom_layout'] = '6x6' # 預設教室佈局
    if 'retest_students_for_seat' not in st.session_state:
        st.session_state['retest_students_for_seat'] = None # 儲存從 Google Sheet 讀取的學生數據
    if 'edited_retest_students_df' not in st.session_state:
        st.session_state['edited_retest_students_df'] = None # 儲存 data_editor 編輯後的數據

    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    bf.start_password(pwd_context)
    top_level_message_placeholder = st.empty() # 創建一個用於頂部訊息 (如登入成功) 的佔位符

    if not st.session_state['admin_logged_in']:
        # --- 管理員登入頁面 ---
        st.title("後台管理系統")
        st.info("請輸入管理員帳號密碼 ( 預設帳號：user；預設密碼：pass )")

        username = st.text_input("帳號", key="admin_username_input", value = "user")
        password = st.text_input("密碼", type="password", key="admin_password_input", value = "pass")
        log_in_data = bf.load_admin_credentials_from_sheet(username)

        if st.button("登入", key="admin_login_button"):
            if log_in_data and bf.verify_password(pwd_context, username, password, log_in_data["password"]):
                top_level_message_placeholder.success("登入成功！")
                st.session_state['account'] = username
                time.sleep(1)
                top_level_message_placeholder.empty() # 清空訊息
                st.session_state['admin_logged_in'] = True
                
                if password == "pass" and username == "user": # 如果使用者使用預設密碼登入
                    st.session_state['current_page'] = 'first_change_password'
                    st.rerun()
                else:
                    st.session_state['current_page'] = 'home' # 登入成功後設定為首頁                
                    st.rerun()
            elif log_in_data:
                error = st.error("帳號或密碼錯誤，請重新輸入。")
                time.sleep(2)
                error.empty()

        if username != st.secrets['admin']['username'] and log_in_data and log_in_data["pre_password"] == False:
            st.warning(f"帳號{username}的密碼已經透過{st.secrets['admin']['username']}帳號重新設定")

    elif st.session_state['current_page'] != 'first_change_password':
        st.sidebar.title("功能選單")
        st.sidebar.write(f"當前使用者：{st.session_state['account']}")
        if st.sidebar.button("首頁", key="sidebar_home"):
            st.session_state['current_page'] = 'home'
            st.rerun()
        if st.sidebar.button("上傳補考名單", key="sidebar_upload_retest"):
            st.session_state['current_page'] = 'upload_retest_list'
            st.rerun()
        if st.sidebar.button("下載補考者報名資料", key="sidebar_download_registrants"):
            st.session_state['current_page'] = 'download_registrants_data'
            st.rerun()
        if st.sidebar.button("清空表單資料", key="sidebar_claen_registrants"):
            st.session_state['current_page'] = 'sidebar_claen_registrants'
            st.rerun()
        if st.sidebar.button("手動新增補考學生", key="sidebar_add_retester"):
            st.session_state['current_page'] = 'add_retester'
            st.rerun()
        if st.sidebar.button("生成考生座位表", key="sidebar_retest_seat"):
            st.session_state['current_page'] = 'retest_seat'
            st.rerun()
        if st.sidebar.button("年度資料管理", key="sidebar_year_data_manage"):
            st.session_state['current_page'] = 'year_data_manage'
            st.rerun()
        if st.sidebar.button("補考系統開放時間", key="sidebar_time_set"):
            st.session_state['current_page'] = 'time_set'
            st.rerun()
        if st.sidebar.button("帳號管理", key="sidebar_change_password"):
            st.session_state['current_page'] = 'change_password'
            st.rerun()
        if st.sidebar.button("登出", key="sidebar_logout"):
            st.session_state['admin_logged_in'] = False
            st.session_state['current_page'] = 'login'
            top_level_message_placeholder.info("您已登出。")
            time.sleep(1)
            top_level_message_placeholder.empty()
            st.rerun()

    previous_page = st.session_state.get('previous_page', None)
    current_page = st.session_state['current_page']

    if previous_page == 'change_password' and current_page != 'change_password':
        st.session_state['change_password_page'] = 'unverify'

    st.session_state['previous_page'] = current_page

    # 根據 session state 顯示當前頁面
    if st.session_state['current_page'] == 'home':
        bf.home_page()
    elif st.session_state['current_page'] == 'first_change_password':
        bf.first_change_password(pwd_context)
    elif st.session_state['current_page'] == 'upload_retest_list':
        bf.upload_retest_list_page()
    elif st.session_state['current_page'] == 'download_registrants_data':
        bf.download_retest_registrants_data_page()
    elif st.session_state['current_page'] == 'sidebar_claen_registrants':
        bf.clear_retest_list_page()
    elif st.session_state['current_page'] == 'add_retester':
        bf.add_retester()
    elif st.session_state['current_page'] == 'year_data_manage':
        bf.year_data_manage()
    elif st.session_state['current_page'] == 'retest_seat':
        bf.retest_seat()
    elif st.session_state['current_page'] == 'time_set':
        bf.time_set()
    elif st.session_state['current_page'] == 'change_password':
        if st.session_state['change_password_page'] == 'unverify':
            bf.verify_password_page(pwd_context)
        elif st.session_state['change_password_page'] == 'verify':
            bf.account_management_page(pwd_context)

if __name__ == '__main__':
    main_app()