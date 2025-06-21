import json, pytz, gspread, streamlit as st, datetime, pandas as pd, io
#-------------------------------------------goodsheet金鑰認證----------------------------------------------------
@st.cache_resource(ttl=3600) # # 緩存 gspread 客戶端，緩存 1 小時
def get_gspread_client():
    if "gsheets" not in st.secrets:
        st.error("錯誤：未設定 Google Sheets 服務帳戶金鑰。請告知管理者檢查 .streamlit/secrets.toml。")
        st.stop()
    try:
        json_credentials = st.secrets["gsheets"]["service_account_json"]
        creds_dict = json.loads(json_credentials) # 將 JSON 字串轉換為字典
        gc = gspread.service_account_from_dict(creds_dict) # 使用 gspread 的 service_account_from_dict 方法獲取客戶端
        return gc
    except json.JSONDecodeError:
        st.error("錯誤：服務帳戶金鑰 JSON 格式無效。請檢查 .streamlit/secrets.toml。")
        st.stop()
    except Exception as e:
        st.error(f"認證失敗：{e}")
        st.stop()

#-------------------------------------------goodsheet檔案管理--------------------------------------------------------
@st.cache_resource(ttl=3600) # 緩存工作表物件，緩存 1 小時
def open_google_sheet(sheet_name): #檔案開啟
    gc_client = get_gspread_client()
    try:
        spreadsheet = gc_client.open(sheet_name) # 開啟 Google_sheet
        return spreadsheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"錯誤：找不到名為 '{sheet_name}' 的 Google Sheet 檔案。")
        st.warning("請告知管理者確認該檔案是否存在於 Google Drive 中，且已共享給服務帳戶郵件地址。")
        st.stop()
    except Exception as e:
        st.error(f"無法開啟或存取 Google Sheet，請告知管理者確認Google Sheet情況：{e}")
        st.stop()

def open_google_sheet_worksheet(sheet_name, worksheet_name): #工作表開啟
    try:
        worksheet = sheet_name.worksheet(worksheet_name) # 選取指定名稱的工作表
        return worksheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"錯誤：找不到名為 '{sheet_name}' 的 Google Sheet 檔案。")
        st.warning("請告知管理者確認該檔案是否存在於 Google Drive 中，且已共享給服務帳戶郵件地址。")
        st.stop()
    except Exception as e:
        st.error(f"無法開啟或存取 Google Sheet，請告知管理者確認Google Sheet情況：{e}")
        st.stop()

def save_to_google_sheet(data_list, sheet_name, worksheet_name): #將資料上傳googlesheet
    worksheet = open_google_sheet_worksheet(sheet_name, worksheet_name) #儲存補考者報名資料的檔案
    try:
        if len(data_list) != 5:
            change_row = data_list[len(data_list) - 1] # 最後一個元素是要更新的行數
            data_list.pop() # 移除最後一個元素，因為它是行數，不需要更新
            worksheet.update(f'A{change_row}:C{change_row}', [data_list])
        else:
            for subject in data_list[2]: #在學生的補考資料中，data_list[2]是科目列表
                data_list[2] = subject
                #print(data_list)
                worksheet.append_row(data_list)
        return True
    except Exception as e:
        st.error(f"儲存報名資料時發生錯誤：{e}")
        return False
    
