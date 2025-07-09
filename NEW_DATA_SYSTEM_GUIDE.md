# 新しいデータシステム使用ガイド

## 📊 概要

新しいデータ仕様に対応したマーケティング施策提案AIシステムです。4つの主要なデータタイプを管理し、実績データに基づいた施策提案を行います。

## 🗃️ データベース構造

### 1. カンファレンス集客施策実績データ (`conference_campaign_results`)

実際のカンファレンス集客施策の実績データを格納します。

**主要フィールド:**
- `campaign_name`: 施策名（例: FCメルマガ、Meta広告）
- `conference_name`: カンファレンス名
- `theme_category`: テーマ・カテゴリ
- `format`: 形式（ハイブリッド、オンライン、オフライン）
- `target_industry`: ターゲット業種
- `target_job_title`: ターゲット職種
- `target_company_size`: ターゲット企業規模
- `distribution_count`: 配信数/PV
- `click_count`: クリック数
- `conversion_count`: 申込(CV数)
- `cost_excluding_tax`: 費用（税抜）
- `cpa`: CPA（Cost Per Acquisition）

### 2. カンファレンス申込者ユーザーデータ (`conference_participants`)

カンファレンス申込者の属性データを格納します。

**主要フィールド:**
- `conference_name`: 関連カンファレンス名
- `job_title`: 職種
- `position`: 役職
- `industry`: 業種
- `company_name`: 企業名
- `company_size`: 企業規模
- `registration_source`: 申込経路
- `registration_date`: 申込日

### 3. 有償メディアデータ (`paid_media_data`)

有償メディアの基本情報と料金データを格納します。

**主要フィールド:**
- `media_name`: メディア名
- `reachable_count`: リーチ可能数
- `target_industry`: ターゲット業界
- `target_job_title`: ターゲット職種
- `target_company_size`: ターゲット企業規模
- `cost_excluding_tax`: 費用（税抜）
- `media_type`: メディアタイプ
- `description`: 説明
- `contact_info`: 連絡先情報

### 4. 知見データ (`knowledge_database`)

マーケティング施策に関する知見・ノウハウを格納します。

**主要フィールド:**
- `title`: タイトル
- `content`: 内容
- `knowledge_type`: 知見タイプ（general, campaign, media, audience, timing）
- `impact_degree`: 影響度（0.0-5.0）
- `impact_scope`: 影響範囲
- `impact_frequency`: 影響頻度
- `applicable_conditions`: 適用条件
- `tags`: タグ
- `source`: 情報源
- `confidence_score`: 信頼度（0.0-1.0）

## 🚀 使用方法

### 1. データインポート

#### A. カンファレンス集客施策実績データのインポート

```bash
# CSVファイルを直接インポート
python import_csv_data.py
```

または、Streamlitアプリの「データインポート」タブからCSVファイルをアップロード。

**必要な列:**
- 施策名
- カンファレンス名
- テーマ・カテゴリ
- 形式
- ターゲット(業種)
- ターゲット(職種)
- ターゲット(従業員規模)
- 配信数/PV
- クリック数
- 申込(CV数)
- 費用(税抜)
- CPA

#### B. 申込者ユーザーデータのインポート

Streamlitアプリの「申込者ユーザーデータ」タブからCSVファイルをアップロード。

**必要な列:**
- 職種
- 役職
- 業種
- 企業名
- 従業員規模

#### C. 有償メディアデータの追加

Streamlitアプリの「有償メディアデータ」タブから手動入力またはCSVインポート。

#### D. 知見データの追加

Streamlitアプリの「知見データ」タブから手動入力。

### 2. アプリケーションの起動

```bash
# データインポート専用アプリ
streamlit run data_import_ui.py

# メインアプリケーション
streamlit run updated_streamlit_app.py --server.port 8502
```

### 3. 施策提案の生成

1. メインアプリケーションの「施策提案」メニューを選択
2. イベント情報を入力：
   - イベント名
   - イベントカテゴリ
   - 目標参加者数
   - 予算
3. ターゲット設定：
   - 業界
   - 職種
   - 企業規模
4. 「施策提案を生成」ボタンをクリック

### 4. データ分析

1. 「データ分析」メニューを選択
2. 以下の分析結果を確認：
   - キャンペーンパフォーマンス
   - 施策別効果
   - カンファレンス別実績
   - コンバージョン分析

## 📈 機能詳細

### AI施策提案エンジン

実績データに基づいて最適な施策を提案します：

1. **類似事例分析**: 過去の同様のターゲット・予算での成功事例を分析
2. **パフォーマンス予測**: 実績データから期待コンバージョン・CPA・費用を予測
3. **予算最適化**: 予算に応じた施策の組み合わせを提案
4. **リスク評価**: 知見データに基づくリスク評価

### データ分析機能

- **キャンペーン効果分析**: 施策別・カンファレンス別のパフォーマンス分析
- **ターゲット分析**: 参加者属性の分析
- **コスト分析**: CPA・ROIの分析
- **トレンド分析**: 時系列での効果変化の分析

### 知見管理システム

- **知見の体系化**: タイプ別・影響度別の知見管理
- **適用条件管理**: 知見の適用条件の明確化
- **信頼度管理**: 知見の信頼度スコア管理
- **施策への反映**: 知見を施策提案に自動反映

## 🔧 技術仕様

### 使用技術

- **フロントエンド**: Streamlit
- **データベース**: SQLite
- **データ処理**: pandas, numpy
- **可視化**: Plotly
- **言語**: Python 3.8+

### ファイル構成

```
events-marketing-ai/
├── data_import_ui.py          # データインポートUI
├── updated_streamlit_app.py   # メインアプリケーション
├── import_csv_data.py         # CSVインポートスクリプト
├── data/
│   └── events_marketing.db    # SQLiteデータベース
└── NEW_DATA_SYSTEM_GUIDE.md   # このガイド
```

## 📊 実績データ例

現在インポート済みのデータ：
- **カンファレンス集客施策実績**: 56件
- **主要カンファレンス**:
  - 開発生産性Conference 2023/2024/2025
  - 内製開発Summit 2025
  - AI Engineering Summit

## 🎯 今後の拡張予定

1. **機械学習モデル**: より高精度な予測モデルの導入
2. **リアルタイム分析**: リアルタイムでのパフォーマンス監視
3. **A/Bテスト機能**: 施策の効果測定機能
4. **レポート自動生成**: 定期レポートの自動生成
5. **外部API連携**: 広告プラットフォームとの連携

## 📞 サポート

システムに関する質問や問題がある場合は、プロジェクトチームまでお問い合わせください。

---

**最終更新**: 2025年7月9日
**バージョン**: 1.0.0 