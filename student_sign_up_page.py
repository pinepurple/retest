import streamlit as st, student_sign_up_page_function as sf, googlesheet_manage as gm
#---------------------------------------------初始化-----------------------------------------------------------
st.set_page_config(page_title="補考報名系統", page_icon="clipboard")
if 'stage' not in st.session_state: #控制頁面切換
    st.session_state['stage'] = 'login'
if 'student_data' not in st.session_state: #記錄登入學生的基本資料
    st.session_state['student_data'] = None
if 'student_sign_up_data' not in st.session_state: #儲存登入學生在雲端中的資料
    st.session_state['student_sign_up_data'] = None
if 'selected_subjects' not in st.session_state: #儲存下拉選單中已選擇科目
    st.session_state['selected_subjects'] = []
if 'cloud_retest_data_manage' not in st.session_state: #儲存"補考資料管理"試算表的雲端資料，內涵補考名單、報名資料
    st.session_state['cloud_retest_data_manage'] = gm.open_google_sheet("補考資料管理")

#---------------------------------------------session_state頁面作動---------------------------------------------
if  st.session_state['stage'] == 'login':
    registration_status = sf.check_registration_status()

    if registration_status[0] == "開放報名" or registration_status[0] == "不限時間":
        sf.login_actions()
    elif registration_status[0] == "尚未開放":
        st.warning("補考報名將在 " + str(registration_status[1]) + " 開始。")
    elif registration_status[0] == "已結束":
        st.warning("補考報名已在 "+ str(registration_status[2]) + " 結束。")
    else:
        st.info("補考報名時間設定未完成，請聯繫管理員。")

elif st.session_state['stage'] == 'retest_form':
    sf.retest_form_actions()

elif st.session_state['stage'] == 'success':
    sf.success_actions()