def upload_to_google_sheet(auto, grade_list, uploaded_file, file_type):    
    if uploaded_file is None:
        return "請先上傳一個 Excel 檔案。"
    try:
        worksheet_list = []
        df_list = []
        for grade in grade_list:
            try:
                worksheet = open_google_sheet_worksheet(st.session_state['cloud_retest_data_manage'], grade + '年級補考名單')
                worksheet_list.append(worksheet)
            except Exception as e:
                return f"無法取得 Google Sheet 工作表 '補考名單 - {grade}'，請確認試算表名稱和工作表名稱是否正確，或服務帳戶權限。 {e}"

        try: # 讀取 Excel 文件，明確指定引擎和工作表
            if file_type == 'xlsx' and auto:
                dfs_dict = pd.read_excel(uploaded_file, engine='openpyxl', sheet_name=None) #建議不要有太多工作表，可能消耗太多記憶體資源
                all_sheet_names = list(dfs_dict.keys()) # 獲取所有工作表名稱的列表

                i = 0
                while i < 3 and i < len(all_sheet_names):
                    df = dfs_dict[all_sheet_names[i]]
                    expected_columns = ["班級", "座號", "科目", "必選修", "成績"] # 定義預期欄位，用於數據驗證
                    if not all(col in df.columns for col in expected_columns): # 驗證 Excel 檔案是否包含所有必要的欄位
                        missing_cols = [col for col in expected_columns if col not in df.columns]
                        return f"上傳失敗：Excel 檔案缺少必要的欄位。缺少欄位：{', '.join(missing_cols)}"

                    df_list.append(df)
                    i += 1

            elif file_type == 'xlsx' and auto == False:
                df = pd.read_excel(uploaded_file, engine='openpyxl', sheet_name=0)

                expected_columns = ["班級", "座號", "科目", "必選修", "成績"] # 定義預期欄位，用於數據驗證
                if not all(col in df.columns for col in expected_columns): # 驗證 Excel 檔案是否包含所有必要的欄位
                    missing_cols = [col for col in expected_columns if col not in df.columns]
                    return f"上傳失敗：Excel 檔案缺少必要的欄位。缺少欄位：{', '.join(missing_cols)}"

                df_list.append(df)

            elif file_type == 'csv':
                df = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')))
                df = df.fillna('') #替換空值

                expected_columns = ["班級", "座號", "科目", "必選修", "成績"] # 定義預期欄位，用於數據驗證
                if not all(col in df.columns for col in expected_columns): # 驗證 Excel 檔案是否包含所有必要的欄位
                    missing_cols = [col for col in expected_columns if col not in df.columns]
                    return f"上傳失敗：Excel 檔案缺少必要的欄位。缺少欄位：{', '.join(missing_cols)}"

                df_list.append(df)

        except FileNotFoundError:
            return "上傳失敗：找不到指定的 Excel 檔案。"
        except pd.errors.EmptyDataError:
            return "上傳失敗：Excel 檔案為空。"
        except pd.errors.ParserError:
            return f"上傳失敗：無法解析 {file_type} 檔案。請確認檔案格式正確。"
        except Exception as e:
            return f"讀取 Excel 檔案時發生未預期的錯誤：{e}"
        except UnicodeDecodeError:
            return "上傳失敗：無法以 UTF-8 編碼讀取 CSV 檔案。請確認檔案編碼。"

        data_num = 0
        for df in df_list:
            first_record_series = df.iloc[0]
            class_name = int(str(first_record_series['班級'])[0])

            if auto:
                worksheet = worksheet_list[class_name - 1]
            else:
                worksheet = worksheet_list[0]

            status_message_placeholder = st.warning(f"正在清空 {worksheet.title} 並上傳資料中...")
            clear_google_sheet_data(worksheet)
            status_message_placeholder.empty()

            # 將 DataFrame 轉換為列表的列表 (包含標頭行)，以便 gspread 進行更新
            data_to_upload = [df.columns.tolist()] + df.values.tolist()
            try:
                worksheet.update(values=data_to_upload)
                data_num += len(df)
                if auto == False:
                    return f"{worksheet.title} 已成功更新！共上傳 {len(df)} 筆資料。"
            except gspread.exceptions.APIError as e:
                return f"更新 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。"
            except Exception as e:
                return f"更新 Google Sheet 時發生未預期的錯誤：{e}"
        return f"雲端資料已成功更新！共更新 {len(df_list)} 個工作表，共 {data_num} 筆資料。"
    except Exception as e:
        return f"上傳補考名單時發生錯誤：{e}"
    
def display_cloud_data(sheet_name, worksheet_name):
    try:
        info = st.info(f"正在從 Google Sheet 獲取 {worksheet_name} 工作表，來自 {sheet_name.title} 檔")
        worksheet = open_google_sheet_worksheet(sheet_name, worksheet_name)
        data = worksheet.get_all_values()
        info.empty()

        if data:
            df_retest = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df_retest, hide_index=True)
        else:
            st.warning(f"{data} 工作表中沒有找到資料。錯誤檔案：{sheet_name}")
    except Exception as e:
        st.error(f"查看 {data} 發生錯誤。錯誤檔案：{sheet_name}。錯誤訊息：{e}")
        st.exception(e)

