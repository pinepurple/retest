import streamlit as st, time, teacher_manage_page_function as tf, googlesheet_manage as gm
from passlib.context import CryptContext

def main_app():
    st.set_page_config(page_title="補考資料管理系統", page_icon="lock")

    # 初始化管理員登入狀態
    if 'cloud_retest_data_manage' not in st.session_state: #儲存"補考資料管理"試算表的雲端資料，內涵補考名單、報名資料
        st.session_state['cloud_retest_data_manage'] = gm.open_google_sheet("補考資料管理")
    if 'cloud_retest_system_manage' not in st.session_state: #儲存"補考系統資料管理"試算表的雲端資料，內涵補考名單、報名資料
        st.session_state['cloud_retest_system_manage'] = gm.open_google_sheet("補考系統資料管理")
    if 'current_page' not in st.session_state: # 儲存當前頁面狀態
        st.session_state['current_page'] = 'login'
        tf.start_password()
    if 'account' not in st.session_state: # 儲存當前使用帳號
        st.session_state['account'] = st.secrets.get("admin", {}).get("username")
    if 'selected_view_type' not in st.session_state: # 儲存首頁顯示的表單類型(補考資料或補考名單)
        st.session_state['selected_view_type'] = 'retest_data' # 預設顯示補考名單
    if 'selected_grade' not in st.session_state: # 儲存顯示的表單年級
        st.session_state['selected_grade'] = "1"
    if 'selected_class' not in st.session_state:
        st.session_state['selected_class'] = "1"
    if 'name_input_value' not in st.session_state:
        st.session_state['name_input_value'] = ""
    if 'seat_number_input_value' not in st.session_state:
        st.session_state['seat_number_input_value'] = 1
    if 'student_data' not in st.session_state:
        st.session_state['student_data'] = None
    if 'account_management_page' not in st.session_state:
        st.session_state['account_management_page'] = '更改密碼'
    if 'pwd_context' not in st.session_state: # 儲存使用的密碼雜湊、加鹽演算法
        st.session_state['pwd_context'] = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if 'grade_list' not in st.session_state: # 儲存年級列表
        st.session_state['grade_list'] = ["1", "2", "3"]
    if 'class_list' not in st.session_state: # 儲存年級列表
        st.session_state['class_list'] = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"] # 儲存班級列表

    if st.session_state['current_page'] == 'login':
        st.title("補考資料管理系統")
        st.info("請輸入管理員帳號密碼 ( 預設帳號：user；預設密碼：pass )")

        username = st.text_input("帳號", key="admin_username_input", value = "user")
        password = st.text_input("密碼", type="password", key="admin_password_input", value = "pass")

        log_in_data = tf.load_admin_credentials_from_sheet(username) # 儲存雲端關於當前使用者的資料
        if st.button("登入", key="admin_login_button"):
            if log_in_data != False:
                if log_in_data and tf.verify_password(username, password, log_in_data["password"]):
                    st.success("登入成功！")
                    st.session_state['account'] = username
                    time.sleep(1)
                    
                    if password == "pass" and username == "user": # 如果使用者使用預設密碼登入
                        st.session_state['current_page'] = 'first_change_password'
                        st.rerun()
                    elif username != st.secrets['admin']['username'] and log_in_data and log_in_data["pre_password"] == False:
                        st.session_state['current_page'] = 'is_change_password'
                        st.rerun()
                    else:
                        st.session_state['current_page'] = 'home'
                        st.rerun()
                elif log_in_data:
                    error = st.error("帳號或密碼錯誤，請重新輸入。")
                    time.sleep(2)
                    error.empty()
            else:
                st.warning(f"找不到 {username} 帳號")

        if log_in_data["pre_password"] == False:
            st.warning(f"帳號 {username} 的密碼已經透過 {st.secrets['admin']['username']} 帳號重新設定。")

    elif st.session_state['current_page'] != 'first_change_password' and st.session_state['current_page'] != 'is_change_password':
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
            st.session_state['current_page'] = 'claen_registrants'
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
        if st.sidebar.button("帳號管理", key="sidebar_account_manage_unverify"):
            if st.session_state['current_page'] != 'account_manage_verify':
                st.session_state['current_page'] = 'account_manage_unverify'
                st.rerun()
            else:
                st.session_state['current_page'] = 'account_manage_verify'
                st.rerun()
        if st.sidebar.button("登出", key="sidebar_logout"):
            st.session_state['current_page'] = 'login'
            st.info("您已登出。")
            time.sleep(1)
            st.rerun()

    # 根據 session state 顯示當前頁面
    if st.session_state['current_page'] == 'home':
        tf.home_page()
    elif st.session_state['current_page'] == 'first_change_password':
        tf.change_password("您使用預設密碼登入，請更改您的密碼。")
    elif st.session_state['current_page'] == 'is_change_password':
        tf.change_password(f"帳號 {st.session_state['account']} 的密碼已經透過 {st.secrets['admin']['username']} 帳號重新設定，請更改您的密碼。")
    elif st.session_state['current_page'] == 'upload_retest_list':
        tf.upload_retest_list_page()
    elif st.session_state['current_page'] == 'download_registrants_data':
        tf.download_retest_registrants_data_page()
    elif st.session_state['current_page'] == 'claen_registrants':
        tf.clear_retest_list_page()
    elif st.session_state['current_page'] == 'add_retester':
        tf.add_retester()
    elif st.session_state['current_page'] == 'year_data_manage':
        tf.year_data_manage()
    elif st.session_state['current_page'] == 'retest_seat':
        tf.retest_seat()
    elif st.session_state['current_page'] == 'time_set':
        tf.time_set()
    elif st.session_state['current_page'] == 'account_manage_unverify':
        tf.verify_password_page()
    elif st.session_state['current_page'] == 'account_manage_verify':
        tf.account_management_page()

if __name__ == '__main__':
    main_app()