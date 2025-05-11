#撰寫金鑰

import json
import os

json_file_path = 'retest-system-d96534a3f513.json' # 例如: 'service_account.json'

try:
    # 檢查檔案是否存在
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The file '{json_file_path}' was not found.")

    with open(json_file_path, 'r', encoding='utf-8') as f:
        original_credentials = json.load(f)

    # 確保 private_key 中的所有換行符都被正確地逸脫為 '\\n'
    if "private_key" in original_credentials:
        original_credentials["private_key"] = original_credentials["private_key"].replace('\n', '\\n')

    # 將整個字典轉換回 JSON 字串，並設定縮排以提高可讀性
    # 這個字串就是我們要放入 secrets.toml 的 service_account_json 值
    json_string_for_toml = json.dumps(original_credentials, indent=2, ensure_ascii=False)

    # 建構完整的 secrets.toml 內容，使用 .format() 方法避免 f-string 嵌套引號問題
    secrets_toml_template = """
# .streamlit/secrets.toml

[gsheets]
service_account_json = \"\"\"
{}
\"\"\"
""".format(json_string_for_toml) # 在這裡使用 .format() 來插入 JSON 字串

    print("--- 請複製以下所有內容，並貼到你的 .streamlit/secrets.toml 檔案中 ---")
    print(secrets_toml_template) # 打印格式化後的字串
    print("--------------------------------------------------------------------")
    print("\n完成後，請將這個內容也貼到 Streamlit Community Cloud 的 Secrets 頁面中：")
    print("1. 登入 Streamlit Cloud，進入你的應用程式頁面。")
    print("2. 點擊右下角的 'Manage app'。")
    print("3. 選擇 'Secrets' 選項卡。")
    ("4. 將上述內容完整貼入文本框，然後點擊 'Save secrets'。")
    print("5. 最後，重新部署你的應用程式。")

except FileNotFoundError:
    print(f"錯誤：檔案 '{json_file_path}' 未找到。")
    print("請檢查路徑和檔案名稱是否正確。")
except json.JSONDecodeError:
    print(f"錯誤：檔案 '{json_file_path}' 包含無效的 JSON 格式。")
    print("請確認你的原始 JSON 金鑰檔案是否是有效的 JSON。")
except Exception as e:
    print(f"發生了一個意外錯誤：{e}")