# charts.py （二重エリアバグ完全排除・最終解決版）
import io
import os
import glob
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# 外部ファイルから異常検知マネージャーをインポート
from detectors import AnomalyDetectors

# UIスレッド以外でも安全にMatplotlibを動かすための設定
matplotlib.use("Agg")
matplotlib.rcParams["axes.unicode_minus"] = False

# ─── 📊 通常モニター用グラフ生成 ───
def make_matplotlib_figure(actual_base, mode, yyyymm, dd, start_dd, end_dd, switch, filename, cols, start_hour, end_hour, speed="", desc=""):
    # 各列数に合わせて無駄のないアスペクト比を設定
    fig_size = (12, 3.8) if cols == 1 else (5.2, 2.6) if cols == 4 else (6.5, 3.0)
    fig = Figure(figsize=fig_size)
    
    # 💡 修正箇所：二重領域バグを完全に防ぐため、1つのグラフエリア(1行1列の1番目)のみを明示的に作成
    ax = fig.add_subplot(1, 1, 1)
    #g_speed = f"{int(speed)//1000}Gbps" if speed else ""
    g_speed = ""
    if speed:
        try:
            g_speed = f"{int(speed)//1000}Gbps"
        except (ValueError, TypeError):
            # もし info.json の speed に不正な値や説明文が混入していても、
            # キャストエラーで画面全体がクラッシュするのを100%防止します
            g_speed = str(speed) 

    try:
        from data_loader import get_filtered_traffic_data
        df_filtered, start_time, end_time, x_label_text, x_tick_format = get_filtered_traffic_data(
            actual_base, mode, yyyymm, dd, start_dd, end_dd, switch, filename, start_hour, end_hour
        )

        fig.set_facecolor("#f0f0f0")
        ax.set_facecolor("#ffffff")

        if not df_filtered.empty:
            ax.fill_between(df_filtered["日時"], df_filtered["bps_A"], color="#00eb0c", alpha=0.9, label="In (bps)")
            ax.plot(df_filtered["日時"], df_filtered["bps_A"], color="#006600", linewidth=0.8)
            if "bps_B" in df_filtered.columns:
                ax.plot(df_filtered["日時"], df_filtered["bps_B"], color="#1000ff", linewidth=1.8, label="Out (bps)")
        else:
            ax.text(0.5, 0.5, "データがありません", ha="center", va="center", color="red")

        ax.grid(True, which="both", color="#cccccc", linestyle="-", linewidth=0.5)
        ax.set_xlim(start_time, end_time)
        ax.xaxis.set_major_formatter(mdates.DateFormatter(x_tick_format))
        if mode == "range":
            for label in ax.get_xticklabels():
                label.set_rotation(30)
                label.set_horizontalalignment("right")

        max_val = max(df_filtered["bps_A"].max(), df_filtered["bps_B"].max()) if not df_filtered.empty else 0
        if max_val >= 1_000_000_000:
            ax.set_ylim(0, 2_000_000_000)
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"{x / 1_000_000_000:,.1f} G"))
            ax.set_ylabel("転送速度 (Gbps)")
        else:
            ax.set_ylim(0, 1_000_000_000)
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"{x / 1_000_000:,.0f} M"))
            ax.set_ylabel("転送速度 (Mbps)")

        ax.get_yaxis().get_offset_text().set_visible(False)
        ax.set_title(f"{switch}: {filename.replace('.csv', '')} {g_speed}", fontsize=10, loc="left")
        ax.set_title(desc, fontsize=9, loc="right", color="#000000")
        ax.set_xlabel(x_label_text)

    except Exception as e:
        ax.text(0.5, 0.5, f"Error: {type(e).__name__}", ha="center", va="center", color="red")

    # 💡 修正箇所：凡例をグラフ内の左上に綺麗に収め、下部に余白を作らせないように配置
    ax.legend(loc='upper left', ncol=2, frameon=True, facecolor="#ffffff", edgecolor="#cccccc", fontsize=8)
    
    # 💡 修正箇所：無駄なマージンをカットし、波形を上下いっぱいに引き伸ばす
    fig.tight_layout()
    return fig

# ─── 🧠 異常検知用グラフ生成 ───
def make_anomaly_figure(actual_base, start_dd, end_dd, switch, filename, logic, start_hour, end_hour, cols):
    fig_size = (12, 3.8) if cols == 1 else (5.2, 2.6) if cols == 4 else (6.5, 3.0)
    fig = Figure(figsize=fig_size)
    
    # 💡 修正箇所：異常検知側も一重エリア化を強制
    ax = fig.add_subplot(1, 1, 1)
    df_filtered = pd.DataFrame()

    try:
        from data_loader import get_filtered_traffic_data
        df, start_time, end_time, x_label_text, x_tick_format = get_filtered_traffic_data(
            actual_base, "range", "", "", start_dd, end_dd, switch, filename, start_hour, end_hour
        )

        fig.set_facecolor("#f0f0f0")
        ax.set_facecolor("#ffffff")

        if not df.empty:
            df = df[~df["日時"].duplicated(keep='first')].reset_index(drop=True)
            max_points = 1000
            df_filtered = df.iloc[::(len(df) // max_points)].copy().reset_index(drop=True) if len(df) > max_points else df.copy()

            ax.plot(df_filtered.index, df_filtered["bps_A"], color="#006600", linewidth=0.8, label="In (bps)")
            ax.fill_between(df_filtered.index, df_filtered["bps_A"], color="#00eb0c", alpha=0.4)

            percentile_val = 0.95 if logic == "burst_detector" else 0.98 if logic == "z_score_outlier" else 0.99
            anomalies = AnomalyDetectors.detect(logic, df_filtered, percentile_val)
            title_prefix = AnomalyDetectors.get_available_logics().get(logic, "【異常検知】")

            if not anomalies.empty:
                ax.scatter(anomalies.index, anomalies["bps_A"], color="red", s=15, zorder=5, label="Anomaly")

            ax.set_xlim(0, len(df_filtered) - 1)
            tick_indices = [0, len(df_filtered)//4, len(df_filtered)//2, (len(df_filtered)*3)//4, len(df_filtered)-1]
            tick_labels = [df_filtered["日時"].iloc[i].strftime(x_tick_format) for i in tick_indices if i < len(df_filtered)]
            ax.set_xticks(tick_indices)
            ax.set_xticklabels(tick_labels, rotation=30, ha="right")
        else:
            ax.text(0.5, 0.5, "データがありません", ha="center", va="center", color="red")
            title_prefix = "【異常検知】"

        max_val = df_filtered["bps_A"].max() if 'df_filtered' in locals() and not df_filtered.empty else 0
        if max_val >= 1_000_000:
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"{x / 1_000_000:,.1f} M"))
            ax.set_ylabel("転送速度 (Mbps)")
        else:
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
            ax.set_ylabel("転送速度 (bps)")

        ax.set_title(f"{title_prefix} {switch}: {filename.replace('.csv', '')}", fontsize=10, loc="left", color="darkred")
        ax.set_xlabel(x_label_text)
    except Exception as e:
        ax.text(0.5, 0.5, f"Error: {type(e).__name__}", ha="center", va="center", color="red")

    ax.legend(loc='upper left', ncol=2, frameon=True, fontsize=8)
    fig.tight_layout()
    return fig
