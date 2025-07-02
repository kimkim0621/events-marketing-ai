# イベント集客マーケティングAI

イベントの詳細情報に基づいて最適な集客施策ポートフォリオを提案するAIシステムです。

## 🚀 機能

### 📥 データ管理
- **🏆 カンファレンス実績**: 手入力（基本情報）+ CSV（申込者データ）
- **💰 有償メディア**: 手入力（メディア情報）+ CSV（申込者データ）
- **🌐 WEB広告**: キャンペーン情報とパフォーマンス管理
- **🆓 無償施策**: SNS・コンテンツマーケティング実績
- **🧠 知見・ノウハウ**: Markdown/Word/PDF対応の知見管理

### 🎯 施策提案
- 社内データ活用型システム
- 知見ベースの施策強化
- パフォーマンス予測
- リスク評価・最適化提案

### 📊 分析機能
- パフォーマンス分析・可視化
- 予算配分最適化
- CSV/JSONエクスポート

## 🔧 技術スタック

- **Frontend**: Streamlit
- **Backend**: FastAPI (optional)
- **Database**: SQLite
- **AI/ML**: Claude API, pandas, scikit-learn
- **Visualization**: Plotly, matplotlib, seaborn
- **Document Processing**: PyPDF2, python-docx, python-pptx

## 📦 インストール

```bash
pip install -r requirements.txt
```

## 🚀 起動方法

```bash
streamlit run streamlit_app.py
```

## 🌐 デプロイ

### 🚀 Supabase + Streamlit Cloud（推奨）

