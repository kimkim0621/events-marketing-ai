import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import json
import os
import tempfile
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import io
from typing import List
import plotly.express as px
import plotly.graph_objects as go

# 共有データベース設定
try:
    from database_setup import SharedDatabase, setup_shared_database
    SHARED_DB_AVAILABLE = True
    if 'db_mode' not in st.session_state:
        st.session_state.db_mode = "shared"  # shared または local
except ImportError:
    SHARED_DB_AVAILABLE = False
    if 'db_mode' not in st.session_state:
        st.session_state.db_mode = "local"

# クラウド対応のデータベースパス設定
if "STREAMLIT_CLOUD" in os.environ or not os.path.exists("data"):
    # Streamlit Cloud環境またはdataディレクトリが存在しない場合
    DB_PATH = "events_marketing.db"
    # 必要なディレクトリを作成（エラー処理付き）
    try:
        os.makedirs("backups", exist_ok=True)
    except Exception:
        pass  # Streamlit Cloudでは書き込み権限がない場合がある
else:
    # ローカル環境
    DB_PATH = "data/events_marketing.db"
    try:
        os.makedirs("data/backups", exist_ok=True)
    except Exception:
        pass

# 社内データシステムのインポート
try:
    from internal_data_system import InternalDataSystem
    from data_cleaner import DataCleaner
    INTERNAL_DATA_AVAILABLE = True
except ImportError as e:
    # Streamlit Cloudでは警告のみ表示
    if "STREAMLIT_CLOUD" in os.environ:
        st.warning("⚠️ 社内データシステムが利用できません（クラウド環境）")
    else:
        st.error(f"⚠️ 社内データシステムが利用できません: {str(e)}")
    INTERNAL_DATA_AVAILABLE = False



# ページ設定
st.set_page_config(
    page_title="イベント集客施策提案AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .campaign-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .free-campaign {
        border-left: 4px solid #28a745;
    }
    .paid-campaign {
        border-left: 4px solid #ffc107;
    }
    
    /* Multiselectのドロップダウンをスクロール可能にする */
    .stMultiSelect > div[data-baseweb="select"] > div {
        max-height: 300px;
        overflow-y: auto;
    }
    
    /* ドロップダウンメニューのスクロール設定 */
    div[data-baseweb="popover"] {
        max-height: 400px;
    }
    
    div[data-baseweb="popover"] > div {
        max-height: 350px;
        overflow-y: auto;
    }
    
    /* スクロールバーのスタイリング */
    div[data-baseweb="popover"] > div::-webkit-scrollbar {
        width: 8px;
    }
    
    div[data-baseweb="popover"] > div::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    div[data-baseweb="popover"] > div::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    
    div[data-baseweb="popover"] > div::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # データインポートUIを呼び出し
    try:
        from data_import_ui import main as data_import_main
        data_import_main()
    except ImportError:
        # フォールバック: 元のUI
        initialize_database()
        
        st.markdown('<h1 class="main-header">🎯 イベント集客施策提案AI</h1>', unsafe_allow_html=True)
        
        # タブの追加
        main_tab, data_tab = st.tabs(["🎯 施策提案", "📊 データ管理"])
        
        with data_tab:
            show_data_management()
        
        with main_tab:
            show_main_interface()

def initialize_database():
    """データベースとテーブルの初期化（サイレント処理）"""
    if SHARED_DB_AVAILABLE:
        # Supabaseデータベースの初期化
        try:
            if 'shared_db' not in st.session_state:
                db = setup_shared_database()
                if db:
                    st.session_state['shared_db'] = db
        except Exception:
            pass  # エラーは記録するが表示しない
    else:
        # ローカルSQLiteの初期化
        try:
            if not os.path.exists(DB_PATH):
                # ローカルデータベースファイルが存在しない場合は作成
                os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
        except Exception:
            pass  # エラーは記録するが表示しない

def show_main_interface():
    """メイン施策提案インターフェース"""
    # サイドバーでの入力フォーム
    with st.sidebar:
        st.markdown("## 📝 イベント情報入力")
        
        # 基本情報
        event_name = st.text_input("イベント名", placeholder="例: AI技術セミナー")
        
        event_category = st.selectbox(
            "イベントカテゴリ",
            ["conference", "seminar", "workshop", "webinar", "networking", "product_launch"],
            format_func=lambda x: {
                "conference": "カンファレンス",
                "seminar": "セミナー", 
                "workshop": "ワークショップ",
                "webinar": "ウェビナー",
                "networking": "ネットワーキング",
                "product_launch": "製品発表"
            }[x]
        )
        
        event_theme = st.text_area("イベントテーマ・内容", placeholder="例: 最新のAI技術動向と実践事例")
        
        # ターゲット設定
        st.markdown("### 🎯 ターゲット設定")
        
        with st.expander("🏢 業種選択 (34業種)", expanded=True):
            # 業種の選択肢（「すべて」を最上段に追加）
            industry_options = ["すべて", "輸送用機器", "電気機器", "小売業", "卸売業", "医薬品", "その他製品", "精密機器", "不動産業", "陸運業", "鉄鋼", "鉱業", "石油・石炭製品", "非鉄金属", "空運業", "ガラス・土石製品", "パルプ・紙", "水産・農林業", "銀行業", "サービス業", "情報・通信業", "化学", "保険業", "食料品", "機械", "ゴム製品", "建設業", "証券、商品先物取引業", "電気・ガス業", "海運業", "その他金融業", "繊維製品", "金属製品", "倉庫・運輸関連業", "その他"]
            
            # セッション状態の初期化
            if 'selected_industries' not in st.session_state:
                st.session_state.selected_industries = ["情報・通信業"]
            
            # 「すべて」選択の処理
            def on_industries_change():
                selected = st.session_state.industries_multiselect
                if "すべて" in selected and "すべて" not in st.session_state.selected_industries:
                    # 「すべて」が新しく選択された場合
                    st.session_state.selected_industries = industry_options.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_industries:
                    # 「すべて」が解除された場合
                    st.session_state.selected_industries = []
                elif "すべて" in selected:
                    # 「すべて」が選択されている状態で他が変更された場合
                    if len(selected) < len(industry_options):
                        # 一部解除された場合、「すべて」を除外
                        st.session_state.selected_industries = [opt for opt in selected if opt != "すべて"]
                else:
                    # 通常の選択
                    st.session_state.selected_industries = selected
                    # 全て選択されている場合、「すべて」を追加
                    if len(selected) == len(industry_options) - 1:
                        st.session_state.selected_industries = ["すべて"] + selected
            
            industries = st.multiselect(
                "業種",
                industry_options,
                default=st.session_state.selected_industries,
                key="industries_multiselect",
                on_change=on_industries_change,
                help="複数選択可能です。「すべて」を選択すると全業種が対象になります。"
            )
            
            # 表示用に実際の業種のみを抽出
            industries_actual = [ind for ind in industries if ind != "すべて"] if "すべて" not in industries else [ind for ind in industry_options if ind != "すべて"]
        
        with st.expander("👥 職種選択 (31職種)", expanded=True):
            # 職種の選択肢（「すべて」を最上段に追加）
            job_title_options = ["すべて", "CTO", "VPoE", "EM", "フロントエンドエンジニア", "インフラエンジニア", "フルスタックエンジニア", "モバイルエンジニア", "セキュリティエンジニア", "アプリケーションエンジニア・ソリューションアーキテクト", "データサイエンティスト", "情報システム", "ネットワークエンジニア", "UXエンジニア", "デザイナー", "学生", "データアナリスト", "CPO", "VPoT/VPoP", "テックリード", "バックエンドエンジニア", "SRE", "プロダクトマネージャー", "DevOpsエンジニア", "QAエンジニア", "機械学習エンジニア", "プロジェクトマネージャー", "SIer", "ゲーム開発エンジニア", "組み込みエンジニア", "エンジニア以外", "データエンジニア"]
            
            # セッション状態の初期化
            if 'selected_job_titles' not in st.session_state:
                st.session_state.selected_job_titles = ["フロントエンドエンジニア", "バックエンドエンジニア"]
            
            # 「すべて」選択の処理
            def on_job_titles_change():
                selected = st.session_state.job_titles_multiselect
                if "すべて" in selected and "すべて" not in st.session_state.selected_job_titles:
                    st.session_state.selected_job_titles = job_title_options.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_job_titles:
                    st.session_state.selected_job_titles = []
                elif "すべて" in selected:
                    if len(selected) < len(job_title_options):
                        st.session_state.selected_job_titles = [opt for opt in selected if opt != "すべて"]
                else:
                    st.session_state.selected_job_titles = selected
                    if len(selected) == len(job_title_options) - 1:
                        st.session_state.selected_job_titles = ["すべて"] + selected
            
            job_titles = st.multiselect(
                "職種",
                job_title_options,
                default=st.session_state.selected_job_titles,
                key="job_titles_multiselect",
                on_change=on_job_titles_change,
                help="複数選択可能です。「すべて」を選択すると全職種が対象になります。"
            )
            
            # 表示用に実際の職種のみを抽出
            job_titles_actual = [jt for jt in job_titles if jt != "すべて"] if "すべて" not in job_titles else [jt for jt in job_title_options if jt != "すべて"]
        
        with st.expander("📊 従業員規模選択 (8段階)", expanded=False):
            # 従業員規模の選択肢（「すべて」を最上段に追加）
            company_size_options = ["すべて", "10名以下", "11名～50名", "51名～100名", "101名～300名", "301名～500名", "501名～1,000名", "1,001～5,000名", "5,001名以上"]
            
            # セッション状態の初期化
            if 'selected_company_sizes' not in st.session_state:
                st.session_state.selected_company_sizes = ["101名～300名", "301名～500名"]
            
            # 「すべて」選択の処理
            def on_company_sizes_change():
                selected = st.session_state.company_sizes_multiselect
                if "すべて" in selected and "すべて" not in st.session_state.selected_company_sizes:
                    st.session_state.selected_company_sizes = company_size_options.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_company_sizes:
                    st.session_state.selected_company_sizes = []
                elif "すべて" in selected:
                    if len(selected) < len(company_size_options):
                        st.session_state.selected_company_sizes = [opt for opt in selected if opt != "すべて"]
                else:
                    st.session_state.selected_company_sizes = selected
                    if len(selected) == len(company_size_options) - 1:
                        st.session_state.selected_company_sizes = ["すべて"] + selected
            
            company_sizes = st.multiselect(
                "従業員規模",
                company_size_options,
                default=st.session_state.selected_company_sizes,
                key="company_sizes_multiselect",
                on_change=on_company_sizes_change,
                help="複数選択可能です。「すべて」を選択すると全規模が対象になります。"
            )
            
            # 表示用に実際の従業員規模のみを抽出
            company_sizes_actual = [cs for cs in company_sizes if cs != "すべて"] if "すべて" not in company_sizes else [cs for cs in company_size_options if cs != "すべて"]
        
        # 目標・予算設定
        st.markdown("### 💰 目標・予算設定")
        
        target_attendees = st.number_input("目標申込人数", min_value=1, value=100)
        budget = st.number_input("集客予算（円）", min_value=0, value=500000, step=50000)
        
        event_date = st.date_input(
            "開催日",
            value=datetime.now().date() + timedelta(days=30),
            min_value=datetime.now().date()
        )
        
        is_free_event = st.checkbox("無料イベント", value=True)
        
        event_format = st.selectbox(
            "開催形式",
            ["online", "offline", "hybrid"],
            format_func=lambda x: {"online": "オンライン", "offline": "オフライン", "hybrid": "ハイブリッド"}[x]
        )
        
        # AI予測エンジン選択
        use_ai_engine = st.checkbox("🧠 高度AI予測エンジンを使用", value=False, help="機械学習ベースの高度な予測を行います（ベータ版）")
        
        # 提案生成ボタン
        if st.button("🚀 施策提案を生成", type="primary", use_container_width=True):
            if event_name and event_theme and industries_actual and job_titles_actual:
                generate_recommendations(
                    event_name, event_category, event_theme, industries_actual, job_titles_actual,
                    company_sizes_actual, target_attendees, budget, event_date, is_free_event, event_format, use_ai_engine
                )
            else:
                st.error("必須項目を入力してください")
    
    # メインエリア（サイドバーの外側に移動）
    if 'recommendations' not in st.session_state:
        show_welcome_screen()
    else:
        show_recommendations()

