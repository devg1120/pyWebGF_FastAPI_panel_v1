# data_loader.py
import os
import pandas as pd

def load_and_process_csv(file_path):
    """単一のCSVファイルを読み込み、初期の列名整理を行います。"""
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    df = pd.read_csv(file_path, engine="c")
    if df.empty:
        return df

    if len(df.columns) >= 6:
        df.columns = ["日時", "INDEX", "NAME", "STATUS", "項目A", "項目B"] + list(df.columns[6:])
    elif len(df.columns) >= 3:
        df.columns = ["日時", "項目A", "項目B"] + list(df.columns[3:])
    
    return df

def get_filtered_traffic_data(actual_base, mode, yyyymm, dd, start_dd, end_dd, switch, filename, start_hour, end_hour):
    """指定された期間・モードに応じたデータを結合・フィルタリングし、bps換算したDataFrameを返します。"""
    df_list = []
    
    if mode == "range" and start_dd and end_dd:
        start_date_obj = pd.to_datetime(str(start_dd).replace("/", "-"))
        end_date_obj = pd.to_datetime(str(end_dd).replace("/", "-"))
        dr = pd.date_range(start=start_date_obj, end=end_date_obj)
        
        for d in dr:
            ym_dir = d.strftime("%Y%m")
            candidate_paths = [
                os.path.join(actual_base, ym_dir, d.strftime("%d"), switch, filename),
                os.path.join(actual_base, ym_dir, str(d.day), switch, filename),
            ]
            for c_path in candidate_paths:
                _df = load_and_process_csv(c_path)
                if not _df.empty:
                    df_list.append(_df)
                    
        if df_list:
            df = pd.concat(df_list, ignore_index=True)
        else:
            raise FileNotFoundError("データファイルが見つかりません。")
            
        start_time = start_date_obj + pd.Timedelta(hours=start_hour)
        end_time = end_date_obj + pd.Timedelta(hours=end_hour, minutes=55)
        x_label_text = f"{start_date_obj.strftime('%Y-%m-%d')} ～ {end_date_obj.strftime('%Y-%m-%d')}"
        x_tick_format = "%m/%d %H:%M"
    else:
        file_path = os.path.join(actual_base, yyyymm, dd, switch, filename)
        df = load_and_process_csv(file_path)
        if df.empty:
            raise FileNotFoundError(f"ファイルなし、または空データ: {yyyymm}/{dd}")
            
        base_date = pd.to_datetime(f"{yyyymm[:4]}-{yyyymm[4:]}-{dd}").normalize()
        start_time = base_date + pd.Timedelta(hours=start_hour)
        end_time = base_date + pd.Timedelta(hours=end_hour, minutes=55)
        x_label_text = f"{yyyymm[:4]}-{yyyymm[4:6]}-{dd}"
        x_tick_format = "%H:%M"

    # 時刻パースと並び替え
    df["日時"] = pd.to_datetime(df["日時"], format="mixed", errors='coerce')
    df = df.dropna(subset=["日時"]).sort_values("日時").reset_index(drop=True)
    
    # 欠損・ギャップガード（5.5分以上の間隔を異常値として破棄）
    time_diff_sec = df["日時"].diff().dt.total_seconds()
    is_missing = (time_diff_sec > 330) | (time_diff_sec < 0)

    # 差分（bps）計算
    df["差分A"] = df["項目A"].diff().clip(lower=0)
    df.loc[is_missing, "差分A"] = None  
    df["bps_A"] = (df["差分A"] * 8) / 300

    if "項目B" in df.columns:
        df["差分B"] = df["項目B"].diff().clip(lower=0)
        df.loc[is_missing, "差分B"] = None
        df["bps_B"] = (df["差分B"] * 8) / 300
    else:
        df["bps_B"] = 0

    # 選択時間内のデータに絞り込み
    df_filtered = df[(df["日時"] >= start_time) & (df["日時"] <= end_time)]
    
    return df_filtered, start_time, end_time, x_label_text, x_tick_format