def clear_google_sheet_data(worksheet_name):
    try:
        all_data = worksheet_name.get_all_values() # 獲取所有資料，包括標題列，以判斷範圍

        if not all_data or len(all_data) <= 1: # 如果工作表為空或只有標題列，則無需清空
            return True

        header_row = all_data[0] # 獲取標題列
        worksheet_name.clear()
        worksheet_name.append_row(header_row) # 重新添加標題列
        return True

    except gspread.exceptions.APIError as e:
        st.error(f"清空 Google Sheet 時發生 API 錯誤：{e}。請檢查服務帳戶權限。")
        st.exception(e)
        return False

    except Exception as e:
        st.error(f"清空 Google Sheet 時發生未預期的錯誤：{e}。")
        st.exception(e)
        return False
    
def find_student_in_sheet(grade, class_name, seat_number, name):
    retest_data = open_google_sheet_worksheet(st.session_state['cloud_retest_data_manage'], grade + '年級補考名單').get_all_records()
    retest_data_df = pd.DataFrame(retest_data)

    if len(class_name) != 2: grade_class_name = grade + "0" + class_name
    else: grade_class_name = grade + class_name

    try:
        if not retest_data_df.empty:
            retest_student_data = retest_data_df[ #取出條件符合的學生資料
                (retest_data_df['班級'] == int(grade_class_name)) &
                (retest_data_df['座號'] == int(seat_number))
            ]
            if retest_student_data.empty: #如果沒有符合條件的學生資料
                st.info(f'查無 {grade} 年 {class_name} 班 {seat_number} 號 的補考資料，不需要補考。')
                return False
            student_data = {
                '年級': str(grade), #在retest_form_actions用來開啟補考者報名資料，因此轉為字串
                '班級': int(grade_class_name),
                '座號': int(seat_number),
                '姓名': str(name),
                '科目': retest_student_data['科目'].tolist(),
                '補考學生資料表格': retest_student_data
            }
            st.session_state['student_data'] = student_data
            return True
        else:
            st.info(f'查無 {grade} 年 {class_name} 班 {seat_number} 號 的補考資料，不需要補考。')
            return False
    except Exception as e:
        st.error(f"查詢學生資料時發生錯誤：{e}")
        return False
    
def student_sign_up():
    student_data = st.session_state['student_data']
    subjects = student_data['科目'] #登入學生的補考科目資料'列表'
    subjects_with_all = subjects

    # 顯示補考學生資料，hide_index=True 可以隱藏 DataFrame 左側的數字索引
    st.dataframe(student_data['補考學生資料表格'], hide_index=True, use_container_width=True)

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        selected_subjects = st.multiselect(
            '請選擇要報名的補考科目:',
            subjects_with_all,
            key='selected_subjects',
        )
    with col2:
        def select_all_callback():
            # 當「全選」按鈕被點擊時，直接將所有科目設置到 `selected_subjects` 的 session_state 中
            st.session_state['selected_subjects'] = subjects_with_all
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True) # 稍微調整垂直邊距
        st.button('全選補考科目', use_container_width=True, key='select_all_button', on_click=select_all_callback)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button('確認報名'):
        if not selected_subjects:
            st.warning('請選擇至少一個要補考的科目。')
            return False
        else:
            taiwan_tz = pytz.timezone('Asia/Taipei') #取得台灣時區
            now_in_taiwan = datetime.datetime.now(taiwan_tz)
            Time = now_in_taiwan.strftime("%Y-%m-%d %H:%M:%S")

            data_list = [int(student_data['班級']), int(student_data['座號']), selected_subjects, Time, str(student_data['姓名'])] # 構建要寫入的行資料
            if save_to_google_sheet(data_list, st.session_state['cloud_retest_data_manage'], student_data['年級'] + '年級報名資料'):
                return True

def delete_user_from_sheet(username_to_delete, worksheet, username_column_index):
    if worksheet is None:
        return False
    try:
        usernames = worksheet.col_values(username_column_index) # 讀取使用者名稱的所有資料列
        try: # 尋找要刪除的使用者名稱所在的列
            row_index_to_delete = usernames.index(username_to_delete) + 1  # gspread 的索引從 1 開始
        except ValueError:
            st.warning(f"找不到使用者名稱 '{username_to_delete}'。")
            return False

        worksheet.delete_rows(row_index_to_delete) # 刪除該列
        return True

    except Exception as e:
        st.error(f"刪除資料時發生錯誤：{e}")
        return False