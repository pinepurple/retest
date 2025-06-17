import streamlit as st, pandas as pd, datetime, time, googlesheet_manage as gm, pytz

@st.cache_data(ttl=3600)
def check_registration_status():
    cloud_retest_system_manage = gm.open_google_sheet("補考系統資料管理")
    work_sheet = gm.open_google_sheet_worksheet(cloud_retest_system_manage, "補考系統開放時間")
    start_time_str = work_sheet.cell(2, 1).value
    end_time_str = work_sheet.cell(2, 2).value

    # 將字串解析為 naive datetime 物件
    if start_time_str != "不限時間":
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

        taiwan_tz = pytz.timezone('Asia/Taipei') #取得台灣時區
        now_in_taiwan = datetime.datetime.now(taiwan_tz)

        # 將 naive datetime 物件轉換為帶有時區的 aware datetime 物件(確保比較時考慮到時區)
        # naive datetime 物件不包含時區資訊，而 aware datetime 物件則包含時區資訊，兩者不能比較。
        start_time_aware = taiwan_tz.localize(start_time)
        end_time_aware = taiwan_tz.localize(end_time)

        if start_time_aware <= now_in_taiwan <= end_time_aware:
            return ["開放報名", start_time, end_time]
        elif now_in_taiwan < start_time_aware:
            return ["尚未開放", start_time, end_time]
        else:
            return ["已結束", start_time, end_time]
    else:
        return ["不限時間", None, None]
    
def login_actions():
    st.title('學生補考報名')
    col = st.columns([1, 1], gap="small")
    with col[0]:
        grade = st.selectbox('年級', options=["1", "2", "3"], key='grade_input')
    with col[1]:
        class_name = st.selectbox('班級', options=["1", "2", "3","4", "5", "6","7", "8", "9","10"], key='class_name_input')
    
    name = st.text_input('姓名', key='name_input')
    seat_number = st.number_input('座號', min_value=1, step=1, key='seat_number_input')
    
    if st.button('登入'):
        if not name:
            st.error("請填寫姓名欄位。")
        elif gm.find_student_in_sheet(grade, class_name, seat_number, name):
            st.session_state['stage'] = 'retest_form'
            st.rerun()

def retest_form_actions():
    col = st.columns([3, 1], gap="small")
    with col[0]:
        st.title('學生補考報名')
    with col[1]:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        st.button('返回首頁',on_click=back_front_page, key='back_button', use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if gm.student_sign_up():
        st.success('已報名成功！')
        time.sleep(1)
        st.session_state['student_data'] = None
        st.session_state['stage'] = 'success'
        st.rerun()

def success_actions():
    st.title('報名成功')
    st.write('您已成功報名補考！')
    st.button('返回首頁', on_click=back_front_page, key='back_button')

def back_front_page():
    st.session_state.update({'stage': 'login', 'student_data': None})
