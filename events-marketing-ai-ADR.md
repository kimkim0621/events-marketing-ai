# Architecture Decision Record (ADR)
# イベント集客施策提案AIシステム

**文書作成日**: 2025年6月21日  
**バージョン**: 1.0  
**ステータス**: 承認済み

## 📋 目次

1. [概要](#概要)
2. [技術選定の判断基準](#技術選定の判断基準)
3. [データベース選定](#データベース選定)
4. [機械学習・AI技術スタック](#機械学習ai技術スタック)
5. [インフラ・デプロイメント](#インフラデプロイメント)
6. [API・インテグレーション](#apiインテグレーション)
7. [監視・ログ・セキュリティ](#監視ログセキュリティ)
8. [フロントエンド技術](#フロントエンド技術)
9. [推奨アーキテクチャパターン](#推奨アーキテクチャパターン)
10. [実装ロードマップ](#実装ロードマップ)

---

## 概要

### システム目的
イベントのテーマ、ターゲット、目標人数、集客予算をもとに、無償・有償施策の最適なポートフォリオを提案するAIシステム

### 現在の技術スタック
- **フロントエンド**: Streamlit
- **バックエンド**: FastAPI
- **データベース**: SQLite
- **機械学習**: scikit-learn
- **言語**: Python 3.9+

---

## 技術選定の判断基準

### 1. ビジネス要件
| 項目 | 現在 | 6ヶ月後予想 | 1年後予想 |
|------|------|-------------|-----------|
| 同時ユーザー数 | 1-5 | 10-50 | 100-500 |
| データ量 | <100MB | 1-10GB | 10-100GB |
| イベント数/月 | 10-50 | 100-500 | 500-2000 |
| 予測精度要求 | 70%+ | 80%+ | 85%+ |

### 2. 技術的制約
- **チーム規模**: 1-3名の開発者
- **運用体制**: 専任運用者なし
- **予算**: 月額 $50-500 (段階的拡張)
- **セキュリティ**: 中程度（個人情報含まず）

### 3. 非機能要件
- **可用性**: 99.5% (月間ダウンタイム < 4時間)
- **応答時間**: API < 2秒, 予測生成 < 10秒
- **スケーラビリティ**: 10倍のユーザー増に対応可能
- **保守性**: 新機能追加が容易

---

## データベース選定

### 決定: PostgreSQL + Redis

#### PostgreSQL（メインデータベース）
**選定理由**:
- 高度なSQL機能（JSON、配列、全文検索）
- 機械学習拡張（MADlib）対応
- 優れたACID特性
- 豊富な運用ノウハウ

**代替案検討**:
- **MySQL**: 高速だが機能制限あり
- **MongoDB**: NoSQLだが複雑なクエリに不向き
- **TimescaleDB**: 時系列データに特化、汎用性低い

#### Redis（キャッシュ・セッション）
**用途**:
- 予測結果のキャッシュ
- セッション管理
- リアルタイムデータ

**設定例**:
```yaml
PostgreSQL:
  - Primary: AWS RDS PostgreSQL 13
  - Read Replica: 2台（負荷分散）
  - Backup: 自動バックアップ（7日保持）

Redis:
  - AWS ElastiCache Redis 6.2
  - Multi-AZ: 高可用性
  - TTL: 予測結果 1時間, セッション 24時間
```

---

## 機械学習・AI技術スタック

### 決定: XGBoost + MLflow + Feast

#### 機械学習フレームワーク
**XGBoost（メイン予測モデル）**
```python
# 現在: scikit-learn LinearRegression
# 移行先: XGBoost
from xgboost import XGBRegressor

model = XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)
```

**Prophet（時系列予測）**
```python
# 季節性・トレンド分析
from prophet import Prophet

# イベント参加者数の時系列予測
prophet_model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False
)
```

#### MLOps
**MLflow（実験管理・モデル管理）**
- 実験追跡
- モデルバージョニング
- A/Bテスト管理
- 自動デプロイ

**Feast（特徴量ストア）**
- 特徴量の再利用
- オンライン/オフライン統一
- データ品質監視

#### 代替案検討
- **LightGBM**: XGBoostと同等、メモリ効率良い
- **TensorFlow**: オーバースペック
- **PyTorch**: 深層学習不要

---

## インフラ・デプロイメント

### 3つの推奨アーキテクチャパターン

#### パターン1: スタートアップ向け（月額 $50-100）
**構成**: Heroku + Heroku Postgres + Redis Cloud
- 簡単デプロイ
- 運用負荷最小
- 段階的スケーリング

#### パターン2: 成長企業向け（月額 $200-500）
**構成**: AWS ECS + RDS + ElastiCache
- コンテナベース
- 自動スケーリング
- 本格的な監視

#### パターン3: エンタープライズ向け（月額 $500-2000）
**構成**: Kubernetes + Aurora + 分散キャッシュ
- マイクロサービス
- 高可用性
- 多リージョン対応

### コンテナ化
**Docker + Docker Compose**
```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Kubernetes（本格運用時）**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: events-ai-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: events-ai-api
  template:
    metadata:
      labels:
        app: events-ai-api
    spec:
      containers:
      - name: api
        image: events-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

---

## API・インテグレーション

### 決定: FastAPI + Kong Gateway

#### API Framework
**FastAPI（継続使用）**
- 高性能（Starlette/Pydantic）
- 自動API文書生成
- 型安全性
- 非同期処理対応

#### API Gateway
**Kong**
```yaml
機能:
  - レート制限: 1000 req/min/user
  - 認証: JWT + OAuth 2.0
  - ログ: 全APIコール記録
  - 監視: Prometheus メトリクス
```

#### 外部連携API
**メール配信**: SendGrid
```python
import sendgrid
from sendgrid.helpers.mail import Mail

sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
```

**広告プラットフォーム**: 
- Facebook Ads API
- Google Ads API
- LinkedIn Campaign Manager API

---

## 監視・ログ・セキュリティ

### 監視スタック: Prometheus + Grafana + AlertManager

#### メトリクス監視
```yaml
監視項目:
  - API応答時間 (P50, P95, P99)
  - 予測精度 (MAE, RMSE)
  - データ品質 (欠損率, 異常値)
  - システムリソース (CPU, Memory, Disk)
  - ビジネスメトリクス (予測回数, 成功率)
```

#### ログ管理: ELK Stack
```yaml
Elasticsearch: ログ保存・検索
Logstash: ログ収集・変換
Kibana: 可視化・ダッシュボード

保持期間:
  - エラーログ: 90日
  - アクセスログ: 30日
  - 予測ログ: 1年
```

### セキュリティ

#### 認証・認可: Auth0
```yaml
機能:
  - SSO (Google, Microsoft)
  - 多要素認証 (MFA)
  - ロールベースアクセス制御
  - セッション管理
```

#### データ暗号化
```yaml
保存時:
  - データベース: TDE (Transparent Data Encryption)
  - ファイル: AES-256

転送時:
  - HTTPS/TLS 1.3
  - API通信: JWT署名
```

---

## フロントエンド技術

### 段階的移行戦略

#### Phase 1: Streamlit（現在）
- 迅速なプロトタイピング
- データサイエンティスト向け

#### Phase 2: Streamlit + カスタムコンポーネント
```python
# React コンポーネントの埋め込み
import streamlit.components.v1 as components

components.html("""
<div id="custom-dashboard"></div>
<script src="dashboard.js"></script>
""", height=600)
```

#### Phase 3: React + TypeScript（本格運用）
```typescript
// 型安全なAPI呼び出し
interface EventRequest {
  eventName: string;
  category: EventCategory;
  targetAudience: TargetAudience;
  budget: number;
}

const generateCampaigns = async (request: EventRequest): Promise<CampaignResponse> => {
  // API呼び出し
};
```

### UI/UXライブラリ
- **Material-UI**: 統一されたデザインシステム
- **Chart.js/D3.js**: 高度なデータ可視化
- **React Query**: 効率的なデータフェッチ

---

## 推奨アーキテクチャパターン

### パターン1: スタートアップ向け
**対象**: ユーザー数 < 100, 予算 < $100/月

**メリット**:
- 低コスト
- 簡単デプロイ
- 運用負荷最小

**デメリット**:
- スケーラビリティ制限
- カスタマイズ制約

### パターン2: 成長企業向け
**対象**: ユーザー数 100-1000, 予算 $200-500/月

**メリット**:
- 自動スケーリング
- 本格的な監視
- CI/CD統合

**デメリット**:
- 運用複雑性増加
- AWS依存

### パターン3: エンタープライズ向け
**対象**: ユーザー数 > 1000, 予算 > $500/月

**メリット**:
- 高可用性
- マルチリージョン
- 完全な可観測性

**デメリット**:
- 高い運用コスト
- 複雑なアーキテクチャ

---

## 実装ロードマップ

### Phase 1: 基盤強化（1-2ヶ月）
```yaml
必須:
  - PostgreSQL移行
  - Docker化
  - 基本監視 (Prometheus)
  - CI/CD パイプライン (GitHub Actions)

推奨:
  - MLflow導入
  - Redis キャッシュ
  - API Gateway
```

### Phase 2: 機能拡張（2-3ヶ月）
```yaml
必須:
  - XGBoost モデル
  - データパイプライン (Airflow)
  - 認証システム (Auth0)
  - ログ管理 (ELK)

推奨:
  - 外部API連携
  - A/Bテスト機能
  - 特徴量ストア (Feast)
```

### Phase 3: 本格運用（3-6ヶ月）
```yaml
必須:
  - 包括的監視・アラート
  - セキュリティ強化
  - パフォーマンス最適化
  - React フロントエンド

推奨:
  - Kubernetes移行
  - マイクロサービス化
  - モバイルアプリ
```

### Phase 4: スケーリング（6-12ヶ月）
```yaml
必須:
  - 多リージョン展開
  - 機械学習パイプライン自動化
  - リアルタイム予測
  - 高度な分析機能

推奨:
  - 深層学習モデル
  - エッジコンピューティング
  - API エコシステム
```

---

## 意思決定の記録

### 主要な技術選定理由

#### データベース: PostgreSQL
- **決定日**: 2025年6月21日
- **理由**: 機械学習拡張、JSON対応、成熟度
- **代替案**: MySQL（機能制限）、MongoDB（複雑性）

#### ML フレームワーク: XGBoost
- **決定日**: 2025年6月21日
- **理由**: 表形式データに最適、解釈性、性能
- **代替案**: LightGBM（メモリ効率）、TensorFlow（オーバースペック）

#### インフラ: AWS
- **決定日**: 2025年6月21日
- **理由**: 豊富なマネージドサービス、スケーラビリティ
- **代替案**: GCP（機械学習特化）、Azure（企業向け）

#### フロントエンド: Streamlit → React
- **決定日**: 2025年6月21日
- **理由**: 段階的移行、開発効率、ユーザビリティ
- **代替案**: Vue.js（学習コスト低）、Angular（エンタープライズ）

---

## リスク評価

### 技術リスク
| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| PostgreSQL移行時のデータ損失 | 高 | 低 | バックアップ、段階的移行 |
| XGBoost性能不足 | 中 | 中 | LightGBM代替案準備 |
| AWS障害 | 高 | 低 | マルチAZ、バックアップ |
| React移行の遅延 | 低 | 中 | Streamlit並行運用 |

### ビジネスリスク
| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| ユーザー急増によるスケール不足 | 高 | 中 | 自動スケーリング |
| 予測精度低下 | 高 | 中 | モデル監視、再学習 |
| セキュリティ侵害 | 高 | 低 | 多層防御、監査 |
| 競合サービス出現 | 中 | 高 | 差別化機能開発 |

---

## 承認・レビュー

**作成者**: AI開発チーム  
**レビュー者**: CTO、プロダクトマネージャー  
**承認者**: CEO  
**次回レビュー予定**: 2025年9月

---

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)
- [XGBoost公式ドキュメント](https://xgboost.readthedocs.io/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [MLflow公式ドキュメント](https://mlflow.org/docs/latest/index.html)

---

**文書バージョン履歴**:
- v1.0 (2025年6月21日): 初版作成 