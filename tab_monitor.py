# tab_monitor.py （ピンポイント部分描画リファクタリング版）
import os
import glob
import json
import io
import base64
import panel as pn
from natsort import natsorted
import pandas as pd

from models import get_base_dir_path, DASHBOARD_REGISTRY
from charts import make_matplotlib_figure

def build_main_tab(self):
    """通常モニタータブのレイウル、目次、カードグリッドを構築する"""
    self.main_graph_grid.clear()
    
    # 選択された列数に基づいて、カード1個あたりの横幅（%）を動的に計算
    card_percent_width = 100 if self.state.cols == 1 else 48 if self.state.cols == 2 else 23

    actual_base = get_base_dir_path(self.state.base_id)
    target_dir = os.path.join(actual_base, self.state.yyyymm, self.state.dd, self.state.switch)
    
    info_json_path = os.path.join(target_dir, "info.json")
    info_dic = {}
    if os.path.exists(info_json_path):
        with open(info_json_path, 'r', encoding='utf-8') as f:
            info_dic = json.load(f)

    csv_filenames = natsorted([os.path.basename(f) for f in glob.glob(os.path.join(target_dir, "*.csv"))])
    if not csv_filenames:
        self.main_toc_pane.object = ""
        self.main_graph_grid.append(pn.pane.Markdown("### ⚠️ CSVファイルが見つかりません。"))
        return

    # 固定目次HTMLの動的生成
    toc_html = """
    <div style="position: sticky; top: 10px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; max-height: 85vh; overflow-y: auto; font-size: 13px; line-height: 1.6;">
        <h4 style="margin-top: 0; color: #333; border-bottom: 2px solid #002b36; padding-bottom: 5px; font-size: 14px;">📌 インターフェース目次</h4>
        <ul style="list-style: none; padding-left: 0; margin-bottom: 0;">
    """
    
    for fname in csv_filenames:
        if_name = fname.replace('.csv', '')
        desc = info_dic.get(if_name, {}).get("desc", "")
        speed = info_dic.get(if_name, {}).get("speed", "")
        label = f"<b>{if_name}</b><br><span style='color: #666; font-size: 11px;'>{desc}</span>" if desc else f"<b>{if_name}</b>"
        
        toc_html += f"""
            <li style="margin-bottom: 12px; border-bottom: 1px dashed #e9ecef; padding-bottom: 6px;">
                <a href="#" style="color: #0072B2; text-decoration: none; display: block;" 
                       onclick="
                           (function() {{
                               var searchTitle = '🔌 {if_name}';
                               var foundElement = null;
                               function searchElements(root) {{
                                   if (foundElement) return;
                                   var elements = root.querySelectorAll('*');
                                   for (var i = 0; i < elements.length; i++) {{
                                       var el = elements[i];
                                       if (el.textContent && el.textContent.trim().indexOf(searchTitle) === 0) {{
                                           foundElement = el;
                                           return;
                                       }}
                                       if (el.shadowRoot) {{
                                           searchElements(el.shadowRoot);
                                       }}
                                   }}
                               }}
                               searchElements(document);
                               if (foundElement) {{
                                   var targetCard = foundElement.closest('.bk-panel-Card') || foundElement.closest('.card') || foundElement;
                                   targetCard.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                               }}
                           }})();
                           return false;
                       ">
                    {label}
                </a>
            </li>
        """
        
        fig = make_matplotlib_figure(
            actual_base, self.state.mode, self.state.yyyymm, self.state.dd, self.state.start_dd, self.state.end_dd,
            self.state.switch, fname, self.state.cols, self.state.start_hour, self.state.end_hour, 
            speed, desc
        )
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.01)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        is_registered = any(i["yyyymm"] == self.state.yyyymm and i["dd"] == self.state.dd and i["switch"] == self.state.switch and i["filename"] == fname and i["base_id"] == self.state.base_id for i in DASHBOARD_REGISTRY)

        # 隠し通信ウィジェット
        widget_class = f"select-{if_name.replace('/', '_').replace('.', '_')}"
        hidden_select = pn.widgets.Select(options=["", fname], value="", visible=False, height=0, width=0, css_classes=[widget_class])

        # 💡 HTMLの描画ペインオブジェクトをあらかじめ「名前空間」に固定して生成
        html_pane = pn.pane.HTML(sizing_mode="stretch_width", margin=0)

        # ボタン部分の登録完了後HTMLシート
        registered_btn_html = f"""<div style="text-align: right; margin-top: 6px;"><button style="background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; padding: 5px 14px; border-radius: 4px; font-size: 12px; cursor: not-allowed;" disabled>⏳ 登録中</button></div>"""
        
        # 通常時の登録ボタンHTML
        normal_btn_html = f"""
        <div style="text-align: right; margin-top: 6px;">
            <button style="background: #0072B2; color: white; border: none; padding: 5px 14px; border-radius: 4px; font-size: 12px; cursor: pointer; font-weight: bold;" 
                    onclick="
                        (function(btn) {{
                            var targetClass = '{widget_class}';
                            var foundSelect = null;
                            function scanShadow(root) {{
                                if (foundSelect) return;
                                var container = root.querySelector('.' + targetClass);
                                if (container) {{
                                    foundSelect = container.querySelector('select') || container.shadowRoot?.querySelector('select');
                                    return;
                                }}
                                var allNodes = root.querySelectorAll('*');
                                for (var i = 0; i < allNodes.length; i++) {{
                                    if (allNodes[i].shadowRoot) scanShadow(allNodes[i].shadowRoot);
                                }}
                            }}
                            scanShadow(document);
                            if (foundSelect) {{
                                foundSelect.value = '{fname}';
                                foundSelect.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                            }}
                        }})(this);
                    ">
                ＋ ダッシュボード登録
            </button>
        </div>
        """

        # スケルトン関数（クロージャ）を定義してピンポイントでそのカードのボタン文字列だけを差し替える仕様に変更
        def make_html_card_string(btn_markup):
            return f"""
            <div style="width: 100%; height: auto; display: block; margin: 0; padding: 0;">
                <img src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block; margin: 0; padding: 0;" />
                <hr style="border: 0; border-top: 1px solid #dee2e6; margin: 6px 0 0 0; padding: 0; clear: both;" />
                {btn_markup}
            </div>
            """

        # 初期表示の割り当て
        if is_registered:
            html_pane.object = make_html_card_string(registered_btn_html)
        else:
            html_pane.object = make_html_card_string(normal_btn_html)

        # 💡 コールバックハンドラーの修正
        def make_register_callback(f_file=fname, d_desc=desc, s_widget=hidden_select, pane=html_pane):
            def handler(event):
                if event.new == f_file:
                    # 1. バックエンドリポジトリへ登録を実行
                    self.add_to_dashboard(f_file, d_desc)
                    # 2. 値をクリア
                    s_widget.value = ""
                    # 💡 3. 画面全体（self.render_main_tab()）は絶対に呼ばず、このカードのHTML部品オブジェクトだけをインライン置換！
                    pane.object = make_html_card_string(registered_btn_html)
            return handler
            
        hidden_select.param.watch(make_register_callback(), 'value')

        card_content = pn.Column(
            html_pane,
            hidden_select,
            sizing_mode="stretch_width",
            margin=0
        )
        
        self.main_graph_grid.append(pn.Card(
            card_content,
            title=f"🔌 {if_name}", header_background="#0072B2", header_color="white", collapsible=False, margin=8,
            stylesheets=[f"""
                :host {{
                    scroll-margin-top: 20px;
                    width: {card_percent_width}% !important;
                    min-width: 280px !important;
                    max-width: 100% !important;
                    height: auto !important;
                }}
                .bk-accordion-content {{
                    padding: 8px !important;
                    height: auto !important;
                }}
            """]
        ))

    toc_html += "</ul></div>"
    self.main_toc_pane.object = toc_html
