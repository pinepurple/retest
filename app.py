import streamlit as st
import pandas as pd
from datetime import datetime
import time
import googlesheet_process as gp

#---------------------------------------------函式定義----------------------------------------------
def save_retest_records(registration_data): #將資料上傳googlesheet
    # 從 session_state 中獲取用於儲存報名資料的 Worksheet 物件
    data_from_retest_list = st.session_state.get('data_from_retest_list')

    # 檢查工作表是否已成功載入，如果沒有，可能是用戶未登入或發生錯誤
    if data_from_retest_list is None:
        st.error("錯誤：報名工作表未正確載入。請重新登入。")
        st.session_state['stage'] = 'login' # 強制返回登入頁面
        st.rerun() # 重新運行以更新介面
        return # 退出函式，避免後續錯誤
    
    try:
        row_data = [
            registration_data.get('學號', ''),
            registration_data.get('班級', ''),
            registration_data.get('座號', ''),
            registration_data.get('姓名', ''),
            registration_data.get('補考科目', ''),
            registration_data.get('報名時間', '')
        ]
        data_from_retest_list.append_row(row_data) # 將資料以列表形式添加到工作表末尾
        success_container = st.empty()
        success_container.success('已報名成功！')
        time.sleep(2)  # 顯示 2 秒
        st.session_state['stage'] = 'success'
        st.session_state['student_info'] = None
        st.session_state.pop('target_registration_sheet', None) #報名成功後清除緩存的工作表，讓下次登入重新載入
        st.rerun()
    except Exception as e:
        st.error(f"儲存報名資料時發生錯誤：{e}")

def login_action(): #登入頁面
    student_id = st.session_state.get('student_id_input')
    class_name = st.session_state.get('class_name_input')
    seat_number = st.session_state.get('seat_number_input')
    grade = st.session_state.get('grade_input')

    retest_data = gp.get_google_sheet_worksheet(gc_instance, "補考名單", st.session_state.get('grade_input')).get_all_records() #儲存補考者名單的檔案
    data_from_retest_list = gp.get_google_sheet_worksheet(gc_instance, "補考者報名資料", st.session_state.get('grade_input')) #儲存補考者報名資料的檔案
    st.session_state['data_from_retest_list'] = data_from_retest_list

    if not retest_data: #資料為空表
        retest_df = pd.DataFrame(columns=['學號', '班級', '座號', '姓名', '科目', '原始分數']) #建立空表單
    else:
        retest_df = pd.DataFrame(retest_data)

    if retest_df is not None and student_id and class_name and seat_number is not None:
        try:
            student_info_df = retest_df[
                (retest_df['學號'] == int(student_id)) &
                (retest_df['班級'] == int(class_name)) &
                (retest_df['座號'] == int(seat_number)) &
                (retest_df['年級'] == str(grade))
            ]
            if not student_info_df.empty:
                st.session_state['student_info'] = student_info_df.iloc[0].to_dict()
                st.session_state['stage'] = 'retest_form'
            else:
                st.session_state['student_info'] = None
                st.info('查無您的補考資料，您不需要補考。')
        except ValueError:
            st.warning("請以數字型式輸入。")
    else:
        st.warning('請輸入完整的學號、年級、班級和座號。')

#---------------------------------------------初始化-----------------------------------------------------------
st.set_page_config(page_title="補考報名系統", page_icon="clipboard")
gc_instance = gp.get_gspread_client()

#---------------------------------------------初始化session_state---------------------------------------------
if 'stage' not in st.session_state: st.session_state['stage'] = 'login'
if 'student_info' not in st.session_state: st.session_state['student_info'] = None
if 'data_from_retest_list' not in st.session_state:
    st.session_state['data_from_retest_list'] = None

#---------------------------------------------session_state頁面作動---------------------------------------------
if st.session_state['stage'] == 'login':
    st.title('補考報名系統')
    st.text_input('學號:', key='student_id_input')
    
    col1, col2 = st.columns([1, 1], gap="small")
    with col1:
        st.selectbox('年級', options=["一年級","二年級","三年級"], key='grade_input')
    with col2:
            st.selectbox('班級', options=list(range(1, 11)), key='class_name_input')

    st.number_input('座號:', min_value=0, step=1, key='seat_number_input')
    st.button('登入', on_click=login_action)

elif st.session_state['stage'] == 'retest_form':
    if st.session_state['student_info']:
        student_data = st.session_state['student_info']
        name = student_data['姓名']       
        subjects = student_data['科目'].split('、')
        subjects_with_all = subjects

        col_submit_back = st.columns([3, 1], gap="small")
        with col_submit_back[0]:        
            st.title('補考報名系統')
        with col_submit_back[1]:
            st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
            st.button('返回首頁',on_click=lambda: st.session_state.update({'stage': 'login', 'student_info': None}), key='back_button', use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader(f'學生姓名: {name}')

        container = st.container()
        with container:
            col1, col2 = st.columns([3, 1], gap="small")
            with col1:
                default_subjects = []
                if st.session_state.get('select_all_clicked', False):
                    default_subjects = subjects_with_all
                else:
                    default_subjects = st.session_state.get('selected_subjects', [])
 
                selected_subjects = st.multiselect('請選擇要報名的補考科目:', subjects_with_all, key='selected_subjects', default=default_subjects)
                st.session_state['select_all_clicked'] = False

            with col2:
                def select_all():
                    st.session_state['select_all_clicked'] = True
                    st.session_state['rerun_flag'] = not st.session_state.get('rerun_flag', False) # 觸發重新渲染
                
                st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
                st.button('全選補考科目', use_container_width=True, key='select_all_button', on_click=select_all)
                st.markdown("</div>", unsafe_allow_html=True)

        if st.button('確認報名'):
            selected_subjects = st.session_state.get('selected_subjects', [])
            if not selected_subjects:
                st.warning('請選擇至少一個要補考的科目。')
            else:
                registration_data = {
                    '學號': student_data['學號'],
                    '班級': student_data['班級'],
                    '座號': student_data['座號'],
                    '姓名': name,
                    '補考科目': '、'.join(selected_subjects),
                    '報名時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_retest_records(registration_data)

elif st.session_state['stage'] == 'success':
    st.title('報名成功')
    st.write('您已成功報名補考！')
    st.button('返回首頁', on_click=lambda: st.session_state.update({'stage': 'login', 'student_info': None}), key='back_button')