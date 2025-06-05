#後臺處理的相關函數

import streamlit as st
import pandas as pd
import googlesheet_process as gp
import gspread
import time
import io
import datetime
import page_function as pf

def upload_retest_list_page():
    st.title("上傳補考名單")
    st.info("請上傳補考名單的 Excel 檔案，檔案格式必須為 .xlsx。")

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input', index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    grade = st.session_state.get("grade_input")
    uploaded_file = st.file_uploader("選擇一個 .xlsx 檔案", type=["xlsx"], key='upload_retest_excel_uploader')

    if st.button("確認上傳", key="upload_retest"):
        if uploaded_file is None:
            st.info("請先上傳一個 Excel 檔案。")
            return False
        try:
            try: # 嘗試讀取 Excel 文件，明確指定引擎和工作表
                    df = pd.read_excel(uploaded_file, engine='openpyxl', sheet_name=grade)
            except FileNotFoundError:
                st.error("上傳失敗：找不到指定的 Excel 檔案。")
                return False
            except pd.errors.EmptyDataError:
                st.error("上傳失敗：Excel 檔案為空。")
                return False
            except pd.errors.ParserError:
                st.error("上傳失敗：無法解析 Excel 檔案。請確認檔案格式正確。")
                st.exception(e)
                return False
            except ValueError:
                st.error("上傳失敗：請確認工作表名稱為 1 、2 、 3。")
                return False
            except Exception as e:
                st.error(f"讀取 Excel 檔案時發生未預期的錯誤：{e}")
                st.exception(e)
                return False

            expected_columns = ["班級", "座號", "科目", "必選修", "成績"] # 定義預期欄位，用於數據驗證
            if not all(col in df.columns for col in expected_columns): # 驗證 Excel 檔案是否包含所有必要的欄位
                missing_cols = [col for col in expected_columns if col not in df.columns]
                st.error(f"上傳失敗：Excel 檔案缺少必要的欄位。缺少欄位：{', '.join(missing_cols)}")
                st.warning(f"請確保檔案包含所有預期欄位：{', '.join(expected_columns)}")
                return False

            try: # 獲取目標工作表
                worksheet = gp.get_google_sheet_worksheet("補考名單", grade)
            except Exception as e:
                st.error(f"無法取得 Google Sheet 工作表 '補考名單 - {grade}'，請確認試算表名稱和工作表名稱是否正確，或服務帳戶權限。")
                st.exception(e)
                return False

            status_message_placeholder = st.empty()
            status_message_placeholder.info(f"正在清空 {grade} 年級補考名單並上傳資料中...")
        
            try: # 清空現有資料
                worksheet.clear()
            except gspread.exceptions.APIError as e:
                status_message_placeholder.error(f"清空 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。")
                st.exception(e)
                return False
            except Exception as e:
                status_message_placeholder.error(f"清空 Google Sheet 時發生未預期的錯誤：{e}。")
                st.exception(e)
                return False

            # 將 DataFrame 轉換為列表的列表 (包含標頭行)，以便 gspread 進行更新
            data_to_upload = [df.columns.tolist()] + df.values.tolist()
            try:
                worksheet.update(values=data_to_upload)
                status_message_placeholder.success(f"{grade} 年級補考名單已成功更新！共上傳 {len(df)} 筆資料。")
                time.sleep(2)
                st.rerun()
            except gspread.exceptions.APIError as e:
                status_message_placeholder.error(f"更新 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。")
                st.exception(e)
                return False
            except Exception as e:
                status_message_placeholder.error(f"更新 Google Sheet 時發生未預期的錯誤：{e}")
                st.exception(e)
                return False

        except Exception as e:
            st.error(f"上傳補考名單時發生錯誤：{e}")
            st.exception(e)
            return False
    display_cloud_data(grade,sheet_name="補考名單")