#### ステップ1: Supabaseデータベース準備
1. [Supabase](https://supabase.com)でアカウント作成
2. 新しいプロジェクト作成（Tokyoリージョン推奨）
3. Settings > Database で接続情報を取得
4. `.streamlit/secrets.toml.example`を参考に設定

#### ステップ2: GitHubリポジトリ作成
```bash
git remote add origin https://github.com/YOUR_USERNAME/events-marketing-ai.git
git branch -M main
git push -u origin main
```

#### ステップ3: Streamlit Cloudデプロイ
1. [Streamlit Cloud](https://streamlit.io/cloud)でGitHubアカウントでログイン
2. 「New app」をクリック
3. リポジトリ選択: `YOUR_USERNAME/events-marketing-ai`
4. Main file path: `streamlit_app.py`
5. 「Advanced settings」で環境変数設定:
   ```
   [database]
   connection_string = "postgresql://postgres.YOUR_PROJECT_ID:YOUR_PASSWORD@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
   ```
6. 「Deploy!」をクリック

#### ✅ デプロイ完了
- チーム共有用URL: `https://YOUR_APP_NAME.streamlit.app/`
- 自動SSL証明書とHTTPS対応
- Supabaseで複数メンバー同時利用可能

### 🆓 代替案: Google Sheets + Streamlit Cloud
簡単なデータ共有にはGoogle Sheetsオプションも利用可能  
詳細: `QUICK_GOOGLE_SHEETS_SETUP.md`

### 🔒 セキュリティ設定
- `secrets.toml`は`.gitignore`で除外済み
- Streamlit Cloud側でのみ機密情報を設定
- Supabase Row Level Security (RLS)有効化推奨

### 環境変数（オプション）
- `ANTHROPIC_API_KEY`: Claude API使用時に設定
- `database.connection_string`: Supabase接続文字列

## 📁 プロジェクト構造

```
events-marketing-ai/
├── streamlit_app.py              # メインアプリケーション
├── internal_data_system.py       # データ管理システム
├── requirements.txt              # Python依存関係
├── data/                         # データファイル
├── .streamlit/
│   └── config.toml              # Streamlit設定
└── README.md                    # このファイル
```

## 📚 使用方法

1. **データインポート**: 各タブでデータをインポート
2. **施策提案**: メイン画面でイベント情報を入力
3. **結果確認**: 推奨施策とパフォーマンス予測を確認
4. **データエクスポート**: CSV/JSON形式でデータ出力

## 🤝 貢献

プルリクエストやイシューでの貢献を歓迎します。

## 📄 ライセンス

This project is licensed under the MIT License.

## 📖 概要

イベントのテーマ、ターゲット、目標人数、集客予算をもとに、無償・有償施策の最適なポートフォリオを提案するAIシステムです。過去のイベントデータとメディアパフォーマンスデータを活用して、データドリブンな集客戦略を自動生成します。

## ✨ 主な機能

### 🎯 施策提案エンジン
- **無料施策**: メール配信、SNS投稿、SEO対策など
- **有料施策**: 各種メディア広告、リスティング広告など
- **予算配分最適化**: 限られた予算での最大効果を狙った組み合わせ

### 📊 パフォーマンス予測
- **成果予測**: リーチ数、コンバージョン数、CTR、CVR、CPA
- **目標達成確率**: 過去データに基づく目標達成の可能性
- **リスク分析**: 想定されるリスク要因の特定

### 💡 最適化提案
- **改善提案**: パフォーマンス向上のための具体的なアドバイス
- **代替シナリオ**: 異なる予算・目標での施策組み合わせ

### 📋 データ管理・テンプレートシステム
- **構造化テンプレート**: イベント実績・メディア属性・知見データ用CSV
- **LLM技術統合**: 柔軟なPDF解析と自動データ抽出
- **データインポートガイド**: 段階的品質向上のための完全ガイド
- **社内知見管理**: ノウハウの蓄積・検索・活用
- **データクリーニング**: 重複削除・品質チェック・バックアップ機能

### 🌐 ターミナル独立実行
- **nohupスクリプト**: ターミナル終了後も継続動作
- **macOS自動起動**: システム再起動時の自動起動設定
- **ネットワーク共有**: チーム全員でのアクセス可能
- **プロセス管理**: 安全な起動・停止・ログ管理

## 🚀 セットアップ

### 必要な環境
- Python 3.8以上
- pip

### インストール

1. リポジトリのクローン
```bash
git clone <repository-url>
cd events-marketing-ai
```

2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

3. データベースの初期化
初回起動時に自動的にSQLiteデータベースが作成され、サンプルデータが投入されます。

## 💻 使用方法

### 1. Streamlit Webアプリケーション（推奨）

```bash
streamlit run streamlit_app.py
```

ブラウザで `http://localhost:8501` にアクセスして、直感的なWebインターフェースを使用できます。

#### 使い方
1. 左サイドバーでイベント情報を入力
2. ターゲットオーディエンスを設定
3. 目標参加者数と予算を入力
4. 「施策提案を生成」ボタンをクリック
5. 提案された施策を確認・分析

### 2. FastAPI サーバー

```bash
python main.py
```

APIサーバーが `http://localhost:8000` で起動します。

#### API エンドポイント

- `POST /api/campaigns/suggest`: 施策提案の生成
- `GET /api/historical-data/events`: 過去のイベントデータ取得
- `GET /api/media-data/performance`: メディアパフォーマンスデータ取得
- `POST /api/data/upload-event`: 新しいイベントデータの追加
- `POST /api/data/upload-media`: 新しいメディアデータの追加

#### APIドキュメント
`http://localhost:8000/docs` でSwagger UIによるAPIドキュメントを確認できます。

## 📊 データ構造

### イベントリクエスト例
```json
{
  "event_name": "AI技術セミナー",
  "event_category": "seminar",
  "event_theme": "最新のAI技術動向と実践事例",
  "target_audience": {
    "job_titles": ["エンジニア", "マネージャー"],
    "industries": ["IT", "製造業"],
    "company_sizes": ["中小企業", "大企業"]
  },
  "target_attendees": 100,
  "budget": 500000,
  "event_date": "2025-03-01T00:00:00",
  "is_free_event": true,
  "event_format": "online"
}
```

### レスポンス例
```json
{
  "recommended_campaigns": [
    {
      "campaign_name": "既存リスト向けメール配信",
      "channel": "email_marketing",
      "is_paid": false,
      "estimated_cost": 0,
      "estimated_reach": 5000,
      "estimated_conversions": 50,
      "estimated_ctr": 2.0,
      "estimated_cvr": 5.0,
      "confidence_score": 0.8
    }
  ],
  "performance_predictions": {
    "total_reach": 10000,
    "total_conversions": 85,
    "goal_achievement_probability": 0.75
  }
}
```

## 🗃️ データ管理

### 📊 推奨テンプレート（新機能）
LLM技術と構造化データの最適な組み合わせを実現する専用テンプレートを提供：

#### **CSVテンプレート**
- **`templates/event_data_template.csv`**: イベント実績データ（13項目）
- **`templates/media_data_template.csv`**: メディア属性データ（CTR、CVR、読者層等）
- **`templates/insights_template.csv`**: 知見・ノウハウ構造化データ

#### **PDFフォーマットガイド**  
- **`templates/pdf_format_guide.md`**: LLM認識最適化PDF構造
- **`DATA_IMPORT_GUIDE.md`**: 包括的なデータインポート完全ガイド

#### **推奨データ項目**
| データ種別 | 必須項目 | 推奨項目 | 自動マッピング率 |
|------------|----------|----------|------------------|
| **イベント実績** | イベント名、開催日、目標・実績申込数 | カテゴリ、予算、ターゲット | 95%以上 |
| **メディア属性** | メディア名、主要読者層 | リーチ数、CTR、CPA | 90%以上 |
| **知見・ノウハウ** | 知見内容、カテゴリ | 影響度、信頼度 | 85%以上 |

### サンプルデータ
システム初回起動時に、サンプルデータが自動投入されます：

- **過去のイベントデータ**: AI Engineering Summit、DX推進セミナー等
- **メディアパフォーマンス**: TechCrunch Japan、ITmedia、日経xTECH等

### 新しいデータの追加
1. **CSVテンプレート**: 📊データ管理タブから推奨テンプレートをダウンロード
2. **PDFインポート**: LLM技術による自動解析・構造化
3. **Webインターフェース**: 管理画面から手動入力
4. **API**: `/api/data/upload-event` および `/api/data/upload-media` エンドポイント

## 🔧 カスタマイズ

### 新しいメディアの追加
`services/data_manager.py` の `load_sample_data` メソッドを編集して、新しいメディアデータを追加できます。

### 施策アルゴリズムの調整
`services/campaign_optimizer.py` で施策生成ロジックをカスタマイズできます：

- 予算配分アルゴリズム
- チャネル優先度
- パフォーマンス予測モデル

### 予測モデルの改善
`services/prediction_engine.py` で予測精度を向上させることができます：

- 機械学習モデルの導入
- 重複調整ロジックの改善
- リスク分析の強化

## 📈 パフォーマンス指標

システムが提供する主要な指標：

- **CTR (Click Through Rate)**: クリック率
- **CVR (Conversion Rate)**: コンバージョン率  
- **CPA (Cost Per Acquisition)**: 獲得単価
- **リーチ数**: 想定接触人数
- **コンバージョン数**: 予測参加者数

## 🔒 セキュリティ

- SQLiteデータベースを使用（本番環境ではPostgreSQL等を推奨）
- CORS設定によるクロスオリジンアクセス制御
- 入力バリデーションによるデータ整合性確保

## 🤝 コントリビューション

### 開発ルール
このプロジェクトでは、品質と一貫性を保つために専用のCursor Rulesを適用しています：
- **ルールファイル**: `.cursor-rules`
- **重要事項**: 日付の正確性、技術文書の品質基準、エラー防止プロトコル

### コントリビューション手順
1. Forkしてブランチを作成
2. `.cursor-rules` を確認し、開発基準に従う
3. 機能追加・バグ修正を実装
4. テストを追加
5. 文書更新（日付確認必須）
6. Pull Requestを作成

## 📞 サポート

質問やサポートが必要な場合は、Issues を作成してください。

---

**開発チーム**: イベント集客AI開発チーム  
**最終更新**: 2025年6月21日 