# app.py （カード固定高さ完全破壊・最終解決版）
import platform
import matplotlib
import panel as pn

from models import AppState
from views import TabRenderer

# Panelの初期化設定（トースト通知と通知機能を有効化）
pn.extension(loading_spinner='dots', notifications=True)
pn.config.nthreads = 4

# ─── 💡 修正箇所：カードの外箱にこびりつく固定のインライン高さを完全に消滅させるグローバルCSS ───
RAW_CSS = """
/* Panel/Bokehがカードやコンテナの外枠に強制的に焼き付ける固定のインライン高さをすべて強制解除 */
.bk-panel-Card,
.bk-Card,
.bk-accordion,
.bk-accordion-content,
.bk-FlexBox,
.bk-FlexBox > div,
.bk-Column,
.bk-Column > div,
.fit-img,
.fit-img > div {
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
}

/* カード内部の無駄な余白を極小化 */
.bk-accordion-content {
    padding: 8px !important;
}

/* グラフ画像タグ自体の伸縮特性をアスペクト比維持で完全成り行き化 */
.fit-img img {
    display: block !important;
    width: 100% !important;
    height: auto !important;
    max-height: none !important;
}
"""
# グローバル設定へ注入
pn.config.raw_css.append(RAW_CSS)


# OS自動判定による日本語フォント対策
current_os = platform.system()
if current_os == "Windows":
    matplotlib.rcParams["font.family"] = "Yu Gothic"
elif current_os == "Linux":
    matplotlib.rcParams["font.family"] = ["VL Gothic", "IPAGothic", "sans-serif"]
else:
    matplotlib.rcParams["font.family"] = "sans-serif"


def build_dashboard():
    # 1. 状態管理インスタンスと描画クラスの立ち上げ
    state = AppState()
    renderer = TabRenderer(state)

    # 「条件を更新」ボタンイベントのアタッチ
    update_btn = pn.widgets.Button(name="🔄 条件を更新", button_type="success", sizing_mode="stretch_width")
    update_btn.on_click(lambda e: renderer.render_all())

    # モード（単日・期間指定）に合わせてウィジェットを動的に切り替える関数
    def dynamic_date_controls(mode):
        if mode == "single":
            return pn.Column(
                pn.widgets.Select.from_param(state.param.yyyymm, name="対象月"),
                pn.widgets.Select.from_param(state.param.dd, name="対象日"),
                margin=(0, 0, 10, 0)
            )
        else:
            return pn.Column(
                pn.widgets.DatePicker.from_param(state.param.start_dd, name="開始日"),
                pn.widgets.DatePicker.from_param(state.param.end_dd, name="終了日"),
                margin=(0, 0, 10, 0)
            )

    bound_date_controls = pn.bind(dynamic_date_controls, state.param.mode)

    # 2. サイドバーコンポーネントの組み上げ
    sidebar = pn.Column(
        "## ⚙️ 制御パラメータ",
        pn.widgets.Select.from_param(state.param.base_id, name="📁 データソース (BASE_DIR)"),
        pn.widgets.RadioButtonGroup.from_param(state.param.mode, name="📅 表示モード"),
        
        bound_date_controls,
        
        pn.widgets.Select.from_param(state.param.switch, name="対象スイッチ名"),
        pn.Row(
            pn.widgets.IntInput.from_param(state.param.start_hour, name="開始(時)", width=90),
            pn.widgets.IntInput.from_param(state.param.end_hour, name="終了(時)", width=90)
        ),
        pn.widgets.RadioButtonGroup.from_param(state.param.cols, name="グラフ列数表示"),
        "---",
        "### 🧠 AI異常検知設定",
        pn.widgets.Select.from_param(state.param.anomaly_logic, name="検知アルゴリズム選択"),
        update_btn,
        sizing_mode="stretch_height", width=300
    )

    # 3. メインビュータブの構築
    tabs = pn.Tabs(
        ("📊 通常モニター", renderer.main_tab_layout),
        ("⭐ カスタムダッシュボード", renderer.dashboard_graph_grid),
        ("🧠 異常検知ダッシュボード", renderer.anomaly_graph_grid),
        dynamic=True
    )

    # 初回表示時に自動描画
    renderer.render_all()

    return pn.template.BootstrapTemplate(
        title="📊 SNMP トラフィック・コアモニター (Panel Web App)",
        sidebar=sidebar,
        main=tabs,
        header_background="#002b36"
    )

# サーバ公開用設定
app_template = build_dashboard()
app_template.servable()
