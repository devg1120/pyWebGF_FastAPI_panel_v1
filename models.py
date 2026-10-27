# models.py （修正版）
import os
import glob
import pandas as pd
import param

BASE_DIRS = {
    "test1": "./test_data/test1",
    "test2": "./test_data/test2",
}
DEFAULT_DIR = "test1"

# 登録済みダッシュボードの保存用（メモリ保持リポジトリ）
DASHBOARD_REGISTRY = []

def get_base_dir_path(base_id: str) -> str:
    return BASE_DIRS.get(base_id, BASE_DIRS[DEFAULT_DIR])

def get_date_tree(base_id: str):
    date_tree = {}
    actual_base = get_base_dir_path(base_id)
    if not os.path.exists(actual_base):
        os.makedirs(actual_base)
    yyyymm_dirs = sorted([d for d in glob.glob(os.path.join(actual_base, "*")) if os.path.isdir(d)])
    for ymd in yyyymm_dirs:
        ym_name = os.path.basename(ymd)
        dd_dirs = sorted([d for d in glob.glob(os.path.join(ymd, "*")) if os.path.isdir(d)])
        dd_list = [os.path.basename(d) for d in dd_dirs]
        if dd_list:
            date_tree[ym_name] = dd_list
    return date_tree


class AppState(param.Parameterized):
    """アプリケーション内のウィジェットの選択状態と連動ロジックを管理するモデル"""
    base_id = param.Selector(objects=list(BASE_DIRS.keys()), default=DEFAULT_DIR)
    mode = param.Selector(objects=["single", "range"], default="single")
    yyyymm = param.Selector(objects=[""])
    dd = param.Selector(objects=[""])
    start_dd = param.CalendarDate(default=pd.Timestamp.now().date() - pd.Timedelta(days=1))
    end_dd = param.CalendarDate(default=pd.Timestamp.now().date())
    switch = param.Selector(objects=[""])
    cols = param.Selector(objects=[1, 2, 4], default=2)
    start_hour = param.Integer(default=8, bounds=(0, 23))
    end_hour = param.Integer(default=18, bounds=(0, 23))
    
    # 💡 修正箇所：初期化時は空リストにして、デフォルト値は設定しない（後で動的にセットする）
    anomaly_logic = param.Selector(objects=[])

    def __init__(self, **params):
        super().__init__(**params)
        self.date_tree = {}
        
        # 💡 修正箇所：detectors.py から辞書マップ（内部名と画面表示名）を取得し、安全に割り当てる
        from detectors import AnomalyDetectors
        logics_map = AnomalyDetectors.get_available_logics() # 例: {"stat_threshold": "【異常検知: 直近急変重視】", ...}
        
        # param.Selectorに辞書を安全にマップするPanelの推奨ルール
        self.param.anomaly_logic.objects = logics_map
        if "stat_threshold" in logics_map:
            # 辞書を渡した場合、Selector内部では「値（日本語表示名）」が有効値となるため、
            # デフォルト値には対応する日本語文字列を代入します
            self.anomaly_logic = logics_map["stat_threshold"]
            
        self.update_date_tree()

    @param.depends('base_id', watch=True)
    def update_date_tree(self):
        """データソース変更時に選択肢をリフレッシュ"""
        self.date_tree = get_date_tree(self.base_id)
        if self.date_tree:
            available_ym = list(self.date_tree.keys())
            self.param.yyyymm.objects = available_ym
            if self.yyyymm not in available_ym:
                self.yyyymm = available_ym[-1]
            self.update_days()
        else:
            self.param.yyyymm.objects = [""]
            self.param.dd.objects = [""]
            self.param.switch.objects = [""]

    @param.depends('yyyymm', watch=True)
    def update_days(self):
        """対象月変更時に日プルダウンを自動更新"""
        if self.date_tree and self.yyyymm in self.date_tree:
            available_dds = self.date_tree[self.yyyymm]
            self.param.dd.objects = available_dds
            if self.dd not in available_dds:
                self.dd = available_dds[-1]
            self.update_switches()

    @param.depends('dd', 'mode', 'start_dd', watch=True)
    def update_switches(self):
        """日付やモード変更時にスイッチ一覧を自動更新"""
        actual_base = get_base_dir_path(self.base_id)
        switch_set = set()
        
        if self.mode == "single" and self.yyyymm and self.dd:
            date_dir = os.path.join(actual_base, self.yyyymm, self.dd)
            if os.path.exists(date_dir):
                switch_set = {os.path.basename(d) for d in glob.glob(os.path.join(date_dir, "*")) if os.path.isdir(d)}
        else:
            for ym, dds in self.date_tree.items():
                if dds:
                    date_dir = os.path.join(actual_base, ym, dds[-1])
                    if os.path.exists(date_dir):
                        switch_set.update({os.path.basename(d) for d in glob.glob(os.path.join(date_dir, "*")) if os.path.isdir(d)})
        
        available_switches = sorted(list(switch_set))
        self.param.switch.objects = available_switches if available_switches else [""]
        if available_switches and self.switch not in available_switches:
            self.switch = available_switches[0]
