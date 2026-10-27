# tab_dashboard.py
import io
import panel as pn
from models import get_base_dir_path, DASHBOARD_REGISTRY
from charts import make_matplotlib_figure

def build_dashboard_tab(self):
    """カスタムダッシュボードタブのカードグリッドを構築する"""
    self.dashboard_graph_grid.clear()
    card_percent_width = 100 if self.state.cols == 1 else 48 if self.state.cols == 2 else 23
    
    if not DASHBOARD_REGISTRY:
        self.dashboard_graph_grid.append(pn.pane.Markdown("### 📌 ダッシュボードに登録されたグラフはありません。"))
        return

    for idx, item in enumerate(DASHBOARD_REGISTRY):
        fig = make_matplotlib_figure(
            get_base_dir_path(item["base_id"]), self.state.mode, self.state.yyyymm, self.state.dd, item["start_dd"], item["end_dd"],
            item["switch"], item["filename"], self.state.cols, self.state.start_hour, self.state.end_hour, desc=item["desc"]
        )
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.01)
        buf.seek(0)
        
        # 💡 削除ボタン自体に align="end" を指定
        del_btn = pn.widgets.Button(name="× 削除", button_type="danger", width=80, align="end", margin=(6, 0, 0, 0))
        del_btn.on_click(lambda e, i=idx: self.delete_dashboard_item(i))
        
        card_content = pn.Column(
            pn.pane.PNG(buf.read(), sizing_mode="stretch_width", margin=0, css_classes=['fit-img']),
            del_btn,
            sizing_mode="stretch_width"
        )
        
        self.dashboard_graph_grid.append(pn.Card(
            card_content,
            title=f"⭐ [{item['base_id']}] {item['switch']} - {item['filename']}", header_background="#D55E00", header_color="white", collapsible=False, margin=8,
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
