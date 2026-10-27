# view_tabs.py
from view_base import BaseTabRenderer

# 分割した3つの独立した画面タブ描画関数をロード
from tab_monitor import build_main_tab
from tab_dashboard import build_dashboard_tab
from tab_anomaly import build_anomaly_tab

class DetailedTabRenderer(BaseTabRenderer):
    """
    各タブ画面の具体的な実装を外部の分割ファイルからロードしてバインドするブリッジクラス
    """
    def render_main_tab(self):
        build_main_tab(self)

    def render_dashboard_tab(self):
        build_dashboard_tab(self)

    def render_anomaly_tab(self):
        build_anomaly_tab(self)
