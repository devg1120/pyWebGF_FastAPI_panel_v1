# view_base.py （最外親コンテナ・縦幅連動引き伸ばし完全破壊版）
import panel as pn
from models import DASHBOARD_REGISTRY

class BaseTabRenderer:
    """各タブで共有するデータ操作や基本構造を管理する基盤クラス"""
    def __init__(self, state):
        self.state = state
        
        # ─── 💡 通常モニター用コンテナの構成変更 ───
        self.main_toc_pane = pn.pane.HTML(width=260, sizing_mode="stretch_height")
        
        # 💡 修正箇所：align_items='flex-start' を指定し、同じ列の背の高いカードに引きずられて縦に間伸びする挙動を完全にシャットダウンします。
        self.main_graph_grid = pn.FlexBox(sizing_mode="stretch_width", align_items="flex-start")
        
        self.main_tab_layout = pn.Row(
            self.main_toc_pane,
            self.main_graph_grid,
            sizing_mode="stretch_width"
        )
        
        # 💡 修正箇所：カスタムダッシュボードと異常検知コンテナ側も同様に、縦の強制ストレッチを解除します。
        self.dashboard_graph_grid = pn.FlexBox(sizing_mode="stretch_width", align_items="flex-start")
        self.anomaly_graph_grid = pn.FlexBox(sizing_mode="stretch_width", align_items="flex-start")

    def add_to_dashboard(self, filename, desc):
        """ダッシュボードへのお気に入り登録処理"""
        exists = any(i["yyyymm"] == self.state.yyyymm and i["dd"] == self.state.dd and i["switch"] == self.state.switch and i["filename"] == filename and i["base_id"] == self.state.base_id for i in DASHBOARD_REGISTRY)
        if not exists:
            DASHBOARD_REGISTRY.append({
                "base_id": self.state.base_id, "mode": self.state.mode, 
                "yyyymm": self.state.yyyymm, "dd": self.state.dd,
                "start_dd": self.state.start_dd, "end_dd": self.state.end_dd, 
                "switch": self.state.switch, "filename": filename, "desc": desc
            })
            pn.state.notifications.success(f"🔌 {filename.replace('.csv','')} を登録しました！")
            self.render_dashboard_tab()

    def delete_dashboard_item(self, idx):
        """ダッシュボードからの登録解除処理"""
        if 0 <= idx < len(DASHBOARD_REGISTRY):
            DASHBOARD_REGISTRY.pop(idx)
            self.render_all()

    def render_all(self):
        """具象クラスでオーバーライドされる全画面描画のプレースホルダー"""
        pass

    def render_dashboard_tab(self):
        """具象クラスでオーバーライドされるダッシュボード描画のプレースホルダー"""
        pass
