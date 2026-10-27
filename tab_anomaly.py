# tab_anomaly.py
import os
import glob
import io
import panel as pn
from natsort import natsorted
import pandas as pd

from models import get_base_dir_path
from charts import make_anomaly_figure

def build_anomaly_tab(self):
    """異常検知ダッシュボードタブのカードグリッドを構築する"""
    self.anomaly_graph_grid.clear()
    card_percent_width = 100 if self.state.cols == 1 else 48 if self.state.cols == 2 else 23
    
    if not (self.state.start_dd and self.state.end_dd and self.state.switch):
        self.anomaly_graph_grid.append(pn.pane.Markdown("### 🔍 条件を指定してください。"))
        return

    actual_base = get_base_dir_path(self.state.base_id)
    scan_date_dir = os.path.join(actual_base, pd.to_datetime(self.state.start_dd).strftime("%Y%m"), pd.to_datetime(self.state.start_dd).strftime("%d"), self.state.switch)
    csv_filenames = natsorted([os.path.basename(f) for f in glob.glob(os.path.join(scan_date_dir, "*.csv"))])

    if not csv_filenames:
        self.anomaly_graph_grid.append(pn.pane.Markdown("### ⚠️ CSVファイルが見つかりません。"))
        return

    from detectors import AnomalyDetectors
    logics_map = AnomalyDetectors.get_available_logics()
    inv_logics_map = {v: k for k, v in logics_map.items()}
    selected_logic_key = inv_logics_map.get(self.state.anomaly_logic, "stat_threshold")

    for fname in csv_filenames:
        fig = make_anomaly_figure(
            actual_base, self.state.start_dd, self.state.end_dd, self.state.switch, fname,
            selected_logic_key, self.state.start_hour, self.state.end_hour, self.state.cols
        )
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.01)
        buf.seek(0)
        
        card_content = pn.Column(
            pn.pane.PNG(buf.read(), sizing_mode="stretch_width", margin=0, css_classes=['fit-img']),
            sizing_mode="stretch_width"
        )
        
        self.anomaly_graph_grid.append(pn.Card(
            card_content,
            title=f"🧠 {fname.replace('.csv','')}", header_background="#CC79A7", header_color="white", collapsible=False, margin=8,
            stylesheets=[f"""
                :host {{
                    width: {card_percent_width}% !important;
                    min-width: 280px !important;
                    max-width: 100% !important;
                }}
                .bk-accordion-content {{
                    padding: 8px !important;
                }}
            """]
        ))
