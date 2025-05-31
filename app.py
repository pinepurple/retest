#頁面主控制區
#相關安裝包與指令：
#pip freeze > requirements.txt 取得需求列表
#pip install pytz streamlit pandas openpyxl passlib bcrypt
#pip install --upgrade bcrypt passlib #更新 bcrypt 與 passlib
#streamlit run app.py 本地執行
#部屬：https://share.streamlit.io/ 記得先將所有程式放到github上
#本地執行時記得將金鑰放到 .streamlit/secrets.toml (用generate_secrets.py 產生)
#部屬時記得將金鑰放到 Streamlit Cloud 的 Secrets 頁面中
#在vscode中選擇解譯器：上方搜尋中輸入 > Python: Select Interpreter
#---------------------------------------------虛擬機創建--------------------------------------------------------
#python -m venv .venv ：創建虛擬機
#.venv\Scripts\Activate.ps1 ：啟動虛擬機(PowerShell，記得創建完成後要重裝套件)
#在vscode上列搜尋部分輸入">"，選取編譯器
#deactivate ：關閉虛擬機
#pip freeze > requirements.txt ：取得需求列表
#pip install -r requirements.txt ：安裝需求列表
#Get-ExecutionPolicy : 查看當前執行策略(以系統管理員身份執行PowerShell)
#Set-ExecutionPolicy RemoteSigned : 設定執行策略(以系統管理員身份執行PowerShell)

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
if 'name' not in st.session_state:
    st.session_state['name'] = ""

#---------------------------------------------session_state頁面作動---------------------------------------------
if  st.session_state['stage'] == 'login':
    registration_status = pf.check_registration_status()

    if registration_status[0] == "開放報名":
        pf.login_actions() #登入頁面
    elif registration_status[0] == "尚未開放":
        st.warning("補考報名將在 " + str(registration_status[1]) + " 開始。")
    elif registration_status[0] == "已結束":
        st.warning("補考報名已在 "+ str(registration_status[2]) + " 結束。")
    else:
        st.info("補考報名時間設定未完成，請聯繫管理員。")

elif st.session_state['stage'] == 'retest_form':
    pf.retest_form_actions()

elif st.session_state['stage'] == 'success':
    pf.success_actions() #報名成功頁面