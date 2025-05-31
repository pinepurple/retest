#控制頁面的相關函式

import streamlit as st
import pandas as pd
import datetime
import time
import googlesheet_process as gp
import pytz

def save_retest_records(student_common_data, selected_subjects_list): #將資料上傳googlesheet
    # 從 session_state 中獲取用於儲存報名資料的 Worksheet 物件
    data_from_retest_list = st.session_state.get('data_from_retest_list')

    # 檢查工作表是否已成功載入，如果沒有，可能是用戶未登入或發生錯誤
    if data_from_retest_list is None:
        st.error("錯誤：報名工作表未正確載入。請重新登入。")
        st.session_state['stage'] = 'login' # 強制返回登入頁面
        st.rerun() # 重新運行以更新介面
        return # 退出函式，避免後續錯誤
    
    try:
        Class = str(student_common_data.get('班級', ''))
        seat = str(student_common_data.get('座號', ''))
        name = str(student_common_data.get('姓名', ''))
        
        taiwan_tz = pytz.timezone('Asia/Taipei') #取得台灣時區
        now_in_taiwan = datetime.datetime.now(taiwan_tz)
        Time = now_in_taiwan.strftime("%Y-%m-%d %H:%M:%S")
        
        for subject in selected_subjects_list: # 對每個選定的科目進行迴圈，逐一寫入 Google Sheet
            row_data = [Class, seat, subject, Time, name] # 構建要寫入的行資料
            data_from_retest_list.append_row(row_data) # 將資料以列表形式添加到工作表末尾
        return True
    except Exception as e:
        st.error(f"儲存報名資料時發生錯誤：{e}")
        return False

def login_action(): #登入頁面
    class_name = st.session_state.get('class_name_input') #班級
    seat_number = st.session_state.get('seat_number_input') #座號
    grade = st.session_state.get('grade_input') #年級
    name = st.session_state.get('name_input') #姓名

    st.session_state['show_no_data_message'] = False # 在每次嘗試登入時，先將訊息標記重置為 False

    st.session_state['name'] = name
    retest_data = gp.get_google_sheet_worksheet("補考名單", grade).get_all_records() #儲存補考者名單的檔案
    data_from_retest_list = gp.get_google_sheet_worksheet("補考者報名資料", grade) #儲存補考者報名資料的檔案
    st.session_state['data_from_retest_list'] = data_from_retest_list
    
    if len(class_name) != 2: grade_class_name = grade + "0" + class_name
    else: grade_class_name = grade + class_name

    if not retest_data: #資料為空表
        retest_df = pd.DataFrame(columns=["班級","座號","科目","必選修","成績"]) #建立空表單
    else:
        retest_df = pd.DataFrame(retest_data)

    try:
        student_info_df = retest_df[
            (retest_df['班級'] == int(grade_class_name)) &
            (retest_df['座號'] == int(seat_number))
        ]
        if not student_info_df.empty:
            st.session_state['student_info'] = student_info_df
            st.session_state['stage'] = 'retest_form'
        else:
            st.session_state['student_info'] = None
            st.session_state['show_no_data_message'] = True
    except Exception as e:
        st.error(f"查詢學生資料時發生錯誤：{e}")

def login_actions():
    st.title('學生補考報名')
    col_submit_back = st.columns([1, 1], gap="small")
    with col_submit_back[0]:
        st.selectbox('年級', options=["1", "2", "3"], key='grade_input')
    with col_submit_back[1]:
        st.selectbox('班級', options=["1", "2", "3","4", "5", "6","7", "8", "9","10"], key='class_name_input')
    
    name = st.text_input('姓名', key='name_input')
    st.number_input('座號', min_value=1, step=1, key='seat_number_input')
    
    if st.button('登入'):
        if not name:
            st.error("請填寫姓名欄位。")
            return
        login_action()
        st.rerun()

    if st.session_state['show_no_data_message']:
        st.info('查無您的補考資料，您不需要補考。')
        st.session_state['show_no_data_message'] = False # 顯示後立即重置標記，避免在下次重新運行時重複顯示

def back_front_page():
    # 清除 'selected_subjects' 狀態，確保返回首頁時選擇是空的
    st.session_state.update({'stage': 'login', 'student_info': None})

def retest_form_actions():
    student_data = st.session_state['student_info']
    subjects = student_data['科目'].tolist()
    subjects_with_all = subjects

    col_submit_back = st.columns([3, 1], gap="small")
    with col_submit_back[0]:
        st.title('學生補考報名')
    with col_submit_back[1]:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        st.button('返回首頁',on_click=back_front_page, key='back_button', use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    #顯示該生補考資訊
    display_columns = ["班級", "座號", "科目", "必選修", "成績"]
    actual_display_columns = [col for col in display_columns if col in student_data.columns] # 過濾出 DataFrame 中實際存在的列，以避免 KeyError
    st.dataframe(student_data[actual_display_columns], hide_index=True, use_container_width=True) # hide_index=True 可以隱藏 DataFrame 左側的數字索引

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        selected_subjects = st.multiselect(
            '請選擇要報名的補考科目:',
            subjects_with_all,
            key='selected_subjects', # 使用 key 將選擇綁定到 session_state
        )
    with col2:
        def select_all_callback():
            # 當「全選」按鈕被點擊時，直接將所有科目設置到 `selected_subjects` 的 session_state 中
            st.session_state['selected_subjects'] = subjects_with_all
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        st.button('全選補考科目', use_container_width=True, key='select_all_button', on_click=select_all_callback)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button('確認報名'):
        confirm(selected_subjects,student_data)

def confirm(selected_subjects,student_data):
    if not selected_subjects:
        st.warning('請選擇至少一個要補考的科目。')
    else:
        student_base_info = student_data.iloc[0]
        student_common_data = {
            '班級': str(student_base_info['班級']),
            '座號': str(student_base_info['座號']),
            '姓名': st.session_state['name']
        }
        if save_retest_records(student_common_data, selected_subjects):
            st.success('已報名成功！')
            time.sleep(2)  # 顯示 2 秒
            st.session_state['stage'] = 'success'
            st.session_state['student_info'] = None
            st.session_state.pop('target_registration_sheet', None)
            st.rerun()

def success_actions():
    st.title('報名成功')
    st.write('您已成功報名補考！')
    st.button('返回首頁', on_click=back_front_page, key='back_button')

def check_registration_status():
    sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "補考系統開放時間")
    start_time_str = sheet.cell(2, 1).value
    end_time_str = sheet.cell(2, 2).value

    # 將字串解析為 naive datetime 物件
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