def clear_retest_list_page():
    st.title("清空表單資料")

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        grade = st.selectbox('選擇操作年級', options=["1", "2", "3"], index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"查看 {grade} 年級補考名單", key=f"view_retest_list_btn_{grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'retest_list' # 設定為查看補考名單
            st.rerun() 
    with col2:
        if st.button(f"查看 {grade} 年級補考者報名資料", key=f"view_registrants_data_btn_{grade}", use_container_width=True):
            st.session_state['selected_view_type'] = 'registrants_data' # 設定為查看報名資料
            st.rerun()

    if st.session_state['selected_view_type'] == 'retest_list': sheet_to_view = "補考名單"
    else: sheet_to_view = "補考者報名資料"
    display_cloud_data(grade,sheet_to_view)

    if st.button(f"確認清空 {grade} 年級 {sheet_to_view} 表單資料", key=f"clear_btn_{grade}"):
        try: # 獲取目標工作表
            worksheet = gp.get_google_sheet_worksheet(sheet_to_view, grade)
        
        except Exception as e:
            st.error(f"無法取得 Google Sheet 工作表 '{sheet_to_view} - {grade}'，請確認試算表名稱和工作表名稱是否正確，或服務帳戶權限。")
            st.exception(e)
            return False

        try:
            all_data = worksheet.get_all_values() # 獲取所有資料，包括標題列，以判斷範圍                
            if not all_data or len(all_data) <= 1: # 如果工作表為空或只有標題列，則無需清空
                st.info(f"{grade} 年級補考名單目前沒有資料需要清空 (只有標題或為空)。")
                return True

            header_row = all_data[0]
            num_cols = len(header_row) # 根據標題列的長度來決定要清空的欄位數
            last_row_with_data = len(all_data) # 確定實際有資料的最後一行 (包含標題)
            start_cell_a1 = gspread.utils.rowcol_to_a1(2, 1) # 定義要清空的範圍(A2)
            end_cell_a1 = gspread.utils.rowcol_to_a1(last_row_with_data, num_cols)
            range_to_clear = f"{start_cell_a1}:{end_cell_a1}"
            rows_to_clear_count = last_row_with_data - 1 # 建立一個空的二維列表來填充該範圍
            empty_data_to_fill = [[''] * num_cols for _ in range(rows_to_clear_count)]
            worksheet.update(values=empty_data_to_fill, range_name=range_to_clear)
            st.success(f"{grade} 年級補考名單中的資料已成功清空。")
            time.sleep(2)
            st.rerun()

        except gspread.exceptions.APIError as e:
            st.error(f"清空 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。")
            st.exception(e)
            return False

        except Exception as e:
            st.error(f"清空 Google Sheet 時發生未預期的錯誤：{e}。")
            st.exception(e)
            return False

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
            st.session_state['current_page'] = 'sidebar_claen_registrants'
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
            st.session_state['current_page'] = 'change_password'
            st.rerun()

    st.markdown("---")
    st.header("查看雲端資料")

    view_grade = st.selectbox('選擇查看年級', options=["1", "2", "3"], key='view_data_grade_select', index=0)
    if st.session_state.get('view_data_grade_select') != st.session_state['selected_view_grade']: # 如果 selectbox 的值改變了，更新 session state 並觸發重新渲染
        st.session_state['selected_view_grade'] = st.session_state.get('view_data_grade_select')
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

    if st.session_state['selected_view_type'] == 'retest_list': sheet_to_view = "補考名單"
    else: sheet_to_view = "補考者報名資料"
    display_cloud_data(st.session_state['selected_view_grade'],sheet_to_view)
    
    st.markdown("---")
    if st.button("登出", key="logout_button"):
        st.session_state['admin_logged_in'] = False
        st.session_state['current_page'] = 'login' # 重設頁面到登入頁
        st.info("您已登出。")
        time.sleep(1) # 短暫延遲讓訊息顯示
        st.rerun()

def download_retest_registrants_data_page():
    st.title("下載補考者報名資料")
    registrants_spreadsheet_name = "補考者報名資料"

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        download_grade = st.selectbox('選擇下載年級', options=["1", "2", "3"], key='download_grade_select', index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    try:
        info = st.info(f"正在從 Google Sheet 獲取 {download_grade} 年級補考者報名資料...")
        registrants_worksheet = gp.get_google_sheet_worksheet(registrants_spreadsheet_name, download_grade)
        data = registrants_worksheet.get_all_values()
        info.empty()

        if data:
            df_registrants = pd.DataFrame(data[1:], columns=data[0]) # 將第一行作為欄位名稱，其餘作為資料
            st.dataframe(df_registrants, hide_index=True)
            # 提供下載按鈕
            col3, col4 = st.columns([1, 1], gap="small")
            with col3:
                csv_data = df_registrants.to_csv(index=False).encode('utf-8-sig') # utf-8-sig 支援中文，Excel 可直接開啟
                st.download_button(
                    label=f"下載 {download_grade} 年級補考者報名資料 (CSV)",
                    data=csv_data,
                    file_name=f"補考者報名資料_{download_grade}年級.csv",
                    mime="text/csv",
                    key=f"download_csv_btn_{download_grade}",
                    use_container_width=True
                )
            with col4:
                output = io.BytesIO()
                
                # 使用 ExcelWriter 將 DataFrame 寫入記憶體中的 Excel 檔案
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_registrants.to_excel(writer, index=False, sheet_name=f"{download_grade}年級報名資料")
                xlsx_data = output.getvalue()
                
                st.download_button(
                    label=f"下載 {download_grade} 年級補考者報名資料 (xlsx)",
                    data=xlsx_data,
                    file_name=f"補考者報名資料_{download_grade}年級.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", # Excel 的 MIME 類型
                    key=f"download_xlsx_btn_{download_grade}",
                    use_container_width=True
                )
        else:
            st.warning(f"{download_grade} 年級補考者報名資料中沒有找到資料。")

    except Exception as e:
        st.error(f"下載 {download_grade} 年級補考者報名資料時發生錯誤：{e}")
        st.exception(e)
    st.info("1. 下載的檔案會儲存在本地端的預設下載資料夾中。\n2. 檔案內的時間欄位若為井字號，請將該欄拉寬便能正常顯示。")

def display_cloud_data(view_grade,sheet_name="補考名單"):
    try:
        info = st.info(f"正在從 Google Sheet 獲取 {view_grade} 工作表，來自{sheet_name}檔")
        worksheet = gp.get_google_sheet_worksheet(sheet_name, view_grade)
        data = worksheet.get_all_values()
        info.empty()

        if data:
            df_retest = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df_retest, hide_index=True)
        else:
            st.warning(f"{view_grade} 工作表中沒有找到資料。錯誤檔案：{sheet_name}")
    except Exception as e:
        st.error(f"查看 {view_grade} 發生錯誤。錯誤檔案：{sheet_name}。錯誤訊息：{e}")
        st.exception(e)

def time_set():
    st.title("補考系統開放時間設定")
    info = st.info("預設當日為開始日期，結束日期為一週後。")
    st.session_state['success_info'] = None

    display_cloud_data("補考系統開放時間",sheet_name="補考系統資料管理")
    start_date = st.date_input("開始日期", datetime.date.today())
    start_time = st.time_input("開始時間", datetime.time(8, 0))
    end_date = st.date_input("結束日期", datetime.date.today() + datetime.timedelta(days=7))  # 預設一週後
    end_time = st.time_input("結束時間", datetime.time(17, 0))

    col1, col2 = st.columns([1, 1], gap="small")
    with col1:
        if st.button("儲存設定", use_container_width=True):
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_datetime = datetime.datetime.combine(end_date, end_time)

            if start_datetime <= end_datetime: 
                st.session_state['success_info'] = True
                sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "補考系統開放時間")
                sheet.update_cell(2, 1, start_datetime.strftime("%Y-%m-%d %H:%M:%S"))
                sheet.update_cell(2, 2, end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            else: 
                st.session_state['success_info'] = False
    with col2:
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
    
    if st.session_state['success_info'] == True:
        info = st.success("報名時間設定已儲存！")
        time.sleep(1.5)
        info.empty()
        st.session_state['success_info'] = None
        st.rerun()
    elif st.session_state['success_info'] == False:
        info = st.warning("初始時間不能大於結束時間！")
        time.sleep(1.5)
        info.empty()
        st.session_state['success_info'] = None
        st.rerun()

def retest_seat():
    st.title("生成考生座位表")

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        grade = st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input')
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 教室佈局模式選擇 ---
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("教室佈局：6x6", use_container_width=True, key="layout_6x6"):
            st.session_state['classroom_layout'] = '6x6'
            st.rerun()
    with col2:
        if st.button("教室佈局：6x5", use_container_width=True, key="layout_6x5"):
            st.session_state['classroom_layout'] = '6x5'
            st.rerun()
    
    st.markdown(f"當前教室佈局模式：**{st.session_state['classroom_layout']}**")

    # --- 讀取學生補考數據 ---
    # 通常座位表會針對某個年級，或者所有年級的學生，這裡需要明確如何獲取
    # 假設我們讀取所有年級的補考者報名資料，然後統一處理
    # 您可能需要一個機制來選擇年級，或者將所有年級的數據匯總
    
    # 這裡暫時只讀取一年級的補考資料作為示例
    try:
        # 從 '補考者報名資料' 讀取，它應該包含報名成功的學生信息
        retest_registrants_sheet = gp.get_google_sheet_worksheet("補考者報名資料", "1") # 假設先讀取一年級
        retest_registrants_data = retest_registrants_sheet.get_all_records()
        
        if not retest_registrants_data:
            st.info("目前沒有學生報名補考資料。")
            st.session_state['retest_students_for_seat'] = pd.DataFrame(columns=["班級", "座號", "姓名", "補考科目", "分配座位"])
        else:
            df = pd.DataFrame(retest_registrants_data)
            # 確保補考科目是列表（假設原始數據中是字串，需要轉換回來）
            # 或者，如果它是單個科目，就直接用
            # 如果數據中的「補考科目」列有多個科目，請確保它們是單獨的列或者在讀取時處理為列表
            
            # 這裡需要根據您的 Google Sheet 實際存儲的列名來調整
            # 假設原始數據有 '班級', '座號', '姓名', '科目'
            if '分配座位' not in df.columns:
                df['分配座位'] = '' # 新增一個空欄位供用戶編輯
            
            # 如果有多個科目，可能需要合併或顯示每個科目
            # 示例：將所有科目合併為一個字串顯示
            if '科目' in df.columns:
                # 假設一個學生在 Google Sheet 中有多行記錄，每行一個科目
                # 我們需要將它們按學生聚合
                grouped_df = df.groupby(['班級', '座號', '姓名']).agg(
                    補考科目=('科目', lambda x: ', '.join(x.unique())),
                    分配座位=('分配座位', 'first') # 取第一個分配座位，如果每個科目行都有分配座位
                ).reset_index()
                st.session_state['retest_students_for_seat'] = grouped_df
            else:
                st.session_state['retest_students_for_seat'] = df[['班級', '座號', '姓名', '分配座位']]
                
        # 為了保持編輯狀態，如果之前有編輯過，就用編輯過的數據
        if st.session_state['edited_retest_students_df'] is not None:
             # 合併 edited_df 和原始 df，保留原始df未被編輯的列
             # 僅更新'分配座位'列，或根據你的需求更新其他列
            merged_df = st.session_state['retest_students_for_seat'].set_index(['班級', '座號', '姓名']).combine_first(
                st.session_state['edited_retest_students_df'].set_index(['班級', '座號', '姓名'])
            ).reset_index()
            # 確保 '分配座位' 是字串類型，因為 data_editor 返回的是 object
            merged_df['分配座位'] = merged_df['分配座位'].astype(str).fillna('')
            st.session_state['retest_students_for_seat'] = merged_df


    except Exception as e:
        st.error(f"載入補考學生資料時發生錯誤：{e}")
        st.session_state['retest_students_for_seat'] = pd.DataFrame(columns=["班級", "座號", "姓名", "補考科目", "分配座位"]) # 出錯也給個空DF

    # --- 顯示可編輯表格 ---
    if not st.session_state['retest_students_for_seat'].empty:
        st.subheader("請在此表格中分配座位號 (例如：A1, B3)")
        
        # 使用 data_editor 顯示可編輯表格
        edited_df = st.data_editor(
            st.session_state['retest_students_for_seat'],
            column_config={
                "分配座位": st.column_config.TextColumn(
                    "分配座位",
                    help="輸入座位號，例如 A1, B3",
                    default="",
                    width="medium",
                ),
                # 這裡可以配置其他列的顯示方式，例如班級、座號、姓名設為不可編輯
                "班級": st.column_config.TextColumn("班級", disabled=True),
                "座號": st.column_config.TextColumn("座號", disabled=True),
                "姓名": st.column_config.TextColumn("姓名", disabled=True),
                "補考科目": st.column_config.TextColumn("補考科目", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic", # 允許增刪行（如果需要）
            key="seat_assignment_editor"
        )
        st.session_state['edited_retest_students_df'] = edited_df

        # --- 下載按鈕 ---
        # 這裡可以選擇下載編輯後的學生列表，或者轉換成座位表格式再下載
        # 我會建議先下載編輯後的學生列表，因為它直接包含了用戶分配的座位信息
        @st.cache_data # 緩存下載的數據
        def convert_df_to_excel(df_to_convert, layout_type):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 寫入編輯後的學生列表
                df_to_convert.to_excel(writer, sheet_name='學生座位分配', index=False)
                
                # 可選：生成一個可視化的座位表並寫入另一個工作表
                # 這部分需要根據 '分配座位' 欄位的內容來構建座位表DF
                if not df_to_convert['分配座位'].str.strip().empty:
                    max_row = 6
                    max_col = 6 if layout_type == '6x6' else 5
                    
                    # 創建空的座位表DataFrame
                    seat_map_df = pd.DataFrame(index=range(1, max_row + 1), columns=[chr(65 + i) for i in range(max_col)])
                    
                    for index, row in df_to_convert.iterrows():
                        seat_info = row['分配座位'].strip().upper()
                        if seat_info:
                            try:
                                col_char = seat_info[0]
                                row_num = int(seat_info[1:])
                                
                                if 'A' <= col_char <= chr(65 + max_col - 1) and 1 <= row_num <= max_row:
                                    seat_map_df.loc[row_num, col_char] = f"{row['班級']}-{row['座號']} {row['姓名']}"
                            except (ValueError, IndexError):
                                # 忽略格式不正確的座位號
                                pass
                    seat_map_df.to_excel(writer, sheet_name='座位表佈局', index=True)

            processed_data = output.getvalue()
            return processed_data

        excel_data = convert_df_to_excel(edited_df, st.session_state['classroom_layout'])
        
        st.download_button(
            label="下載座位表 (Excel)",
            data=excel_data,
            file_name=f"考生座位表_{st.session_state['classroom_layout']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("沒有可用的補考學生數據來生成座位表。")

def year_data_manage():
    st.title("年度資料管理")

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        grade = st.selectbox('選擇操作年級', options=["1", "2", "3"], key='grade_input')
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    display_cloud_data(grade,sheet_name="補考者報名資料")

def add_retester():
    if 'student_info' not in st.session_state: st.session_state['student_info'] = None
    if 'grade_input_add_retester_value' not in st.session_state: st.session_state['grade_input_add_retester_value'] = "1"
    if 'class_name_input_add_retester_value' not in st.session_state: st.session_state['class_name_input_add_retester_value'] = "1"
    if 'name_input_value' not in st.session_state: st.session_state['name_input_value'] = ""
    if 'seat_number_input_value' not in st.session_state: st.session_state['seat_number_input_value'] = 1

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
         st.title("手動新增補考學生")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            st.session_state['grade_input_add_retester_value'] = "1"
            st.session_state['class_name_input_add_retester_value'] = "1"
            st.session_state['name_input_value'] = ""
            st.session_state['seat_number_input_value'] = 1
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    col_submit_back = st.columns([1, 1], gap="small")
    with col_submit_back[0]:
        grade_input_list = ["1", "2", "3"]
        st.selectbox('年級',
            options=grade_input_list,
            key='grade_input_add_retester',
            index=grade_input_list.index(st.session_state['grade_input_add_retester_value'])
        )
        st.session_state['grade_input_add_retester_value'] = st.session_state['grade_input_add_retester']
    with col_submit_back[1]:
        class_name_input_input_list = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        st.selectbox('班級',
            options=class_name_input_input_list,
            key='class_name_input_add_retester',
            index=class_name_input_input_list.index(st.session_state['class_name_input_add_retester_value'])
        )
        st.session_state['class_name_input_add_retester_value'] = st.session_state['class_name_input_add_retester']

    st.text_input('姓名', key='name_input', value=st.session_state['name_input_value'])
    st.session_state['name_input_value'] = st.session_state['name_input']
    name = st.session_state['name_input_value']

    st.number_input('座號', min_value=1, step=1, key='seat_number_input', value=st.session_state['seat_number_input_value'])
    st.session_state['seat_number_input_value'] = st.session_state['seat_number_input']
    seat_number = st.session_state['seat_number_input_value']

    grade = st.session_state['grade_input_add_retester_value']
    class_name = st.session_state['class_name_input_add_retester_value']

    retest_data = gp.get_google_sheet_worksheet("補考名單", grade).get_all_records() #儲存補考者名單的檔案
    data_from_retest_list = gp.get_google_sheet_worksheet("補考者報名資料", grade) #儲存補考者報名資料的檔案
    st.session_state['data_from_retest_list'] = data_from_retest_list

    if len(class_name) != 2: grade_class_name = grade + "0" + class_name
    else: grade_class_name = grade + class_name

    if not retest_data: retest_df = pd.DataFrame(columns=["班級","座號","科目","必選修","成績"]) #空表則建立空表單
    else: retest_df = pd.DataFrame(retest_data)

    try:
        student_info_df = retest_df[
            (retest_df['班級'] == int(grade_class_name)) &
            (retest_df['座號'] == int(seat_number))
        ]
        #顯示該生補考資訊
        display_columns = ["班級", "座號", "科目", "必選修", "成績"]
        actual_display_columns = [col for col in display_columns if col in student_info_df.columns] # 過濾出 DataFrame 中實際存在的列，以避免 KeyError
        st.dataframe(student_info_df[actual_display_columns], hide_index=True, use_container_width=True) # hide_index=True 可以隱藏 DataFrame 左側的數字索引

    except Exception as e:
        st.error(f"查詢學生資料時發生錯誤：{e}")
    
    subjects = student_info_df['科目'].tolist()
    subjects_with_all = subjects

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
        if student_info_df.empty:
            st.info('查無學生補考資料，該生可能不需補考。')
        elif not name:
            st.error("請填寫姓名欄位。")
        elif not selected_subjects:
            st.warning('請選擇至少一個要補考的科目。')
        else:
            student_base_info = student_info_df.iloc[0]
            student_common_data = {
                '班級': str(student_base_info['班級']),
                '座號': str(student_base_info['座號']),
                '姓名': name
            }
            if pf.save_retest_records(student_common_data, selected_subjects):
                st.success("已報名成功！")
                time.sleep(1.5)
                st.session_state['grade_input_add_retester_value'] = "1"
                st.session_state['class_name_input_add_retester_value'] = "1"
                st.session_state['name_input_value'] = ""
                st.session_state['seat_number_input_value'] = 1
                st.rerun()

def verify_password_page(pwd_context):
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        st.title("帳號管理")
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True):
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.info("預設帳號：user；預設密碼：pass ")
    username = st.session_state['account']

    password = st.text_input("密碼", type="password", key="verify_password_input")

    if st.button("驗證", key="preunverify"):
        log_in_data = load_admin_credentials_from_sheet(st.session_state['account'])

        if log_in_data and verify_password(pwd_context, username, password, log_in_data["password"]):
            success = st.success("驗證成功！")
            time.sleep(1)
            success.empty() # 清空訊息
            st.session_state['change_password_page'] = "verify"
            st.rerun()
        else: 
            error = st.error("帳號或密碼錯誤，請重新驗證。")
            time.sleep(2)
            error.empty()

    st.warning("請先驗證當前帳號密碼。")

def account_management_page(pwd_context):
    st.title("帳號管理")
    st.info("預設帳號：user；預設密碼：pass ")

    display_cloud_data("登入帳密",sheet_name="補考系統資料管理")
    account_management_list = ["更改密碼", "新增帳號", "刪除帳號"]

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        account_management_state = st.selectbox('帳號密碼管理功能', options = account_management_list, index=0)
    with col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("回到首頁", key="back_to_home_from_upload", use_container_width=True): 
            st.session_state['current_page'] = 'home'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

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
        change_password(pwd_context)
    elif st.session_state['account_management_page'] == "新增帳號":
        add_user_account(pwd_context)
    elif st.session_state['account_management_page'] == "刪除帳號":
        delete_user_account()

def hash_password(pwd_context, password: str) -> str:
    return pwd_context.hash(password)

def verify_password(pwd_context, username, plain_password: str, hashed_password: str) -> bool:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username", "admin_user")
    ADMIN_PASSWORD = st.secrets.get("admin", {}).get("password", "admin_pass")
    try:
        if plain_password == ADMIN_PASSWORD and username == ADMIN_USERNAME: # 如果是 admin 帳號，則直接返回 True
            return True
        return pwd_context.verify(plain_password, hashed_password) #hashed_password：雲端的密碼
    except ValueError:
        return False
    
def start_password(pwd_context):
    try:
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        password = hash_password(pwd_context, "pass")
        if sheet.cell(2, 2).value == None:
            sheet.update_cell(2, 1, "user")
            sheet.update_cell(2, 2, password)
            sheet.update_cell(2, 3, password)
    except Exception as e:
        st.error(f"讀取補考系統資料管理檔案失敗: {e}")

def load_admin_credentials_from_sheet(username: str) -> dict:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username", "admin_user")
    ADMIN_PASSWORD = st.secrets.get("admin", {}).get("password", "admin_pass")
    
    try:
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        data = sheet.get_all_values()  # 讀取整個工作表
        PRE_PASSWORD_HASH_COLUMN = 3
        PASSWORD_HASH_COLUMN = 2
        USERNAME_COLUMN = 1

        if username == ADMIN_USERNAME: # 如果是 admin 帳號，則直接返回預設密碼
            return {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        else:
            for row in data:
                if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == username:
                    if row[PASSWORD_HASH_COLUMN - 1] == row[PRE_PASSWORD_HASH_COLUMN - 1]:
                        return {"username": row[USERNAME_COLUMN - 1], "password": row[PASSWORD_HASH_COLUMN - 1], "pre_password": True}
                    else:
                        return {"username": row[USERNAME_COLUMN - 1], "password": row[PASSWORD_HASH_COLUMN - 1], "pre_password": False}
        
            error = st.error(f"找不到帳號")
            time.sleep(2)
            error.empty()
            return None  # 找不到帳號
    except Exception as e:
        error = st.error(f"讀取補考系統資料管理檔案失敗: {e}")
        time.sleep(2)
        error.empty()
        return None

def save_admin_password_to_sheet(username: str, new_password_hash: str) -> bool:
    ADMIN_USERNAME = st.secrets.get("admin", {}).get("username", "admin_user")
    usernames = st.session_state['account']
    try:
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        data = sheet.get_all_values() #返回列表
        PASSWORD_HASH_COLUMN = 2
        USERNAME_COLUMN = 1

        for i, row in enumerate(data):
            if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == username:
                sheet.update_cell(i + 1, PASSWORD_HASH_COLUMN, new_password_hash)  # 更新密碼雜湊值
                if usernames != ADMIN_USERNAME:
                    sheet.update_cell(i + 1, PASSWORD_HASH_COLUMN + 1, new_password_hash)
                return True
        return False  # 找不到帳號
    except Exception as e:
        st.error(f"儲存管理員密碼失敗: {e}")
        return False
    
def change_password(pwd_context):
    st.header("更改密碼")
    
    username = st.session_state['account']
    is_ADMIN_USERNAME = False

    if username == st.secrets['admin']['username']:
        st.warning("請注意：無法更改 admin 帳號的密碼")
        display_cloud_data("登入帳密",sheet_name="補考系統資料管理")
        username  = st.text_input("輸入更動帳號", key="account _input")
        is_ADMIN_USERNAME = True

    new_password = st.text_input("輸入新密碼", type="password", key="new_password_input")
    confirm_new_password = st.text_input("確認新密碼", type="password", key="confirm_new_password_input")

    if st.button("確認更改密碼", key="change_password_submit"):
        if not new_password or not confirm_new_password:
            st.error("請填寫所有密碼欄位。")
            return  # 結束函式執行
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

        try:
            new_password_hash = hash_password(pwd_context, new_password)
            if save_admin_password_to_sheet(username, new_password_hash):
                if is_ADMIN_USERNAME == False:
                    st.success("密碼已成功更改！請使用新密碼重新登入。")
                    st.session_state['admin_logged_in'] = False
                    st.session_state['current_page'] = 'login'
                    time.sleep(1)
                    st.rerun()
                else:
                    st.success(f"{username}帳號的密碼已成功更改！")
                    time.sleep(2)
                    st.session_state['current_page'] = 'home'
                    st.rerun()
            else:
                if is_ADMIN_USERNAME == True: error = st.error("保存新密碼失敗，admin不能更改帳密。")
                else: st.error("保存新密碼失敗，請重試。")
                time.sleep(2)
                error.empty()
        except Exception as e:
            st.error(f"發生錯誤：{e}")

def add_user_account(pwd_context):
    import re

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
        if not re.search(r"[A-Z]", new_password) or not re.search(r"[0-9]", new_password) or not re.search(r"[!@#$%^&*]", new_password):
            st.error("新密碼必須包含大寫字母、數字和特殊字元。")
            return
        
        sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
        data = sheet.get_all_values()  # 讀取整個工作表
        PASSWORD_HASH_COLUMN = 2
        USERNAME_COLUMN = 1

        if new_username == st.secrets['admin']['username']: # 如果是 admin 帳號，則直接返回預設密碼
            st.error("不能使用 admin 帳號名稱，請使用其他名稱。")
            return
        else:
            for row in data:
                if len(row) >= PASSWORD_HASH_COLUMN and row[USERNAME_COLUMN - 1] == new_username:
                    st.error(f"使用者名稱 '{new_username}' 已存在，請使用其他名稱。")
                    return
        try:
            hashed_password = hash_password(pwd_context, new_password)
            if sheet.append_row([new_username, hashed_password, hashed_password]):
                st.success(f"帳號 '{new_username}' 新增成功！")
                time.sleep(2)
                st.session_state['current_page'] = 'home'
                st.rerun()
            else:
                st.error("新增帳號失敗，請重試。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")

def delete_user_account():
    usernames = []

    st.header("刪除帳號")

    sheet = gp.get_google_sheet_worksheet("補考系統資料管理", "登入帳密")
    data = sheet.get_all_values()  # 讀取整個工作表
    USERNAME_COLUMN = 1
    
    for row in data:
        # 避免刪除預設帳號和當前登入的帳號及欄名稱(使用者名稱)
        if row[USERNAME_COLUMN - 1] != "user" and row[USERNAME_COLUMN - 1] != st.session_state['account'] and row[USERNAME_COLUMN - 1] != "使用者名稱":
            usernames.append(row[USERNAME_COLUMN - 1]) # 將所有使用者名稱加入列表

    username_to_delete = st.selectbox("請選擇要刪除的帳號", usernames)

    if st.button(f"確定刪除帳號 '{username_to_delete}'", icon="⚠️", key=f"confirm_delete_{username_to_delete}"):
        try:
            if gp.delete_user_from_sheet(username_to_delete, "補考系統資料管理", "登入帳密", 1):
                st.success(f"帳號 '{username_to_delete}' 已成功刪除！")
                time.sleep(2)
                st.rerun()
            else:
                st.error("刪除帳號失敗，請重試。")
        except Exception as e:
            st.error(f"發生錯誤：{e}")

    if st.session_state['account'] == st.secrets['admin']['username']:
        st.warning(f"請注意：無法刪除 {st.secrets['admin']['username']} 、 user 帳號。")
    else:
        st.warning("請注意：無法刪除 user 及當前登入的帳號。")

def first_change_password(pwd_context):
    change_password(pwd_context)
    st.info("您使用預設密碼登入，請更改您的密碼。")