def show_data_management():
    """データ管理画面"""
    st.markdown("## 📊 データ管理システム")
    
    # データベース接続状況を表示
    if SHARED_DB_AVAILABLE and 'shared_db' in st.session_state:
        st.info("🌐 Supabase共有データベースを使用中")
        # Supabaseでのシンプルなデータ管理を実装
        show_supabase_data_management()
        return
    elif INTERNAL_DATA_AVAILABLE:
        st.info("💻 ローカルデータシステムを使用中")
        # 初期化
        if 'data_system' not in st.session_state:
            st.session_state['data_system'] = InternalDataSystem()
        data_system = st.session_state['data_system']
    else:
        st.warning("⚠️ データシステムが利用できません（基本機能のみ利用可能）")
        show_basic_data_management()
        return
    
    # データ概要の表示
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 現在のデータ概要")
        
        # データ統計の表示
        try:
            # データ概要を取得して表示
            import sqlite3
            conn = sqlite3.connect(data_system.db_path)
            cursor = conn.cursor()
            
            # 基本統計
            tables_stats = {}
            tables = ['historical_events', 'media_performance', 'media_detailed_attributes', 'internal_knowledge']
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    tables_stats[table] = count
                except:
                    tables_stats[table] = 0
            
            # 統計表示
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("📅 イベントデータ", f"{tables_stats['historical_events']}件")
            
            with col_stat2:
                st.metric("📺 メディアデータ", f"{tables_stats['media_performance']}件")
            
            with col_stat3:
                st.metric("🎯 メディア属性", f"{tables_stats['media_detailed_attributes']}件")
            
            with col_stat4:
                st.metric("🧠 社内知見", f"{tables_stats['internal_knowledge']}件")
            
            conn.close()
            
        except Exception as e:
            st.error(f"データ統計の取得エラー: {str(e)}")
    
    with col2:
        st.markdown("### ⚡ クイックアクション")
        
        if st.button("🔄 データ統計更新", use_container_width=True):
            st.rerun()
        
        if st.button("📋 詳細レポート", use_container_width=True):
            show_detailed_data_report(data_system)
    
    st.markdown("---")
    
    # データインポート機能
    import_tab, knowledge_tab, clean_tab, analysis_tab = st.tabs(["📥 データインポート", "🧠 知見管理", "🧹 データクリーニング", "📊 データ分析"])
    
    with import_tab:
        show_data_import_interface(data_system)
    
    with knowledge_tab:
        show_knowledge_management(data_system)
    
    with clean_tab:
        show_data_cleaning_interface()
    
    with analysis_tab:
        show_data_analysis(data_system)

def analyze_multiple_pdfs(pdf_files: List, data_system, max_workers=4, show_detailed_results=True):
    """複数PDFファイルの並行解析処理"""
    
    # 全体の進捗表示
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    results_placeholder = st.empty()
    
    # 結果格納用
    all_results = []
    successful_files = 0
    failed_files = 0
    total_media_extracted = 0
    total_insights_extracted = 0
    
    # プログレスバーの初期化
    progress_bar = progress_placeholder.progress(0)
    status_placeholder.info("📄 解析準備中...")
    
    def process_single_pdf(file_info):
        """単一PDFファイルの処理"""
        file, index = file_info
        try:
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file.getvalue())
                tmp_file_path = tmp_file.name
            
            # PDF解析実行
            result = data_system.extract_pdf_insights(tmp_file_path)
            
            # 一時ファイル削除
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            
            return {
                'file_name': file.name,
                'index': index,
                'success': result.get('success', False),
                'result': result,
                'file_size': len(file.getvalue()) / 1024  # KB
            }
            
        except Exception as e:
            return {
                'file_name': file.name,
                'index': index,
                'success': False,
                'error': str(e),
                'file_size': len(file.getvalue()) / 1024  # KB
            }
    
    # 並行処理での解析実行
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(pdf_files))) as executor:
        # ファイルにインデックスを付与
        file_list = [(file, i) for i, file in enumerate(pdf_files)]
        
        # 非同期実行
        future_to_file = {executor.submit(process_single_pdf, file_info): file_info for file_info in file_list}
        
        # 結果の収集
        completed = 0
        for future in concurrent.futures.as_completed(future_to_file):
            completed += 1
            progress = completed / len(pdf_files)
            progress_bar.progress(progress)
            
            # 現在の状況を更新
            status_placeholder.info(f"📄 解析中... ({completed}/{len(pdf_files)}) - {progress*100:.1f}%完了")
            
            try:
                result = future.result()
                all_results.append(result)
                
                if result['success']:
                    successful_files += 1
                    if 'result' in result:
                        total_media_extracted += result['result'].get('media_extracted', 0)
                        total_insights_extracted += result['result'].get('insights_extracted', 0)
                else:
                    failed_files += 1
                    
            except Exception as e:
                failed_files += 1
                all_results.append({
                    'file_name': 'Unknown',
                    'success': False,
                    'error': str(e)
                })
    
    # 結果表示
    progress_placeholder.empty()
    
    # 全体サマリー
    if successful_files > 0:
        status_placeholder.success(f"✅ 解析完了！ 成功: {successful_files}件 / 失敗: {failed_files}件")
        
        # カラム入れ子エラー回避のため、メトリクスを縦並びで表示
        st.metric("📺 総メディア情報", f"{total_media_extracted}件")
        st.metric("🧠 総知見情報", f"{total_insights_extracted}件")
        st.metric("📊 解析成功率", f"{successful_files/len(pdf_files)*100:.1f}%")
    else:
        status_placeholder.error(f"❌ 全ファイルの解析に失敗しました")
    
    # 詳細結果表示（オプション）
    if show_detailed_results:
        with results_placeholder.container():
            st.markdown("##### 📋 詳細解析結果")
            
            # 成功したファイル
            if successful_files > 0:
                with st.expander(f"✅ 成功したファイル ({successful_files}件)", expanded=True):
                    for result in all_results:
                        if result['success']:
                            media_count = result['result'].get('media_extracted', 0)
                            insights_count = result['result'].get('insights_extracted', 0)
                            st.success(f"📄 **{result['file_name']}** ({result['file_size']:.1f} KB)")
                            st.write(f"   📺 メディア情報: {media_count}件 | 🧠 知見情報: {insights_count}件")
            
            # 失敗したファイル
            if failed_files > 0:
                with st.expander(f"❌ 失敗したファイル ({failed_files}件)", expanded=False):
                    for result in all_results:
                        if not result['success']:
                            st.error(f"📄 **{result['file_name']}** ({result.get('file_size', 0):.1f} KB)")
                            if 'error' in result:
                                st.write(f"   エラー: {result['error']}")
                            elif 'result' in result and 'error' in result['result']:
                                st.write(f"   エラー: {result['result']['error']}")
    else:
        # 簡易サマリーのみ
        results_placeholder.info("💡 詳細結果の表示がオフになっています。設定で有効にできます。")

