# views.py
from view_tabs import DetailedTabRenderer

class TabRenderer(DetailedTabRenderer):
    """
    アプリケーションのメイン描画クラス。
    UIビルドの実体は view_tabs.py にカプセル化されています。
    """
    def __init__(self, state):
        super().__init__(state)

    def render_all(self):
        """全タブの内容をフレッシュに一括再構成する"""
        self.render_main_tab()
        self.render_dashboard_tab()
        self.render_anomaly_tab()
