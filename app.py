#頁面主控制區
#相關安裝包與指令：
#pip freeze > requirements.txt 取得需求列表
#pip install pytz
#pip install streamlit pandas openpyxl
#streamlit run retest_app.py 本地執行
#部屬：https://share.streamlit.io/ 記得先將所有程式放到github上
#本地執行時記得將金鑰放到 .streamlit/secrets.toml (用generate_secrets.py 產生)
#部屬時記得將金鑰放到 Streamlit Cloud 的 Secrets 頁面中

import streamlit as st
import page_function as pf
#---------------------------------------------初始化-----------------------------------------------------------
st.set_page_config(page_title="補考報名系統", page_icon="clipboard")
if 'stage' not in st.session_state: st.session_state['stage'] = 'login' #初始頁面為登入頁面，stage用來控制頁面切換
if 'student_info' not in st.session_state: st.session_state['student_info'] = None
if 'data_from_retest_list' not in st.session_state:
    st.session_state['data_from_retest_list'] = None
if 'selected_subjects' not in st.session_state: #初始化 selected_subjects 狀態，確保它在第一次渲染時是存在的
    st.session_state['selected_subjects'] = []
if 'show_no_data_message' not in st.session_state:
    st.session_state['show_no_data_message'] = False

#---------------------------------------------session_state頁面作動---------------------------------------------
if  st.session_state['stage'] == 'login':
    pf.login_actions() #登入頁面

elif st.session_state['stage'] == 'retest_form':
    pf.retest_form_actions()

elif st.session_state['stage'] == 'success':
    pf.success_actions() #報名成功頁面