#goodsheet相關函式
#https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=98794591912 (記得啟用Driver、Sheet API)
#建立服務者記得開共用給google sheet的服務者帳號

import json
import gspread
import streamlit as st
#-------------------------------------------goodsheet金鑰認證----------------------------------------------------
@st.cache_resource(ttl=3600) # # 緩存 gspread 客戶端，例如緩存 1 小時，避免頻繁認證
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

#-------------------------------------------goodsheet檔案開啟----------------------------------------------------
@st.cache_resource(ttl=3600) # 緩存工作表物件，例如緩存 1 小時
def get_google_sheet_worksheet(_gc: gspread.Client, sheet_name: str, worksheet_name: str = "1"):
    try:
        spreadsheet = _gc.open(sheet_name) # 開啟 Google 工作表 (by 名稱)
        worksheet = spreadsheet.worksheet(worksheet_name) # 選取指定名稱的工作表
        return worksheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"錯誤：找不到名為 '{sheet_name}' 的 Google Sheet 檔案。")
        st.warning("請告知管理者確認該檔案是否存在於 Google Drive 中，且已共享給服務帳戶郵件地址。")
        st.stop()
    except Exception as e:
        st.error(f"無法開啟或存取 Google Sheet，請告知管理者確認Google Sheet情況：{e}")
        st.stop()