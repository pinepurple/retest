import pandas as pd

try:
    df = pd.read_excel('retest_data.xlsx', sheet_name='Sheet1')
except FileNotFoundError:
    print("找不到 retest_data.xlsx 這個檔案！請確認檔案是否存在。")
    df = None
    raise FileNotFoundError('找不到 retest_data.xlsx 這個檔案！請確認檔案是否存在。')

#----------------------------------------------------------------------------------------
import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 初始化 session_state
if 'stage' not in st.session_state:
    st.session_state['stage'] = 'login'
if 'student_info' not in st.session_state:
    st.session_state['student_info'] = None

@st.cache_data
def load_retest_data():
    try:
        df = pd.read_excel('retest_data.xlsx', sheet_name='Sheet1')
        print("成功讀取補考名單資料！")
        return df
    except FileNotFoundError:
        st.error("找不到 retest_data.xlsx 這個檔案！請確認檔案是否存在。")
        return None

retest_df = load_retest_data()

def save_retest_records(data):
    df = pd.DataFrame([data])
    try:
        existing_df = pd.read_excel('補考者資料檔.xlsx')
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_excel('補考者資料檔.xlsx', index=False)
        success_container = st.empty()
        success_container.success('已報名成功！')
        time.sleep(2)  # 顯示 2 秒
        st.session_state['stage'] = 'success'
        st.session_state['student_info'] = None
        st.rerun()
    except FileNotFoundError:
        df.to_excel('補考者資料檔.xlsx', index=False)
        success_container = st.empty()
        success_container.success('已報名成功！')
        time.sleep(2)
        st.session_state['stage'] = 'login'
        st.session_state['student_info'] = None
        st.rerun()
    except Exception as e:
        st.error(f"儲存報名資料時發生錯誤：{e}")

def login_action():
    student_id = st.session_state.get('student_id_input')
    class_name = st.session_state.get('class_name_input')
    seat_number = st.session_state.get('seat_number_input')

    if retest_df is not None and student_id and class_name and seat_number is not None:
        student_info_df = retest_df[
            (retest_df['學號'] == int(student_id)) &
            (retest_df['班級'] == int(class_name)) &
            (retest_df['座號'] == int(seat_number))
        ]
        if not student_info_df.empty:
            st.session_state['student_info'] = student_info_df.iloc[0].to_dict()
            st.session_state['stage'] = 'retest_form'
        else:
            st.session_state['student_info'] = None
            st.info('查無您的補考資料，您不需要補考。')
    else:
        st.warning('請輸入完整的學號、班級和座號。')

if st.session_state['stage'] == 'login':
    st.title('補考報名系統')
    st.text_input('學號:', key='student_id_input')
    st.text_input('班級:', key='class_name_input')
    st.number_input('座號:', min_value=0, step=1, key='seat_number_input')
    st.button('登入', on_click=login_action)

elif st.session_state['stage'] == 'retest_form':
    if st.session_state['student_info']:
        student_data = st.session_state['student_info']
        name = student_data['姓名']
        original_score = student_data['原始分數']
        subjects = student_data['科目'].split('、')
        subjects_with_all = subjects

        col_submit_back = st.columns([3, 1], gap="small") # 創建兩個等寬的列
        with col_submit_back[0]:        
            st.title('補考報名系統')
        with col_submit_back[1]:
            st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
            st.button('返回首頁',on_click=lambda: st.session_state.update({'stage': 'login', 'student_info': None}), key='back_button', use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader(f'學生姓名: {name}')
        st.write(f'原始分數: {original_score}')

        container = st.container()
        with container:
            col1, col2 = st.columns([3, 1], gap="small")
            with col1:
                default_subjects = []
                if st.session_state.get('select_all_clicked', False):
                    default_subjects = subjects_with_all
                else:
                    default_subjects = st.session_state.get('selected_subjects', [])
                
                selected_subjects = st.multiselect(
                    '請選擇要報名的補考科目:', 
                    subjects_with_all, 
                    key='selected_subjects', 
                    default=default_subjects
                )
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