def show_data_import_interface(data_system):
    """データインポートインターフェース（改善版）"""
    st.markdown("#### 📥 データインポート・管理")
    
    # タブ構成で各データタイプを分離
    tab1, tab2, tab3 = st.tabs([
        "📊 イベント集客実績", 
        "📺 媒体情報",
        "📈 インポート履歴"
    ])
    
    with tab1:
        # イベント集客実績インポート
        st.markdown("##### 📊 イベント集客実績のインポート")
        
        # a. 対象イベント情報（手入力）
        st.markdown("#### 📝 a. 対象イベント情報（手入力）")
        
        col1, col2 = st.columns(2)
        with col1:
            event_name = st.text_input("イベント名", key="event_name_input", 
                                     placeholder="例：AI技術セミナー 2025")
            event_theme = st.text_input("イベントテーマ・内容", key="event_theme_input", 
                                      placeholder="例：生成AIの最新動向と実装方法")
        
        with col2:
            event_category = st.selectbox("イベントカテゴリ", 
                                        ["conference", "seminar", "workshop", "webinar", "networking", "product_launch"],
                                        format_func=lambda x: {
                                            "conference": "カンファレンス",
                                            "seminar": "セミナー", 
                                            "workshop": "ワークショップ",
                                            "webinar": "ウェビナー",
                                            "networking": "ネットワーキング",
                                            "product_launch": "製品発表"
                                        }[x],
                                        key="event_category_input")
            event_date = st.date_input("開催日", key="event_date_input")
        
        # ターゲット選択（複数選択可能）
        st.markdown("**ターゲット設定**")
        col_target1, col_target2, col_target3 = st.columns(3)
        
        with col_target1:
            # 業種の選択肢（右側サイドバーと同じ34業種）
            industry_options_import = ["すべて", "輸送用機器", "電気機器", "小売業", "卸売業", "医薬品", "その他製品", "精密機器", "不動産業", "陸運業", "鉄鋼", "鉱業", "石油・石炭製品", "非鉄金属", "空運業", "ガラス・土石製品", "パルプ・紙", "水産・農林業", "銀行業", "サービス業", "情報・通信業", "化学", "保険業", "食料品", "機械", "ゴム製品", "建設業", "証券、商品先物取引業", "電気・ガス業", "海運業", "その他金融業", "繊維製品", "金属製品", "倉庫・運輸関連業", "その他"]
            
            # セッション状態の初期化
            if 'selected_industries_import' not in st.session_state:
                st.session_state.selected_industries_import = ["情報・通信業"]
            
            # 「すべて」選択の処理
            def on_industries_import_change():
                selected = st.session_state.target_industries_multi
                if "すべて" in selected and "すべて" not in st.session_state.selected_industries_import:
                    # 「すべて」が新しく選択された場合
                    st.session_state.selected_industries_import = industry_options_import.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_industries_import:
                    # 「すべて」が解除された場合
                    st.session_state.selected_industries_import = []
                elif "すべて" in selected:
                    # 「すべて」が選択されている状態で他が変更された場合
                    if len(selected) < len(industry_options_import):
                        # 一部解除された場合、「すべて」を除外
                        st.session_state.selected_industries_import = [opt for opt in selected if opt != "すべて"]
                else:
                    # 通常の選択
                    st.session_state.selected_industries_import = selected
                    # 全て選択されている場合、「すべて」を追加
                    if len(selected) == len(industry_options_import) - 1:
                        st.session_state.selected_industries_import = ["すべて"] + selected
            
            target_industries = st.multiselect(
                "業種",
                options=industry_options_import,
                default=st.session_state.selected_industries_import,
                key="target_industries_multi",
                on_change=on_industries_import_change,
                help="複数選択可能です。「すべて」を選択すると全業種が対象になります。"
            )
        
        with col_target2:
            # 職種の選択肢（右側サイドバーと同じ31職種）
            job_title_options_import = ["すべて", "CTO", "VPoE", "EM", "フロントエンドエンジニア", "インフラエンジニア", "フルスタックエンジニア", "モバイルエンジニア", "セキュリティエンジニア", "アプリケーションエンジニア・ソリューションアーキテクト", "データサイエンティスト", "情報システム", "ネットワークエンジニア", "UXエンジニア", "デザイナー", "学生", "データアナリスト", "CPO", "VPoT/VPoP", "テックリード", "バックエンドエンジニア", "SRE", "プロダクトマネージャー", "DevOpsエンジニア", "QAエンジニア", "機械学習エンジニア", "プロジェクトマネージャー", "SIer", "ゲーム開発エンジニア", "組み込みエンジニア", "エンジニア以外", "データエンジニア"]
            
            # セッション状態の初期化
            if 'selected_job_titles_import' not in st.session_state:
                st.session_state.selected_job_titles_import = ["フロントエンドエンジニア", "バックエンドエンジニア"]
            
            # 「すべて」選択の処理
            def on_job_titles_import_change():
                selected = st.session_state.target_job_titles_multi
                if "すべて" in selected and "すべて" not in st.session_state.selected_job_titles_import:
                    st.session_state.selected_job_titles_import = job_title_options_import.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_job_titles_import:
                    st.session_state.selected_job_titles_import = []
                elif "すべて" in selected:
                    if len(selected) < len(job_title_options_import):
                        st.session_state.selected_job_titles_import = [opt for opt in selected if opt != "すべて"]
                else:
                    st.session_state.selected_job_titles_import = selected
                    if len(selected) == len(job_title_options_import) - 1:
                        st.session_state.selected_job_titles_import = ["すべて"] + selected
            
            target_job_titles = st.multiselect(
                "職種",
                options=job_title_options_import,
                default=st.session_state.selected_job_titles_import,
                key="target_job_titles_multi",
                on_change=on_job_titles_import_change,
                help="複数選択可能です。「すべて」を選択すると全職種が対象になります。"
            )
        
        with col_target3:
            # 従業員規模の選択肢（右側サイドバーと同じ8段階）
            company_size_options_import = ["すべて", "10名以下", "11名～50名", "51名～100名", "101名～300名", "301名～500名", "501名～1,000名", "1,001～5,000名", "5,001名以上"]
            
            # セッション状態の初期化
            if 'selected_company_sizes_import' not in st.session_state:
                st.session_state.selected_company_sizes_import = ["101名～300名", "301名～500名"]
            
            # 「すべて」選択の処理
            def on_company_sizes_import_change():
                selected = st.session_state.target_company_sizes_multi
                if "すべて" in selected and "すべて" not in st.session_state.selected_company_sizes_import:
                    st.session_state.selected_company_sizes_import = company_size_options_import.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_company_sizes_import:
                    st.session_state.selected_company_sizes_import = []
                elif "すべて" in selected:
                    if len(selected) < len(company_size_options_import):
                        st.session_state.selected_company_sizes_import = [opt for opt in selected if opt != "すべて"]
                else:
                    st.session_state.selected_company_sizes_import = selected
                    if len(selected) == len(company_size_options_import) - 1:
                        st.session_state.selected_company_sizes_import = ["すべて"] + selected
            
            target_company_sizes = st.multiselect(
                "従業員規模",
                options=company_size_options_import,
                default=st.session_state.selected_company_sizes_import,
                key="target_company_sizes_multi",
                on_change=on_company_sizes_import_change,
                help="複数選択可能です。「すべて」を選択すると全規模が対象になります。"
            )
        
        st.divider()
        
        # b. 集客施策一覧と実績（CSV）
        st.markdown("#### 📊 b. 集客施策一覧と実績（CSVインポート）")
        
        with st.expander("📋 CSVフォーマット仕様", expanded=False):
            st.markdown("""
            **必須列:**
            - `施策名` または `Campaign Name` - 集客施策の名前
            - `リーチ数` または `Reach` - リーチ数
            - `CTR` - クリック率（%）
            - `CVR` - コンバージョン率（%）
            - `CV数` または `Conversions` - 申込者数
            - `費用` または `Cost` - 施策費用（円）
            - `CPA` - 獲得単価（円）
            
            **CSVサンプル:**
            ```
            施策名,リーチ数,CTR,CVR,CV数,費用,CPA
            Google広告,50000,3.5,2.8,49,200000,4082
            Facebook広告,30000,2.8,3.2,27,150000,5556
            メールマーケティング,10000,5.0,4.0,20,0,0
            ```
            """)
        
        uploaded_campaign_csv = st.file_uploader(
            "📊 集客施策実績CSVファイルを選択",
            type=['csv'],
            key="campaign_results_csv",
            help="集客施策の実績データを含むCSVファイル"
        )
        
        st.divider()
        
        # c. 申込者情報（CSV）
        st.markdown("#### 👥 c. 申込者情報（CSVインポート）")
        
        with st.expander("📋 CSVフォーマット仕様", expanded=False):
            st.markdown("""
            **必須列:**
            - `役職` または `Position` - 申込者の役職
            - `職種` または `Job Title` - 申込者の職種
            - `企業名` または `Company` - 申込者の企業名
            - `業種` または `Industry` - 申込者の業種
            - `従業員規模` または `Company Size` - 申込者の企業規模
            
            **CSVサンプル:**
            ```
            役職,職種,企業名,業種,従業員規模
            部長,フロントエンドエンジニア,株式会社テック,情報・通信業,101名～300名
            マネージャー,データサイエンティスト,データ株式会社,情報・通信業,51名～100名
            取締役,プロダクトマネージャー,コンサル社,サービス業,1,001～5,000名
            ```
            """)
        
        uploaded_applicant_csv = st.file_uploader(
            "📊 申込者情報CSVファイルを選択",
            type=['csv'],
            key="applicant_info_csv",
            help="申込者の詳細情報を含むCSVファイル"
        )
        
        # インポート処理
        if uploaded_applicant_csv is not None:
            # プレビュー機能
            if st.button("👀 申込者データプレビュー", key="preview_conference_csv"):
                try:
                    import tempfile
                    import os
                    
                    # 一時ファイルに保存
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(uploaded_applicant_csv.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # プレビュー表示
                    df_preview = pd.read_csv(tmp_file_path, encoding='utf-8-sig')
                    st.markdown("**📋 申込者データプレビュー（最初の5行）:**")
                    st.dataframe(df_preview.head(), use_container_width=True)
                    st.info(f"📊 {len(df_preview)}行 x {len(df_preview.columns)}列の申込者データを検出")
                    
                    # 一時ファイル削除
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    st.error(f"❌ プレビューエラー: {str(e)}")
        
        # インポート実行
        col_import1, col_import2 = st.columns(2)
        
        with col_import1:
            if st.button("📥 イベント実績をインポート", type="primary", key="import_conference_data"):
                # 基本情報のバリデーション
                if not event_name.strip():
                    st.error("❌ イベント名を入力してください")
                elif not event_theme.strip():
                    st.error("❌ テーマを入力してください")
                elif not target_industries and not target_job_titles and not target_company_sizes:
                    st.error("❌ ターゲットを最低一つ選択してください")
                elif uploaded_applicant_csv is None:
                    st.error("❌ 申込者データCSVファイルをアップロードしてください")
                else:
                    with st.spinner("🏆 イベント実績を処理中..."):
                        try:
                            # ターゲット情報を結合（「すべて」を除外して実際の値のみ使用）
                            target_info = []
                            
                            # 業種の処理
                            industries_actual = [x for x in target_industries if x != "すべて"] if "すべて" not in target_industries else [x for x in industry_options_import if x != "すべて"]
                            if industries_actual:
                                target_info.extend([f"業種:{x}" for x in industries_actual])
                            
                            # 職種の処理
                            job_titles_actual = [x for x in target_job_titles if x != "すべて"] if "すべて" not in target_job_titles else [x for x in job_title_options_import if x != "すべて"]
                            if job_titles_actual:
                                target_info.extend([f"職種:{x}" for x in job_titles_actual])
                            
                            # 従業員規模の処理
                            company_sizes_actual = [x for x in target_company_sizes if x != "すべて"] if "すべて" not in target_company_sizes else [x for x in company_size_options_import if x != "すべて"]
                            if company_sizes_actual:
                                target_info.extend([f"従業員規模:{x}" for x in company_sizes_actual])
                            
                            # 基本情報を整理
                            event_info = {
                                "event_name": event_name.strip(),
                                "theme": event_theme.strip(),
                                "category": event_category,
                                "target": ", ".join(target_info),
                                "target_attendees": 0,  # デフォルト値
                                "budget": 0,  # デフォルト値
                                "event_date": str(event_date)
                            }
                            
                            # CSV処理
                            import tempfile
                            import os
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                                tmp_file.write(uploaded_applicant_csv.getvalue())
                                tmp_file_path = tmp_file.name
                            
                            # インポート実行
                            result = process_conference_import(tmp_file_path, event_info, data_system)
                            
                            # 結果表示
                            if result["success"]:
                                st.success(f"✅ イベント実績をインポートしました！")
                                st.info(f"📊 イベント: {event_info['event_name']}")
                                st.info(f"👥 申込者データ: {result.get('applicant_count', 0)}件")
                                
                                if result.get("errors"):
                                    st.warning(f"⚠️ {len(result['errors'])}件のエラーがありました:")
                                    with st.expander("エラー詳細"):
                                        for error in result["errors"]:
                                            st.write(f"- {error}")
                            else:
                                st.error(f"❌ インポートに失敗しました: {result.get('error', '不明なエラー')}")
                            
                            # 一時ファイル削除
                            os.unlink(tmp_file_path)
                            
                        except Exception as e:
                            st.error(f"❌ インポートエラー: {str(e)}")
        
        with col_import2:
            # テンプレートダウンロード
            template_csv = """職種,役職,企業名,業種,従業員規模
フロントエンドエンジニア,シニアエンジニア,株式会社テック,情報・通信業,301名～500名
データサイエンティスト,マネージャー,データ株式会社,情報・通信業,101名～300名
プロダクトマネージャー,部長,プロダクト社,製造業,1,001～5,000名
デザイナー,課長,マーケティング社,サービス業,101名～300名
CTO,取締役,テック社,情報・通信業,501名～1,000名
"""
            st.download_button(
                label="📄 申込者データテンプレートをダウンロード",
                data=template_csv,
                file_name="conference_applicants_template.csv",
                mime="text/csv"
            )
    
    with tab2:
        # 有償メディアインポート
        st.markdown("##### 💰 有償メディアのインポート")
        
        # 手入力セクション
        st.markdown("#### 📝 基本情報（手入力）")
        col1, col2 = st.columns(2)
        
        with col1:
            paid_media_event_name = st.text_input("イベント名", key="paid_event_name", 
                                                placeholder="例：AI技術カンファレンス 2025")
            paid_media_theme = st.text_input("イベントテーマ", key="paid_theme", 
                                           placeholder="例：次世代AI技術")
        
        with col2:
            paid_media_category = st.selectbox("イベントカテゴリ", 
                                             ["conference", "seminar", "workshop", "webinar", "networking", "product_launch"],
                                             format_func=lambda x: {
                                                 "conference": "カンファレンス",
                                                 "seminar": "セミナー", 
                                                 "workshop": "ワークショップ",
                                                 "webinar": "ウェビナー",
                                                 "networking": "ネットワーキング",
                                                 "product_launch": "製品発表"
                                             }[x],
                                             key="paid_category")
            paid_media_target = st.text_input("イベントターゲット", key="paid_target", 
                                            placeholder="例：経営者・マネージャー")
        
        # 追加情報
        col3, col4, col5 = st.columns(3)
        with col3:
            paid_media_name = st.text_input("有償メディア名", key="paid_media_name", 
                                          placeholder="例：日経ビジネス")
        with col4:
            paid_media_cost = st.number_input("掲載料金（円）", min_value=0, value=0, key="paid_cost")
        with col5:
            paid_media_date = st.date_input("掲載日", key="paid_date")
        
        st.divider()
        
        # CSVアップロードセクション
        st.markdown("#### 📊 申込者詳細データ（CSVインポート）")
        
        # フォーマット説明
        with st.expander("📋 CSVフォーマット仕様", expanded=False):
            st.markdown("""
            **必須列:**
            - `職種` または `Job Title` - 申込者の職種
            - `役職` または `Position` - 申込者の役職
            - `企業名` または `Company` - 申込者の企業名
            - `業種` または `Industry` - 申込者の業種
            - `従業員規模` または `Company Size` - 申込者の企業規模
            
            **推奨列:**
            - `申込経路` または `Source` - 申込経路（有償メディア名）
            - `申込日` または `Apply Date` - 申込日
            
            **CSVサンプル:**
            ```
            職種,役職,企業名,業種,従業員規模,申込経路,申込日
            CTO,取締役,テック株式会社,情報・通信業,301名～500名,日経ビジネス,2025-01-10
            プロダクトマネージャー,部長,マーケティング社,サービス業,101名～300名,日経ビジネス,2025-01-11
            データサイエンティスト,マネージャー,コンサル社,サービス業,501名～1,000名,日経ビジネス,2025-01-12
            ```
            """)
        
        # CSVアップロード
        uploaded_paid_media_csv = st.file_uploader(
            "📊 有償メディア経由申込者データCSVファイルを選択",
            type=['csv'],
            key="paid_media_applicant_csv",
            help="有償メディア経由の申込者の職種、役職、企業名、業種、従業員規模を含むCSVファイル"
        )
        
        # インポート処理
        if uploaded_paid_media_csv is not None:
            # プレビュー機能
            if st.button("👀 申込者データプレビュー", key="preview_paid_media_csv"):
                try:
                    import tempfile
                    import os
                    
                    # 一時ファイルに保存
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(uploaded_paid_media_csv.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # プレビュー表示
                    df_preview = pd.read_csv(tmp_file_path, encoding='utf-8-sig')
                    st.markdown("**📋 申込者データプレビュー（最初の5行）:**")
                    st.dataframe(df_preview.head(), use_container_width=True)
                    st.info(f"📊 {len(df_preview)}行 x {len(df_preview.columns)}列の申込者データを検出")
                    
                    # 一時ファイル削除
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    st.error(f"❌ プレビューエラー: {str(e)}")
        
        # インポート実行
        col_import1, col_import2 = st.columns(2)
        
        with col_import1:
            if st.button("📥 有償メディア実績をインポート", type="primary", key="import_paid_media_data"):
                # 基本情報のバリデーション
                if not paid_media_event_name.strip():
                    st.error("❌ イベント名を入力してください")
                elif not paid_media_theme.strip():
                    st.error("❌ イベントテーマを入力してください")
                elif not paid_media_target.strip():
                    st.error("❌ イベントターゲットを入力してください")
                elif not paid_media_name.strip():
                    st.error("❌ 有償メディア名を入力してください")
                elif uploaded_paid_media_csv is None:
                    st.error("❌ 申込者データCSVファイルをアップロードしてください")
                else:
                    with st.spinner("💰 有償メディア実績を処理中..."):
                        try:
                            # 基本情報を整理
                            media_info = {
                                "event_name": paid_media_event_name.strip(),
                                "event_theme": paid_media_theme.strip(),
                                "event_category": paid_media_category,
                                "event_target": paid_media_target.strip(),
                                "media_name": paid_media_name.strip(),
                                "media_cost": paid_media_cost,
                                "media_date": str(paid_media_date)
                            }
                            
                            # CSV処理
                            import tempfile
                            import os
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                                tmp_file.write(uploaded_paid_media_csv.getvalue())
                                tmp_file_path = tmp_file.name
                            
                            # インポート実行
                            result = process_paid_media_import(tmp_file_path, media_info, data_system)
                            
                            # 結果表示
                            if result["success"]:
                                st.success(f"✅ 有償メディア実績をインポートしました！")
                                st.info(f"📊 イベント: {media_info['event_name']}")
                                st.info(f"💰 メディア: {media_info['media_name']}")
                                st.info(f"👥 申込者データ: {result.get('applicant_count', 0)}件")
                                
                                if result.get("errors"):
                                    st.warning(f"⚠️ {len(result['errors'])}件のエラーがありました:")
                                    with st.expander("エラー詳細"):
                                        for error in result["errors"]:
                                            st.write(f"- {error}")
                            else:
                                st.error(f"❌ インポートに失敗しました: {result.get('error', '不明なエラー')}")
                            
                            # 一時ファイル削除
                            os.unlink(tmp_file_path)
                            
                        except Exception as e:
                            st.error(f"❌ インポートエラー: {str(e)}")
        
        with col_import2:
            # テンプレートダウンロード
            template_csv = """職種,役職,企業名,業種,従業員規模,申込経路,申込日
CTO,取締役,テック株式会社,情報・通信業,301名～500名,日経ビジネス,2025-01-10
プロダクトマネージャー,部長,マーケティング社,サービス業,101名～300名,日経ビジネス,2025-01-11
データサイエンティスト,マネージャー,コンサル社,サービス業,501名～1,000名,日経ビジネス,2025-01-12
バックエンドエンジニア,シニアエンジニア,フィンテック社,銀行業,1,001～5,000名,日経ビジネス,2025-01-13
"""
            st.download_button(
                label="📄 有償メディア申込者テンプレートをダウンロード",
                data=template_csv,
                file_name="paid_media_applicants_template.csv",
                mime="text/csv"
            )
        
        st.divider()
        
        # WEB広告・媒体情報インポート
        st.markdown("##### 🌐 WEB広告・媒体情報のインポート")
        
        # ファイル形式選択
        web_ad_format = st.selectbox(
            "📁 インポート形式を選択",
            ["CSV", "PDF", "PowerPoint (PPT/PPTX)"],
            key="web_ad_format_select"
        )
        
        if web_ad_format == "CSV":
            # CSVフォーマット説明
            with st.expander("📋 CSVフォーマット仕様", expanded=False):
                st.markdown("""
                **必須列:**
                - `広告名` または `Ad Name` - WEB広告キャンペーン名
                - `プラットフォーム` または `Platform` - 広告プラットフォーム（Google、Meta、Yahoo等）
                
                **推奨列:**
                - `広告タイプ` または `Ad Type` - 広告の種類（検索広告、ディスプレイ広告、SNS広告等）
                - `対象読者` または `Target Audience` - ターゲットオーディエンス
                - `CTR` - クリック率（%）
                - `CVR` - コンバージョン率（%）
                - `CPC` - クリック単価（円）
                - `CPA` - 獲得単価（円）
                - `インプレッション` または `Impressions` - インプレッション数
                - `配信期間` または `Duration` - 配信期間
                - `予算` または `Budget` - 広告予算
                
                **CSVサンプル:**
                ```
                広告名,プラットフォーム,広告タイプ,対象読者,CTR,CVR,CPC,CPA,インプレッション,配信期間,予算
                AI技術セミナー検索広告,Google,検索広告,エンジニア,3.5,2.8,120,4200,50000,2週間,300000
                ```
                """)
            
            uploaded_web_ad_csv = st.file_uploader(
                "📊 WEB広告データCSVファイルを選択",
                type=['csv'],
                key="web_ad_csv_upload"
            )
            
            if uploaded_web_ad_csv is not None:
                if st.button("📥 WEB広告CSVをインポート", type="primary", key="import_web_ad_csv"):
                    process_web_ad_csv_import(uploaded_web_ad_csv, data_system)
        
        elif web_ad_format == "PDF":
            # PDF説明
            st.markdown("""
            **📄 PDFからの情報抽出:**
            - WEB広告キャンペーン情報
            - パフォーマンスレポートデータ
            - 広告運用実績や効果測定
            """)
            
            uploaded_web_ad_pdf = st.file_uploader(
                "📄 WEB広告情報PDFファイルを選択",
                type=['pdf'],
                key="web_ad_pdf_upload"
            )
            
            if uploaded_web_ad_pdf is not None:
                if st.button("📥 WEB広告PDFを解析・インポート", type="primary", key="import_web_ad_pdf"):
                    process_media_pdf_import(uploaded_web_ad_pdf, data_system)
        
        elif web_ad_format == "PowerPoint (PPT/PPTX)":
            # PowerPoint説明
            st.markdown("""
            **📊 PowerPointからの情報抽出:**
            - 広告レポート資料の情報
            - パフォーマンスデータ表・グラフ
            - 広告運用結果や分析データ
            """)
            
            uploaded_web_ad_ppt = st.file_uploader(
                "📊 WEB広告情報PowerPointファイルを選択",
                type=['ppt', 'pptx'],
                key="web_ad_ppt_upload"
            )
            
            if uploaded_web_ad_ppt is not None:
                if st.button("📥 PowerPointを解析・インポート", type="primary", key="import_web_ad_ppt"):
                    process_media_ppt_import(uploaded_web_ad_ppt, data_system)
    
    with tab3:
        # インポート履歴・統計
        st.markdown("##### 📊 インポート履歴・統計")
        show_import_history_and_stats(data_system)

def process_media_csv_import(uploaded_file, data_system):
    """メディアCSVインポート処理"""
    with st.spinner("📊 メディアCSVデータを処理中..."):
        try:
            import tempfile
            import os
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # インポート実行
            result = data_system.import_existing_csv(tmp_file_path, "media")
            
            # 結果表示
            if result["success"]:
                st.success(f"✅ {result['imported']}件のメディアデータをインポートしました！")
            else:
                st.error(f"❌ インポートに失敗しました: {result['error']}")
            
            # 一時ファイル削除
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ インポートエラー: {str(e)}")

def process_media_pdf_import(uploaded_file, data_system):
    """メディアPDFインポート処理"""
    with st.spinner("📄 PDFを解析中..."):
        try:
            import tempfile
            import os
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # PDF解析実行
            result = data_system.extract_pdf_insights(tmp_file_path)
            
            # 結果表示
            if result["success"]:
                st.success("✅ PDFの解析が完了しました！")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("抽出されたメディア情報", f"{result.get('media_extracted', 0)}件")
                with col2:
                    st.metric("抽出された知見", f"{result.get('insights_extracted', 0)}件")
                
                if result.get('analysis_method'):
                    st.info(f"🔬 解析方法: {result['analysis_method']}")
                
                if result.get('confidence'):
                    st.info(f"🎯 解析信頼度: {result['confidence']*100:.1f}%")
            else:
                st.error(f"❌ PDF解析に失敗しました: {result['error']}")
            
            # 一時ファイル削除
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ PDF解析エラー: {str(e)}")

def process_media_ppt_import(uploaded_file, data_system):
    """PowerPointインポート処理"""
    with st.spinner("📊 PowerPointを解析中..."):
        try:
            import tempfile
            import os
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # PowerPoint解析実行
            result = data_system.extract_pptx_insights(tmp_file_path)
            
            # 結果表示
            if result["success"]:
                st.success("✅ PowerPointの解析が完了しました！")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("抽出されたメディア情報", f"{result.get('media_extracted', 0)}件")
                with col2:
                    st.metric("抽出された知見", f"{result.get('insights_extracted', 0)}件")
                
                if result.get('analysis_method'):
                    st.info(f"🔬 解析方法: {result['analysis_method']}")
                
                if result.get('confidence'):
                    st.info(f"🎯 解析信頼度: {result['confidence']*100:.1f}%")
            else:
                st.error(f"❌ PowerPoint解析に失敗しました: {result['error']}")
            
            # 一時ファイル削除
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ PowerPoint解析エラー: {str(e)}")

def process_knowledge_file_import(uploaded_file, file_format, data_system):
    """知見ファイルインポート処理"""
    with st.spinner(f"📄 {file_format}ファイルを解析中..."):
        try:
            import tempfile
            import os
            
            if file_format == "Markdown (.md)":
                # Markdown処理
                content = uploaded_file.getvalue().decode('utf-8')
                result = process_markdown_knowledge(content, data_system)
                
            elif file_format == "PDF":
                # PDF処理
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                result = data_system.extract_pdf_insights(tmp_file_path)
                os.unlink(tmp_file_path)
                
            elif file_format == "Word文書 (.docx)":
                # Word文書処理
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                result = data_system.extract_docx_insights(tmp_file_path)
                os.unlink(tmp_file_path)
                
            elif file_format == "テキストファイル (.txt)":
                # テキストファイル処理
                content = uploaded_file.getvalue().decode('utf-8')
                result = process_text_knowledge(content, data_system)
                
            else:
                # その他の処理（今後実装）
                st.warning(f"🚧 {file_format}解析機能は開発中です。まもなく対応予定です！")
                return
            
            # 結果表示
            if result.get("success"):
                st.success("✅ ファイルの解析が完了しました！")
                
                if result.get('insights_extracted', 0) > 0:
                    st.metric("抽出された知見", f"{result['insights_extracted']}件")
                
                if result.get('media_extracted', 0) > 0:
                    st.metric("抽出されたメディア情報", f"{result['media_extracted']}件")
                    
            else:
                st.error(f"❌ ファイル解析に失敗しました: {result.get('error', '不明なエラー')}")
            
        except Exception as e:
            st.error(f"❌ ファイル解析エラー: {str(e)}")

def process_markdown_knowledge(content, data_system):
    """Markdownファイルから知見を抽出"""
    try:
        # Markdownパース（簡易版）
        lines = content.split('\n')
        
        title = ""
        category = "general"
        impact_score = 0.7
        confidence = 0.8
        knowledge_content = ""
        
        current_section = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('# '):
                title = line[2:].strip()
            elif line.startswith('**カテゴリ:**'):
                category = line.split(':')[1].strip()
            elif line.startswith('**影響度:**'):
                try:
                    impact_score = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('**信頼度:**'):
                try:
                    confidence = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('## '):
                current_section = line[3:].strip()
            elif line and not line.startswith('#') and not line.startswith('**'):
                knowledge_content += line + "\n"
        
        if title and knowledge_content:
            knowledge_id = data_system.add_manual_knowledge(
                category, title, knowledge_content.strip(),
                impact=impact_score
            )
            
            return {"success": True, "insights_extracted": 1, "knowledge_id": knowledge_id}
        else:
            return {"success": False, "error": "タイトルまたは内容が見つかりませんでした"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def show_import_history_and_stats(data_system):
    """インポート履歴と統計の表示"""
    try:
        # データ統計表示
        import sqlite3
        conn = sqlite3.connect(data_system.db_path)
        cursor = conn.cursor()
        
        # 各テーブルの件数取得
        tables_info = {
            "historical_events": "📅 イベントデータ",
            "media_basic_info": "📺 メディア基本情報", 
            "media_detailed_attributes": "🎯 メディア属性",
            "internal_knowledge": "🧠 社内知見"
        }
        
        st.markdown("**📊 現在のデータ統計:**")
        
        cols = st.columns(len(tables_info))
        
        for i, (table, label) in enumerate(tables_info.items()):
            with cols[i]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    st.metric(label, f"{count}件")
                except:
                    st.metric(label, "0件")
        
        conn.close()
        
        # 最近のデータ表示
        st.markdown("---")
        st.markdown("**📋 最近追加されたデータ:**")
        
        # 最近の知見表示
        conn = sqlite3.connect(data_system.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT title, category, source, created_at 
                FROM internal_knowledge 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            
            recent_knowledge = cursor.fetchall()
            
            if recent_knowledge:
                knowledge_df = pd.DataFrame(recent_knowledge, columns=[
                    'タイトル', 'カテゴリ', 'ソース', '作成日時'
                ])
                st.dataframe(knowledge_df, use_container_width=True, hide_index=True)
            else:
                st.info("💡 まだ知見データがありません")
                
        except Exception as e:
            st.warning(f"⚠️ データ取得エラー: {e}")
        
        finally:
            conn.close()
            
    except Exception as e:
        st.error(f"❌ 統計表示エラー: {str(e)}")

def show_knowledge_management(data_system):
    """知見管理インターフェースの改善版"""
    st.markdown("#### 🧠 社内知見の管理")
    
    # タブ構成で機能を分離
    tab1, tab2, tab3 = st.tabs(["➕ 知見追加", "📚 知見一覧", "🔍 知見検索"])
    
    with tab1:
        # 知見追加の改善UI
        st.markdown("##### ✍️ 新しい知見を追加")
        
        # 2列レイアウト
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # 知見のタイトル
            knowledge_title = st.text_input(
                "📝 知見のタイトル*",
                placeholder="例: メール配信の最適なタイミング",
                help="この知見を簡潔に表すタイトルを入力してください"
            )
            
            # カテゴリ選択（改善版）
            category_options = {
                "campaign": "📢 キャンペーン・施策",
                "media": "📺 メディア・媒体",
                "audience": "👥 オーディエンス・ターゲット",
                "budget": "💰 予算・コスト",
                "timing": "⏰ タイミング・時期",
                "general": "📋 一般"
            }
            
            knowledge_category = st.selectbox(
                "🏷️ カテゴリ*",
                options=list(category_options.keys()),
                format_func=lambda x: category_options[x],
                help="知見が最も関連するカテゴリを選択してください"
            )
            
            # 知見の内容
            knowledge_content = st.text_area(
                "📖 知見の詳細内容*",
                height=120,
                placeholder="例: 火曜日の午前10時に配信すると開封率が最も高い。特にBtoB向けイベントでは...",
                help="具体的で実用的な内容を記載してください"
            )
            
            # 適用条件（改善版）
            st.markdown("**🎯 適用条件（オプション）**")
            conditions_text = st.text_area(
                "この知見が適用される条件があれば記載してください",
                height=80,
                placeholder="例: BtoBイベント、参加者数100名以上、予算50万円以上",
                help="条件を指定すると、該当するイベントでのみこの知見が提案されます"
            )
        
        with col_right:
            # 知見の重要度設定
            st.markdown("**⚖️ 知見の評価**")
            
            impact_score = st.slider(
                "📊 影響度",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="この知見がイベント成功に与える影響の大きさ"
            )
            
            confidence_score = st.slider(
                "🎯 信頼度",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="この知見の確実性・信頼性"
            )
            
            # プレビュー
            st.markdown("**👀 プレビュー**")
            if knowledge_title and knowledge_content:
                with st.container():
                    st.markdown(f"**{knowledge_title}**")
                    st.markdown(f"📍 {category_options[knowledge_category]}")
                    st.markdown(f"📝 {knowledge_content[:100]}{'...' if len(knowledge_content) > 100 else ''}")
                    st.markdown(f"📊 影響度: {impact_score} | 信頼度: {confidence_score}")
            else:
                st.info("💡 上記フォームを入力するとプレビューが表示されます")
        
        # 知見追加ボタン
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn2:
            add_knowledge_btn = st.button(
                "💾 知見を追加",
                type="primary",
                use_container_width=True,
                disabled=not (knowledge_title and knowledge_content)
            )
        
        if add_knowledge_btn and knowledge_title and knowledge_content:
            try:
                # 条件の処理
                conditions = None
                if conditions_text.strip():
                    # 条件をリスト形式に変換
                    conditions_list = [c.strip() for c in conditions_text.split(',') if c.strip()]
                    conditions = {"general": conditions_list}
                
                knowledge_id = data_system.add_manual_knowledge(
                    knowledge_category, 
                    knowledge_title, 
                    knowledge_content,
                    conditions=conditions,
                    impact=impact_score
                )
                
                st.success(f"✅ 知見を追加しました！ (ID: {knowledge_id})")
                st.balloons()  # 成功時のアニメーション
                
                # フォームリセット
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 知見追加エラー: {str(e)}")
    
    with tab2:
        # 知見一覧の改善表示
        st.markdown("##### 📚 登録済み知見一覧")
        
        try:
            import sqlite3
            conn = sqlite3.connect(data_system.db_path)
            cursor = conn.cursor()
            
            # 知見データの取得（詳細情報付き）
            cursor.execute('''
                SELECT id, category, title, content, impact_score, confidence, 
                       source, created_at, conditions
                FROM internal_knowledge 
                ORDER BY impact_score DESC, created_at DESC
            ''')
            
            knowledge_data = cursor.fetchall()
            conn.close()
            
            if knowledge_data:
                # フィルタリング機能
                col_filter1, col_filter2, col_filter3 = st.columns(3)
                
                with col_filter1:
                    # カテゴリフィルター
                    all_categories = list(set([k[1] for k in knowledge_data]))
                    selected_categories = st.multiselect(
                        "🏷️ カテゴリフィルター",
                        all_categories,
                        default=all_categories,
                        format_func=lambda x: category_options.get(x, x)
                    )
                
                with col_filter2:
                    # 信頼度フィルター
                    min_confidence = st.slider(
                        "🎯 最小信頼度",
                        0.0, 1.0, 0.0, 0.1
                    )
                
                with col_filter3:
                    # 影響度フィルター
                    min_impact = st.slider(
                        "📊 最小影響度",
                        0.0, 1.0, 0.0, 0.1
                    )
                
                # フィルタリング適用
                filtered_knowledge = [
                    k for k in knowledge_data 
                    if k[1] in selected_categories 
                    and k[4] >= min_impact 
                    and k[5] >= min_confidence
                ]
                
                st.markdown(f"**表示中: {len(filtered_knowledge)}件 / 全{len(knowledge_data)}件**")
                
                # 知見カード表示
                for knowledge in filtered_knowledge:
                    knowledge_id, category, title, content, impact, confidence, source, created_at, conditions = knowledge
                    
                    with st.expander(f"🧠 {title} [{category_options.get(category, category)}]"):
                        col_info, col_actions = st.columns([3, 1])
                        
                        with col_info:
                            st.markdown(f"**📖 内容:** {content}")
                            
                            if conditions:
                                try:
                                    conditions_data = json.loads(conditions)
                                    if isinstance(conditions_data, dict) and 'general' in conditions_data:
                                        st.markdown(f"**🎯 適用条件:** {', '.join(conditions_data['general'])}")
                                except:
                                    pass
                            
                            st.markdown(f"**📊 評価:** 影響度 {impact:.1f} | 信頼度 {confidence:.1f}")
                            st.markdown(f"**📅 作成日:** {created_at}")
                            st.markdown(f"**📋 ソース:** {source}")
                        
                        with col_actions:
                            # アクション（将来の拡張用）
                            st.markdown("**🔧 アクション**")
                            if st.button(f"📝 編集", key=f"edit_{knowledge_id}", disabled=True):
                                st.info("編集機能は今後実装予定です")
                            if st.button(f"🗑️ 削除", key=f"delete_{knowledge_id}", disabled=True):
                                st.info("削除機能は今後実装予定です")
            else:
                st.info("💡 まだ知見データがありません。「知見追加」タブから追加してください。")
        
        except Exception as e:
            st.error(f"❌ 知見表示エラー: {str(e)}")
    
    with tab3:
        # 知見検索機能
        st.markdown("##### 🔍 知見検索・フィルタリング")
        
        # 検索機能
        search_query = st.text_input(
            "🔍 キーワード検索",
            placeholder="例: メール, タイミング, BtoB",
            help="タイトルや内容から知見を検索します"
        )
        
        if search_query:
            try:
                import sqlite3
                conn = sqlite3.connect(data_system.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, category, title, content, impact_score, confidence, source
                    FROM internal_knowledge 
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY impact_score DESC
                ''', (f'%{search_query}%', f'%{search_query}%'))
                
                search_results = cursor.fetchall()
                conn.close()
                
                if search_results:
                    st.success(f"🎯 {len(search_results)}件の知見が見つかりました")
                    
                    for result in search_results:
                        knowledge_id, category, title, content, impact, confidence, source = result
                        
                        with st.container():
                            st.markdown(f"**🧠 {title}**")
                            st.markdown(f"📍 {category_options.get(category, category)} | 📊 影響度: {impact:.1f} | 🎯 信頼度: {confidence:.1f}")
                            st.markdown(f"📖 {content}")
                            st.markdown("---")
                else:
                    st.warning(f"🤷‍♂️ 「{search_query}」に関する知見が見つかりませんでした")
            
            except Exception as e:
                st.error(f"❌ 検索エラー: {str(e)}")
        else:
            st.info("💡 上記の検索ボックスにキーワードを入力してください")

def show_data_analysis(data_system):
    """データ分析インターフェース"""
    st.markdown("#### 📊 データ分析・インサイト")
    
    # 基本統計
    st.markdown("##### 📈 データ統計")
    
    try:
        import sqlite3
        conn = sqlite3.connect(data_system.db_path)
        
        # イベントパフォーマンス分析
        events_df = pd.read_sql_query('''
            SELECT event_name, target_attendees, actual_attendees, budget, actual_cost,
                   campaigns_used, performance_metrics
            FROM historical_events
        ''', conn)
        
        if len(events_df) > 0:
            st.markdown("###### 🎯 イベントパフォーマンス")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_conversion = (events_df['actual_attendees'] / events_df['target_attendees']).mean() * 100
                st.metric("平均達成率", f"{avg_conversion:.1f}%")
            
            with col2:
                avg_cpa = (events_df['actual_cost'] / events_df['actual_attendees']).mean()
                st.metric("平均CPA", f"¥{avg_cpa:,.0f}")
            
            with col3:
                total_events = len(events_df)
                st.metric("総イベント数", f"{total_events}件")
            
            # イベント成果の可視化
            if len(events_df) >= 3:
                fig = px.scatter(
                    events_df,
                    x='target_attendees',
                    y='actual_attendees',
                    size='budget',
                    hover_name='event_name',
                    title='イベント目標 vs 実績',
                    labels={'target_attendees': '目標申込数', 'actual_attendees': '実際申込数'}
                )
                fig.add_shape(
                    type="line", line=dict(dash="dash"),
                    x0=0, y0=0, x1=events_df['target_attendees'].max(), y1=events_df['target_attendees'].max()
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # メディア属性分析
        media_attrs_df = pd.read_sql_query('''
            SELECT media_name, attribute_category, attribute_name, attribute_value
            FROM media_detailed_attributes
        ''', conn)
        
        if len(media_attrs_df) > 0:
            st.markdown("###### 📺 メディア属性分析")
            
            # 属性カテゴリ別の分布
            category_counts = media_attrs_df['attribute_category'].value_counts()
            fig = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title='メディア属性カテゴリ分布'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ データ分析エラー: {str(e)}")

def show_data_cleaning_interface():
    """データクリーニングインターフェース"""
    st.markdown("#### 🧹 データクリーニング・管理")
    
    if not INTERNAL_DATA_AVAILABLE:
        st.error("🚫 データクリーニング機能が利用できません")
        return
    
    # データクリーナーの初期化
    if 'data_cleaner' not in st.session_state:
        st.session_state['data_cleaner'] = DataCleaner()
    
    cleaner = st.session_state['data_cleaner']
    
    # 現在のデータ状況表示
    st.markdown("##### 📊 現在のデータ状況")
    
    try:
        import sqlite3
        conn = sqlite3.connect(cleaner.db_path)
        cursor = conn.cursor()
        
        tables = ['historical_events', 'media_performance', 'media_detailed_attributes', 'internal_knowledge']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) FROM historical_events")
            events_count = cursor.fetchone()[0]
            st.metric("📅 イベント", f"{events_count}件")
        
        with col2:
            cursor.execute("SELECT COUNT(*) FROM media_performance")
            media_count = cursor.fetchone()[0]
            st.metric("📺 メディア", f"{media_count}件")
        
        with col3:
            cursor.execute("SELECT COUNT(*) FROM media_detailed_attributes")
            attrs_count = cursor.fetchone()[0]
            st.metric("🎯 属性", f"{attrs_count}件")
        
        with col4:
            cursor.execute("SELECT COUNT(*) FROM internal_knowledge")
            knowledge_count = cursor.fetchone()[0]
            st.metric("🧠 知見", f"{knowledge_count}件")
        
        # データ例の表示
        total_records = events_count + media_count + attrs_count + knowledge_count
        
        if total_records > 0:
            st.markdown("##### 📋 データ例")
            
            if events_count > 0:
                cursor.execute("SELECT event_name FROM historical_events LIMIT 3")
                event_samples = [row[0] for row in cursor.fetchall()]
                st.write(f"**イベント例**: {', '.join(event_samples)}")
            
            if media_count > 0:
                cursor.execute("SELECT media_name FROM media_performance LIMIT 3")
                media_samples = [row[0] for row in cursor.fetchall()]
                st.write(f"**メディア例**: {', '.join(media_samples)}")
        
        conn.close()
        
    except Exception as e:
        st.error(f"データ状況確認エラー: {str(e)}")
    
    st.markdown("---")
    
    # サンプルデータ検出
    st.markdown("##### 🔍 サンプルデータ検出")
    
    if st.button("🔍 サンプルデータをチェック", use_container_width=True):
        with st.spinner("サンプルデータを検出中..."):
            try:
                sample_data = cleaner.check_sample_data()
                total_samples = sum(len(items) for items in sample_data.values())
                
                if total_samples == 0:
                    st.success("✅ サンプルデータは検出されませんでした")
                else:
                    st.warning(f"⚠️ {total_samples}件のサンプルデータを検出しました")
                    
                    for table, items in sample_data.items():
                        if items:
                            with st.expander(f"📋 {table} ({len(items)}件)"):
                                for item in items:
                                    if table == "historical_events":
                                        st.write(f"- **{item['name']}** (ID: {item['id']}) - {item['reason']}")
                                    elif table == "media_performance":
                                        st.write(f"- **{item['name']}** (ID: {item['id']}) - {item['reason']}")
                                    elif table == "internal_knowledge":
                                        st.write(f"- **{item['title']}** (ID: {item['id']}) - {item['reason']}")
                    
                    # サンプルデータ削除ボタン
                    st.markdown("##### 🗑️ サンプルデータ削除")
                    
                    col_clean1, col_clean2 = st.columns(2)
                    
                    with col_clean1:
                        if st.button("🧹 サンプルデータのみ削除", type="secondary", use_container_width=True):
                            with st.spinner("サンプルデータを削除中..."):
                                try:
                                    removed = cleaner.remove_sample_data(sample_data)
                                    st.success(f"✅ サンプルデータを削除しました: {removed}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 削除エラー: {str(e)}")
                    
                    with col_clean2:
                        if st.button("🔄 全データリセット", type="primary", use_container_width=True):
                            if st.checkbox("⚠️ 全データ削除を確認"):
                                with st.spinner("全データをリセット中..."):
                                    try:
                                        backup_path = cleaner.reset_all_data()
                                        st.success(f"✅ 全データをリセットしました")
                                        st.info(f"📦 バックアップ: {backup_path}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ リセットエラー: {str(e)}")
                            else:
                                st.warning("⚠️ 確認チェックボックスにチェックを入れてください")
                    
                    # セッション状態に保存
                    st.session_state['detected_sample_data'] = sample_data
                
            except Exception as e:
                st.error(f"❌ サンプルデータ検出エラー: {str(e)}")
    
    # バックアップ管理
    st.markdown("---")
    st.markdown("##### 📦 バックアップ管理")
    
    col_backup1, col_backup2 = st.columns(2)
    
    with col_backup1:
        if st.button("📦 バックアップ作成", use_container_width=True):
            try:
                backup_path = cleaner.create_backup()
                st.success(f"✅ バックアップを作成しました")
                st.info(f"📁 場所: {backup_path}")
            except Exception as e:
                st.error(f"❌ バックアップ作成エラー: {str(e)}")
    
    with col_backup2:
        # バックアップ一覧を表示（簡易版）
        try:
            backup_dir = Path("data/backups")
            if backup_dir.exists():
                backups = list(backup_dir.glob("*.db"))
                if backups:
                    st.info(f"📋 利用可能なバックアップ: {len(backups)}個")
                else:
                    st.info("📋 バックアップはありません")
            else:
                st.info("📋 バックアップディレクトリがありません")
        except Exception as e:
            st.warning(f"バックアップ確認エラー: {str(e)}")

def show_supabase_data_management():
    """Supabase用のシンプルなデータ管理画面"""
    shared_db = st.session_state.get('shared_db')
    
    if not shared_db:
        st.error("❌ Supabaseデータベース接続がありません")
        return
    
    # タブ構成
    overview_tab, add_event_tab, view_data_tab = st.tabs(["📊 概要", "➕ イベント追加", "👀 データ確認"])
    
    with overview_tab:
        st.markdown("### 📈 データベース概要")
        
        # 簡単な統計情報を表示
        try:
            events = shared_db.get_all_events()
            st.metric("📅 登録済みイベント数", f"{len(events)}件")
            
            if events:
                st.markdown("#### 📋 最近のイベント")
                recent_events = events[:5]  # 最新5件
                for event in recent_events:
                    st.markdown(f"- **{event['event_name']}** ({event['category']}) - {event['created_at']}")
        except Exception as e:
            st.error(f"データ取得エラー: {str(e)}")
    
    with add_event_tab:
        st.markdown("### ➕ 新しいイベントデータを追加")
        
        with st.form("add_event_form"):
            event_name = st.text_input("📝 イベント名*", placeholder="例: AI技術セミナー2025")
            theme = st.text_area("🎯 テーマ・内容*", placeholder="例: 最新のAI技術動向と実践事例")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("📋 カテゴリ", 
                    ["conference", "seminar", "workshop", "webinar", "networking"],
                    format_func=lambda x: {"conference": "カンファレンス", "seminar": "セミナー", 
                                          "workshop": "ワークショップ", "webinar": "ウェビナー", 
                                          "networking": "ネットワーキング"}[x])
                target_attendees = st.number_input("🎯 目標参加者数", min_value=1, value=100)
                budget = st.number_input("💰 予算（円）", min_value=0, value=500000, step=50000)
            
            with col2:
                actual_attendees = st.number_input("✅ 実際の参加者数", min_value=0, value=0)
                actual_cost = st.number_input("💸 実際のコスト（円）", min_value=0, value=0, step=10000)
                event_date = st.date_input("📅 開催日", value=datetime.now().date())
            
            submitted = st.form_submit_button("💾 イベントデータを保存", type="primary")
            
            if submitted:
                if event_name and theme:
                    try:
                        event_data = {
                            'event_name': event_name,
                            'theme': theme,
                            'category': category,
                            'target_attendees': target_attendees,
                            'actual_attendees': actual_attendees,
                            'budget': budget,
                            'actual_cost': actual_cost,
                            'event_date': event_date,
                            'campaigns_used': [],
                            'performance_metrics': {}
                        }
                        
                        if shared_db.insert_event_data(event_data, "streamlit_user"):
                            st.success("✅ イベントデータを保存しました！")
                            st.balloons()
                        else:
                            st.error("❌ データ保存に失敗しました")
                    except Exception as e:
                        st.error(f"❌ 保存エラー: {str(e)}")
                else:
                    st.error("❌ イベント名とテーマは必須です")
    
    with view_data_tab:
        st.markdown("### 👀 登録済みデータ")
        
        try:
            events = shared_db.get_all_events()
            
            if events:
                # データフレームに変換して表示
                import pandas as pd
                df = pd.DataFrame(events)
                
                # 列名を日本語に変換
                column_mapping = {
                    'event_name': 'イベント名',
                    'category': 'カテゴリ',
                    'target_attendees': '目標参加者',
                    'actual_attendees': '実際参加者',
                    'budget': '予算',
                    'actual_cost': '実際コスト',
                    'event_date': '開催日',
                    'created_at': '登録日'
                }
                
                # 表示用に列を選択・リネーム
                display_columns = ['event_name', 'category', 'target_attendees', 'actual_attendees', 
                                 'budget', 'actual_cost', 'event_date', 'created_at']
                df_display = df[display_columns].rename(columns=column_mapping)
                
                st.dataframe(df_display, use_container_width=True)
                
                # 簡単な分析
                if len(events) > 1:
                    st.markdown("#### 📊 簡単な分析")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_conversion = (df['actual_attendees'] / df['target_attendees']).mean() * 100
                        st.metric("平均達成率", f"{avg_conversion:.1f}%")
                    
                    with col2:
                        total_budget = df['budget'].sum()
                        st.metric("総予算", f"¥{total_budget:,}")
                    
                    with col3:
                        total_participants = df['actual_attendees'].sum()
                        st.metric("総参加者数", f"{total_participants:,}人")
            else:
                st.info("📝 まだデータがありません。「イベント追加」タブからデータを追加してください。")
                
        except Exception as e:
            st.error(f"❌ データ表示エラー: {str(e)}")

def show_basic_data_management():
    """基本的なデータ管理画面（フォールバック）"""
    st.markdown("### 🔧 基本モード")
    st.info("💡 現在、基本的なデータ管理機能のみ利用可能です。")
    
    st.markdown("#### 📝 手動データ入力")
    
    with st.form("basic_data_form"):
        st.markdown("**イベント情報**")
        event_name = st.text_input("イベント名")
        event_description = st.text_area("イベント説明")
        
        col1, col2 = st.columns(2)
        with col1:
            target_num = st.number_input("目標参加者数", min_value=0, value=100)
        with col2:
            budget = st.number_input("予算（円）", min_value=0, value=500000)
        
        submitted = st.form_submit_button("💾 保存")
        
        if submitted:
            if event_name:
                st.success(f"✅ イベント「{event_name}」の情報を記録しました")
                st.info("💡 この情報は一時的なものです。完全な機能を利用するには、適切なデータベース接続が必要です。")
            else:
                st.error("❌ イベント名を入力してください")
    
    # データ品質チェック
    st.markdown("---")
    st.markdown("##### ✅ データ品質チェック")
    
    if st.button("🔬 データ品質を分析", use_container_width=True):
        with st.spinner("データ品質を分析中..."):
            try:
                # 簡易的な品質チェック
                conn = sqlite3.connect(cleaner.db_path)
                cursor = conn.cursor()
                
                issues = []
                
                # イベントデータの品質チェック
                cursor.execute("SELECT COUNT(*) FROM historical_events WHERE event_name IS NULL OR event_name = ''")
                empty_names = cursor.fetchone()[0]
                if empty_names > 0:
                    issues.append(f"イベント名未設定: {empty_names}件")
                
                cursor.execute("SELECT COUNT(*) FROM historical_events WHERE target_attendees <= 0")
                invalid_targets = cursor.fetchone()[0]
                if invalid_targets > 0:
                    issues.append(f"無効な目標参加者数: {invalid_targets}件")
                
                cursor.execute("SELECT COUNT(*) FROM historical_events WHERE actual_attendees > target_attendees * 3")
                unrealistic_results = cursor.fetchone()[0]
                if unrealistic_results > 0:
                    issues.append(f"非現実的な実績値: {unrealistic_results}件")
                
                conn.close()
                
                if issues:
                    st.warning("⚠️ データ品質の問題を検出しました:")
                    for issue in issues:
                        st.write(f"- {issue}")
                else:
                    st.success("✅ データ品質に問題は見つかりませんでした")
                
            except Exception as e:
                st.error(f"❌ 品質チェックエラー: {str(e)}")

def show_detailed_data_report(data_system):
    """詳細データレポートの表示"""
    st.markdown("### 📋 詳細データレポート")
    
    try:
        # データ概要の詳細表示をここに実装
        data_system.show_data_overview()
        st.success("✅ データレポートをコンソールに出力しました")
    except Exception as e:
        st.error(f"❌ レポート生成エラー: {str(e)}")

def show_welcome_screen():
    """ウェルカム画面の表示"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### 🎯 イベント集客施策提案AIへようこそ
        
        このツールは、イベントの詳細情報に基づいて最適な集客施策ポートフォリオを提案します。
        
        #### 📋 機能
        - **無料・有料施策の最適組み合わせ提案**
        - **予算配分の最適化**
        - **成果予測とリスク分析**
        - **実装タイムラインの提供**
        
        #### 🚀 使い方
        1. 左のサイドバーでイベント情報を入力
        2. ターゲットオーディエンスを設定
        3. 目標申込人数と予算を入力
        4. 「施策提案を生成」ボタンをクリック
        
        まずは左のサイドバーから情報を入力してください！
        """)

def generate_recommendations(event_name, event_category, event_theme, industries, 
                           job_titles, company_sizes, target_attendees, budget, 
                           event_date, is_free_event, event_format, use_ai_engine=False):
    """施策提案の生成"""
    
    # リクエストデータの準備
    request_data = {
        "event_name": event_name,
        "event_category": event_category,
        "event_theme": event_theme,
        "target_audience": {
            "job_titles": job_titles,
            "industries": industries,
            "company_sizes": company_sizes
        },
        "target_attendees": target_attendees,
        "budget": budget,
        "event_date": event_date.isoformat(),
        "is_free_event": is_free_event,
        "event_format": event_format,
        "priority_metrics": ["conversions", "cost_efficiency"]
    }
    
    with st.spinner("🤖 AIが最適な施策を分析中..."):
        try:
            if use_ai_engine:
                # 高度AI予測エンジンを使用
                response = use_ai_prediction_engine(request_data)
            else:
                # モックレスポンス（デモ用）
                response = create_mock_response(request_data)
            
            st.session_state.recommendations = response
            st.success("✅ 施策提案が生成されました！")
            st.rerun()
            
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

def use_ai_prediction_engine(request_data):
    """実際のAI予測エンジンを使用"""
    import asyncio
    
    try:
        from services.data_manager import DataManager
        from services.campaign_optimizer import CampaignOptimizer
        from services.prediction_engine import PredictionEngine
        from models.event_model import EventRequest, TargetAudience, EventCategory, EventFormat
    except ImportError as e:
        st.error(f"AI予測エンジンのモジュールが見つかりません: {str(e)}")
        return create_mock_response(request_data)
    
    try:
        # EventRequestオブジェクトの作成
        target_audience = TargetAudience(
            job_titles=request_data["target_audience"]["job_titles"],
            industries=request_data["target_audience"]["industries"],
            company_sizes=request_data["target_audience"]["company_sizes"]
        )
        
        event_request = EventRequest(
            event_name=request_data["event_name"],
            event_category=EventCategory(request_data["event_category"]),
            event_theme=request_data["event_theme"],
            target_audience=target_audience,
            target_attendees=request_data["target_attendees"],
            budget=request_data["budget"],
            event_date=datetime.fromisoformat(request_data["event_date"]),
            is_free_event=request_data["is_free_event"],
            event_format=EventFormat(request_data["event_format"])
        )
        
        # AI エンジンの初期化と実行
        async def run_ai_analysis():
            data_manager = DataManager()
            await data_manager.initialize()
            
            optimizer = CampaignOptimizer(data_manager)
            prediction_engine = PredictionEngine(data_manager)
            
            # 施策最適化
            campaigns = await optimizer.optimize_portfolio(event_request)
            
            # パフォーマンス予測
            performance = await prediction_engine.predict_performance(event_request, campaigns)
            
            return campaigns, performance
        
        campaigns, performance = asyncio.run(run_ai_analysis())
        
        # レスポンス形式に変換
        response = {
            "event_info": request_data,
            "recommended_campaigns": [
                {
                    "channel": campaign.channel.value,
                    "campaign_name": campaign.campaign_name,
                    "description": campaign.description,
                    "is_paid": campaign.is_paid,
                    "estimated_cost": campaign.estimated_cost,
                    "estimated_reach": campaign.estimated_reach,
                    "estimated_conversions": campaign.estimated_conversions,
                    "estimated_ctr": campaign.estimated_ctr,
                    "estimated_cvr": campaign.estimated_cvr,
                    "estimated_cpa": campaign.estimated_cpa,
                    "confidence_score": campaign.confidence_score,
                    "implementation_timeline": campaign.implementation_timeline,
                    "required_resources": campaign.required_resources
                }
                for campaign in campaigns
            ],
            "performance_predictions": {
                "total_reach": performance.total_reach,
                "total_conversions": performance.total_conversions,
                "total_cost": performance.total_cost,
                "overall_ctr": performance.overall_ctr,
                "overall_cvr": performance.overall_cvr,
                "overall_cpa": performance.overall_cpa,
                "goal_achievement_probability": performance.goal_achievement_probability,
                "risk_factors": performance.risk_factors,
                "optimization_suggestions": performance.optimization_suggestions
            },
            "total_estimated_cost": performance.total_cost,
            "total_estimated_reach": performance.total_reach,
            "total_estimated_conversions": performance.total_conversions,
            "budget_allocation": {
                "無料施策": sum(c.estimated_cost for c in campaigns if not c.is_paid) / performance.total_cost if performance.total_cost > 0 else 0,
                "有料施策": sum(c.estimated_cost for c in campaigns if c.is_paid) / performance.total_cost if performance.total_cost > 0 else 1
            }
        }
        
        st.info("🧠 高度AI予測エンジンによる分析結果を表示中...")
        return response
    
    except Exception as e:
        st.error(f"AI予測エンジンエラー: {str(e)}")
        st.info("💡 モックレスポンスに切り替えました")
        return create_mock_response(request_data)

def create_mock_response(request_data):
    """社内データ活用型施策提案システム（改善版）"""
    try:
        # 社内データシステムを初期化
        from internal_data_system import InternalDataSystem
        data_system = InternalDataSystem()
        
        # イベント条件の準備
        event_conditions = {
            "target_audience": request_data.get("target_audience", {}),
            "budget": request_data.get("budget", 0),
            "attendees": request_data.get("target_attendees", 0),
            "category": request_data.get("event_category", ""),
            "format": request_data.get("event_format", ""),
            "is_free": request_data.get("is_free_event", True)
        }
        
        # 社内知見の取得
        applicable_knowledge = data_system.get_applicable_knowledge(event_conditions)
        
        # 基本施策の生成（知見を活用）
        campaigns = generate_knowledge_enhanced_campaigns(request_data, applicable_knowledge)
        
        # 知見ベースのパフォーマンス予測
        performance = calculate_enhanced_performance(campaigns, applicable_knowledge)
        
        # 知見ベースの提案とリスク評価
        suggestions = generate_smart_suggestions(applicable_knowledge, request_data)
        risks = assess_smart_risks(applicable_knowledge, request_data, campaigns)
        
        # 総計の計算
        total_cost = sum(c['estimated_cost'] for c in campaigns)
        total_reach = sum(c['estimated_reach'] for c in campaigns)
        total_conversions = sum(c['estimated_conversions'] for c in campaigns)
        
        # 予算配分
        free_cost = sum(c['estimated_cost'] for c in campaigns if not c['is_paid'])
        paid_cost = sum(c['estimated_cost'] for c in campaigns if c['is_paid'])
        
        return {
            "event_info": request_data,
            "recommended_campaigns": campaigns,
            "performance_predictions": {
                "total_reach": total_reach,
                "total_conversions": total_conversions,
                "total_cost": total_cost,
                "overall_ctr": performance.get("ctr", 2.5),
                "overall_cvr": performance.get("cvr", 4.0),
                "overall_cpa": total_cost / total_conversions if total_conversions > 0 else 0,
                "goal_achievement_probability": performance.get("goal_probability", 0.75),
                "risk_factors": risks,
                "optimization_suggestions": suggestions
            },
            "total_estimated_cost": total_cost,
            "total_estimated_reach": total_reach,
            "total_estimated_conversions": total_conversions,
            "budget_allocation": {
                "無料施策": free_cost / total_cost if total_cost > 0 else 1.0,
                "有料施策": paid_cost / total_cost if total_cost > 0 else 0.0
            },
            "applied_knowledge_count": len(applicable_knowledge),
            "analysis_method": "knowledge_enhanced"
        }
        
    except Exception as e:
        # フォールバック: 基本的なモックレスポンス
        return create_basic_fallback_response(request_data)

def generate_knowledge_enhanced_campaigns(request_data, knowledge_list):
    """知見を活用した施策生成"""
    budget = request_data.get("budget", 0)
    target_attendees = request_data.get("target_attendees", 100)
    
    # 基本施策テンプレート
    base_campaigns = [
        {
            "channel": "email_marketing",
            "campaign_name": "メールマーケティング",
            "description": "既存リストへのメール配信",
            "is_paid": False,
            "base_cost": 0,
            "base_reach": 5000,
            "base_conversions": 50,
            "base_ctr": 2.0,
            "base_cvr": 5.0
        },
        {
            "channel": "social_media",
            "campaign_name": "SNS有機投稿",
            "description": "SNSでの有機投稿による集客",
            "is_paid": False,
            "base_cost": 0,
            "base_reach": 3000,
            "base_conversions": 25,
            "base_ctr": 1.5,
            "base_cvr": 3.0
        }
    ]
    
    # 予算がある場合は有料施策を追加
    if budget > 50000:
        base_campaigns.append({
            "channel": "paid_advertising",
            "campaign_name": "デジタル広告",
            "description": "Google/Meta広告による集客",
            "is_paid": True,
            "base_cost": min(budget * 0.6, 300000),
            "base_reach": 8000,
            "base_conversions": 40,
            "base_ctr": 3.0,
            "base_cvr": 2.5
        })
    
    # 知見を各施策に適用
    enhanced_campaigns = []
    for campaign in base_campaigns:
        enhanced = apply_knowledge_boost(campaign, knowledge_list)
        enhanced_campaigns.append(enhanced)
    
    return enhanced_campaigns

def apply_knowledge_boost(campaign, knowledge_list):
    """知見による施策強化"""
    boost_factor = 1.0
    confidence_boost = 0.6
    applied_knowledge = []
    
    # 関連する知見を探す
    channel_keywords = {
        'email_marketing': ['メール', 'email'],
        'social_media': ['sns', 'social', 'twitter'],
        'paid_advertising': ['広告', 'paid', 'ad']
    }
    
    keywords = channel_keywords.get(campaign['channel'], [])
    
    for knowledge in knowledge_list:
        content = knowledge.get('content', '').lower()
        if any(keyword in content for keyword in keywords):
            impact = knowledge.get('impact_score', 0.7)
            confidence = knowledge.get('confidence', 0.8)
            
            boost_factor *= (1 + impact * 0.15)  # 最大15%向上
            confidence_boost += confidence * 0.1
            applied_knowledge.append(knowledge.get('title', 'Unknown'))
    
    # 強化された施策を返す
    return {
        'channel': campaign['channel'],
        'campaign_name': campaign['campaign_name'],
        'description': campaign['description'] + (f" (知見{len(applied_knowledge)}件適用)" if applied_knowledge else ""),
        'is_paid': campaign['is_paid'],
        'estimated_cost': int(campaign['base_cost']),
        'estimated_reach': int(campaign['base_reach'] * boost_factor),
        'estimated_conversions': int(campaign['base_conversions'] * boost_factor),
        'estimated_ctr': campaign['base_ctr'] * boost_factor,
        'estimated_cvr': campaign['base_cvr'] * boost_factor,
        'estimated_cpa': campaign['base_cost'] / max(1, campaign['base_conversions'] * boost_factor),
        'confidence_score': min(0.95, confidence_boost),
        'implementation_timeline': "知見最適化済みタイミング",
        'required_resources': ["基本リソース", "知見適用"],
        'applied_knowledge': applied_knowledge
    }

def calculate_enhanced_performance(campaigns, knowledge_list):
    """知見強化されたパフォーマンス計算"""
    knowledge_boost = len(knowledge_list) * 0.05  # 知見1件につき5%向上
    
    return {
        "ctr": 2.5 * (1 + knowledge_boost),
        "cvr": 4.0 * (1 + knowledge_boost),
        "goal_probability": min(0.9, 0.7 + knowledge_boost)
    }

def generate_smart_suggestions(knowledge_list, request_data):
    """スマートな提案の生成"""
    suggestions = []
    
    if len(knowledge_list) > 0:
        suggestions.append(f"🧠 {len(knowledge_list)}件の社内知見が施策に適用されています")
    else:
        suggestions.append("💡 社内知見を蓄積することで、より精密な施策提案が可能になります")
    
    budget = request_data.get("budget", 0)
    if budget > 0:
        suggestions.append("💰 予算が設定されているため、有料施策との組み合わせが最適化されています")
    else:
        suggestions.append("💡 無料施策中心の構成です。少額でも予算設定すると選択肢が広がります")
    
    return suggestions

def assess_smart_risks(knowledge_list, request_data, campaigns):
    """スマートなリスク評価"""
    risks = []
    
    if len(knowledge_list) == 0:
        risks.append("📚 社内知見が不足しているため、汎用的な提案となっています")
    
    low_confidence_knowledge = [k for k in knowledge_list if k.get('confidence', 1.0) < 0.6]
    if low_confidence_knowledge:
        risks.append("⚠️ 信頼度の低い知見が含まれています")
    
    if not risks:
        risks.append("✅ 大きなリスク要因は検出されませんでした")
    
    return risks

def create_basic_fallback_response(request_data):
    """基本フォールバックレスポンス"""
    return {
        "event_info": request_data,
        "recommended_campaigns": [
            {
                "channel": "email_marketing",
                "campaign_name": "基本メール配信",
                "description": "既存リストへのメール配信",
                "is_paid": False,
                "estimated_cost": 0,
                "estimated_reach": 3000,
                "estimated_conversions": 30,
                "estimated_ctr": 2.0,
                "estimated_cvr": 4.0,
                "estimated_cpa": 0,
                "confidence_score": 0.6,
                "implementation_timeline": "2週間前開始",
                "required_resources": ["メール配信ツール"]
            }
        ],
        "performance_predictions": {
            "total_reach": 3000,
            "total_conversions": 30,
            "total_cost": 0,
            "overall_ctr": 2.0,
            "overall_cvr": 4.0,
            "overall_cpa": 0,
            "goal_achievement_probability": 0.6,
            "risk_factors": ["基本的な提案のみです"],
            "optimization_suggestions": ["社内データを蓄積してください"]
        },
        "total_estimated_cost": 0,
        "total_estimated_reach": 3000,
        "total_estimated_conversions": 30,
        "budget_allocation": {"無料施策": 1.0, "有料施策": 0.0}
    }

def show_recommendations():
    """施策提案の表示"""
    try:
        data = st.session_state.recommendations
        
        # サマリー表示
        st.markdown('<h2 class="sub-header">📊 予測サマリー</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            target_percentage = ""
            try:
                target_attendees = data['event_info'].get('target_attendees', 0)
                total_conversions = data.get('total_estimated_conversions', 0)
                
                if target_attendees and target_attendees > 0 and total_conversions >= 0:
                    percentage = (total_conversions / target_attendees) * 100
                    target_percentage = f"目標の{percentage:.1f}%"
                elif target_attendees == 0:
                    target_percentage = "目標未設定"
                else:
                    target_percentage = "目標情報なし"
            except (ZeroDivisionError, TypeError, KeyError):
                target_percentage = "計算エラー"
            
            st.metric(
                "予測申込人数",
                f"{data['total_estimated_conversions']}人",
                target_percentage
            )
        
        with col2:
            st.metric(
                "総リーチ数",
                f"{data['total_estimated_reach']:,}人"
            )
        
        with col3:
            budget_percentage = ""
            try:
                budget = data['event_info'].get('budget', 0)
                total_cost = data.get('total_estimated_cost', 0)
                
                if budget and budget > 0 and total_cost >= 0:
                    percentage = (total_cost / budget) * 100
                    budget_percentage = f"予算の{percentage:.1f}%"
                elif budget == 0:
                    budget_percentage = "予算未設定"
                else:
                    budget_percentage = "予算情報なし"
            except (ZeroDivisionError, TypeError, KeyError):
                budget_percentage = "計算エラー"
            
            st.metric(
                "推定コスト",
                f"¥{data['total_estimated_cost']:,}",
                budget_percentage
            )
        
        with col4:
            st.metric(
                "目標達成確率",
                f"{data['performance_predictions']['goal_achievement_probability']*100:.1f}%"
            )
        
        # 施策一覧
        st.markdown('<h2 class="sub-header">🎯 推奨施策</h2>', unsafe_allow_html=True)
        
        for i, campaign in enumerate(data['recommended_campaigns']):
            card_class = "free-campaign" if not campaign['is_paid'] else "paid-campaign"
            
            with st.container():
                st.markdown(f'<div class="campaign-card {card_class}">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"### {campaign['campaign_name']}")
                    st.markdown(f"**チャネル:** {campaign['channel']}")
                    st.markdown(f"**説明:** {campaign['description']}")
                    st.markdown(f"**実施タイムライン:** {campaign['implementation_timeline']}")
                    
                    # 必要リソース
                    resources_text = " | ".join(campaign['required_resources'])
                    st.markdown(f"**必要リソース:** {resources_text}")
                
                with col2:
                    # メトリクス表示
                    st.markdown("**予測パフォーマンス**")
                    st.markdown(f"コスト: ¥{campaign['estimated_cost']:,}")
                    st.markdown(f"リーチ: {campaign['estimated_reach']:,}人")
                    st.markdown(f"申込: {campaign['estimated_conversions']}人")
                    st.markdown(f"CTR: {campaign['estimated_ctr']:.1f}%")
                    st.markdown(f"CVR: {campaign['estimated_cvr']:.1f}%")
                    if campaign['estimated_cpa'] > 0:
                        st.markdown(f"CPA: ¥{campaign['estimated_cpa']:,}")
                    else:
                        st.markdown("CPA: 無料")
                    
                    # 信頼度スコア
                    confidence_color = "green" if campaign['confidence_score'] > 0.7 else "orange" if campaign['confidence_score'] > 0.5 else "red"
                    st.markdown(f"**信頼度:** <span style='color:{confidence_color}'>{campaign['confidence_score']*100:.0f}%</span>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # パフォーマンス分析
        show_performance_analysis(data)
        
        # リスクと提案
        show_risks_and_suggestions(data)
        
    except Exception as e:
        st.error(f"❌ 施策提案表示エラー: {str(e)}")
        st.error("申し訳ございません。システムエラーが発生しました。ページを再読み込みしてもう一度お試しください。")

def show_performance_analysis(data):
    """パフォーマンス分析の表示"""
    st.markdown('<h2 class="sub-header">📈 パフォーマンス分析</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 施策別コンバージョン数
        campaigns_df = pd.DataFrame(data['recommended_campaigns'])
        fig_conv = px.bar(
            campaigns_df,
            x='campaign_name',
            y='estimated_conversions',
            color='is_paid',
            title='施策別予測申込数',
            color_discrete_map={True: '#ffc107', False: '#28a745'}
        )
        fig_conv.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_conv, use_container_width=True)
    
    with col2:
        # 予算配分
        budget_data = []
        for campaign in data['recommended_campaigns']:
            budget_data.append({
                'campaign': campaign['campaign_name'],
                'cost': campaign['estimated_cost'],
                'type': '有料' if campaign['is_paid'] else '無料'
            })
        
        budget_df = pd.DataFrame(budget_data)
        fig_budget = px.pie(
            budget_df[budget_df['cost'] > 0],
            values='cost',
            names='campaign',
            title='予算配分'
        )
        st.plotly_chart(fig_budget, use_container_width=True)

def show_risks_and_suggestions(data):
    """リスクと提案の表示"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3 class="sub-header">⚠️ リスク要因</h3>', unsafe_allow_html=True)
        
        if data['performance_predictions']['risk_factors']:
            for risk in data['performance_predictions']['risk_factors']:
                st.warning(f"⚠️ {risk}")
        else:
            st.success("✅ 特に大きなリスク要因は検出されませんでした")
    
    with col2:
        st.markdown('<h3 class="sub-header">💡 最適化提案</h3>', unsafe_allow_html=True)
        
        for suggestion in data['performance_predictions']['optimization_suggestions']:
            st.info(f"💡 {suggestion}")
    
    # データエクスポート
    st.markdown('<h2 class="sub-header">📥 データエクスポート</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV エクスポート
        campaigns_df = pd.DataFrame(data['recommended_campaigns'])
        csv = campaigns_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📊 施策データをCSVでダウンロード",
            data=csv,
            file_name=f"event_campaigns_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON エクスポート
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📋 全データをJSONでダウンロード",
            data=json_data,
            file_name=f"event_analysis_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

def process_text_knowledge(content, data_system):
    """テキストファイルから知見を抽出"""
    try:
        # Claude APIを使用した分析
        if hasattr(data_system, 'claude_client') and data_system.claude_client:
            result = data_system._analyze_document_with_claude(content, "テキストファイル", "Text")
        else:
            # フォールバック: 簡易的な知見抽出
            result = data_system._analyze_text_fallback(content, "テキストファイル", "Text")
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_paid_media_csv_import(uploaded_file, data_system):
    """有償メディアCSVインポート処理"""
    with st.spinner("💰 有償メディアCSVデータを処理中..."):
        try:
            import tempfile
            import os
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # インポート実行
            result = data_system.import_existing_csv(tmp_file_path, "paid_media")
            
            # 結果表示
            if result["success"]:
                st.success(f"✅ {result['imported']}件の有償メディアデータをインポートしました！")
            else:
                st.error(f"❌ インポートに失敗しました: {result['error']}")
            
            # 一時ファイル削除
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ インポートエラー: {str(e)}")

def process_web_ad_csv_import(uploaded_file, data_system):
    """WEB広告CSVインポート処理"""
    with st.spinner("🌐 WEB広告CSVデータを処理中..."):
        try:
            import tempfile
            import os
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # インポート実行
            result = data_system.import_existing_csv(tmp_file_path, "web_advertising")
            
            # 結果表示
            if result["success"]:
                st.success(f"✅ {result['imported']}件のWEB広告データをインポートしました！")
            else:
                st.error(f"❌ インポートに失敗しました: {result['error']}")
            
            # 一時ファイル削除
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ インポートエラー: {str(e)}")

def process_free_campaign_csv_import(uploaded_file, data_system):
    """無償施策CSVインポート処理"""
    with st.spinner("🆓 無償施策CSVデータを処理中..."):
        try:
            import tempfile
            import os
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # インポート実行
            result = data_system.import_existing_csv(tmp_file_path, "free_campaigns")
            
            # 結果表示
            if result["success"]:
                st.success(f"✅ {result['imported']}件の無償施策データをインポートしました！")
            else:
                st.error(f"❌ インポートに失敗しました: {result['error']}")
            
            # 一時ファイル削除
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ インポートエラー: {str(e)}")

def process_conference_import(csv_file_path, event_info, data_system):
    """カンファレンス実績インポート処理（手入力＋CSV）"""
    try:
        import pandas as pd
        
        # CSV読み込み
        try:
            df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_file_path, encoding='shift-jis')
        
        errors = []
        applicant_count = 0
        
        # データベース接続
        import sqlite3
        conn = sqlite3.connect(data_system.db_path)
        cursor = conn.cursor()
        
        # participantsテーブルの作成（存在しない場合）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                job_title TEXT,
                position TEXT,
                company TEXT,
                industry TEXT,
                company_size TEXT,
                source_type TEXT,
                source_name TEXT,
                apply_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # イベント基本情報を保存
        try:
            actual_attendees = len(df)  # 実際申込数はCSVの行数
            target_attendees = event_info["target_attendees"]
            budget = event_info["budget"]
            actual_cost = 0  # 実際コストは未入力
            
            # パフォーマンス計算
            conversion_rate = (actual_attendees / target_attendees * 100) if target_attendees > 0 else 0
            cpa = (actual_cost / actual_attendees) if actual_attendees > 0 else 0
            cost_efficiency = budget / actual_cost if actual_cost > 0 else 1
            
            # パフォーマンスメトリクスをJSON形式で作成
            import json
            performance_metrics = json.dumps({
                "conversion_rate": conversion_rate,
                "cpa": cpa,
                "cost_efficiency": cost_efficiency
            })
            
            # 使用施策をJSON形式で作成
            campaigns_used = json.dumps(["conference"])
            
            cursor.execute("""
                INSERT INTO historical_events 
                (event_name, category, theme, target_attendees, actual_attendees, budget, actual_cost, event_date, campaigns_used, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_info["event_name"],
                event_info["category"],
                event_info["theme"],
                target_attendees,
                actual_attendees,
                budget,
                actual_cost,
                event_info["event_date"],
                campaigns_used,
                performance_metrics
            ))
            event_id = cursor.lastrowid
        except Exception as e:
            errors.append(f"イベント基本情報保存エラー: {str(e)}")
            return {"success": False, "error": f"イベント基本情報保存エラー: {str(e)}"}
        
        # 申込者データ処理
        for index, row in df.iterrows():
            try:
                # 列マッピング（日本語・英語対応）
                job_title = get_column_value(row, ['職種', 'Job Title', 'job_title'])
                position = get_column_value(row, ['役職', 'Position', 'position'])
                company = get_column_value(row, ['企業名', 'Company', 'company'])
                industry = get_column_value(row, ['業種', 'Industry', 'industry'])
                company_size = get_column_value(row, ['従業員規模', 'Company Size', 'company_size'])
                
                # 必須項目チェック
                if not job_title or not position or not company or not industry or not company_size:
                    errors.append(f"行{index+1}: 必須項目が不足しています")
                    continue
                
                # 申込者情報をparticipantsテーブルに保存（仮のテーブル構造）
                cursor.execute("""
                    INSERT OR IGNORE INTO participants 
                    (event_id, job_title, position, company, industry, company_size, source_type, source_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    job_title,
                    position,
                    company,
                    industry,
                    company_size,
                    "conference",
                    event_info["event_name"]
                ))
                
                applicant_count += 1
                
            except Exception as e:
                errors.append(f"行{index+1}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "applicant_count": applicant_count,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_paid_media_import(csv_file_path, media_info, data_system):
    """有償メディア実績インポート処理（手入力＋CSV）"""
    try:
        import pandas as pd
        
        # CSV読み込み
        try:
            df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_file_path, encoding='shift-jis')
        
        errors = []
        applicant_count = 0
        
        # データベース接続
        import sqlite3
        conn = sqlite3.connect(data_system.db_path)
        cursor = conn.cursor()
        
        # participantsテーブルの作成（存在しない場合）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                job_title TEXT,
                position TEXT,
                company TEXT,
                industry TEXT,
                company_size TEXT,
                source_type TEXT,
                source_name TEXT,
                apply_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # media_basic_infoテーブルに必要な列を追加（存在しない場合）
        try:
            cursor.execute("ALTER TABLE media_basic_info ADD COLUMN cost INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # 列が既に存在する場合
        
        try:
            cursor.execute("ALTER TABLE media_basic_info ADD COLUMN event_name TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE media_basic_info ADD COLUMN event_theme TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE media_basic_info ADD COLUMN event_category TEXT")
        except sqlite3.OperationalError:
            pass
        
        # 有償メディア情報を保存
        try:
            cursor.execute("""
                INSERT INTO media_basic_info 
                (media_name, media_type, target_audience, cost, description, event_name, event_theme, event_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                media_info["media_name"],
                "paid_media",
                media_info["event_target"],
                media_info["media_cost"],
                f"有償メディア経由: {media_info['event_name']}",
                media_info["event_name"],
                media_info["event_theme"],
                media_info["event_category"]
            ))
            media_id = cursor.lastrowid
        except Exception as e:
            errors.append(f"メディア基本情報保存エラー: {str(e)}")
            return {"success": False, "error": f"メディア基本情報保存エラー: {str(e)}"}
        
        # 申込者データ処理
        for index, row in df.iterrows():
            try:
                # 列マッピング（日本語・英語対応）
                job_title = get_column_value(row, ['職種', 'Job Title', 'job_title'])
                position = get_column_value(row, ['役職', 'Position', 'position'])
                company = get_column_value(row, ['企業名', 'Company', 'company'])
                industry = get_column_value(row, ['業種', 'Industry', 'industry'])
                company_size = get_column_value(row, ['従業員規模', 'Company Size', 'company_size'])
                source = get_column_value(row, ['申込経路', 'Source', 'source'], default=media_info["media_name"])
                apply_date = get_column_value(row, ['申込日', 'Apply Date', 'apply_date'], default=media_info["media_date"])
                
                # 必須項目チェック
                if not job_title or not position or not company or not industry or not company_size:
                    errors.append(f"行{index+1}: 必須項目が不足しています")
                    continue
                
                # 申込者情報をparticipantsテーブルに保存
                cursor.execute("""
                    INSERT OR IGNORE INTO participants 
                    (event_id, job_title, position, company, industry, company_size, source_type, source_name, apply_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    media_id,  # メディアIDを仮にevent_idとして使用
                    job_title,
                    position,
                    company,
                    industry,
                    company_size,
                    "paid_media",
                    source,
                    apply_date
                ))
                
                applicant_count += 1
                
            except Exception as e:
                errors.append(f"行{index+1}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "applicant_count": applicant_count,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_column_value(row, column_names, default=None):
    """複数の列名候補から値を取得"""
    import pandas as pd
    for col_name in column_names:
        if col_name in row and pd.notna(row[col_name]):
            return str(row[col_name]).strip()
    return default

if __name__ == "__main__":
    main() 