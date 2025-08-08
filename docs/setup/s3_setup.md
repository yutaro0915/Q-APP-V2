# Amazon S3 画像アップロード用バケットセットアップ手順書

## 1. 前提条件
- AWSアカウントへのアクセス権限
- AWS CLIがインストール済み
- IAMユーザーまたはロールの作成権限

## 2. S3バケット作成

### 2.1 コンソールから作成
1. AWS S3コンソールへ移動
2. 「バケットを作成」をクリック
3. 以下の設定を適用：

#### 一般的な設定
| 項目 | 設定値 |
|------|--------|
| バケット名 | kyudai-campus-sns-uploads |
| リージョン | アジアパシフィック（東京）ap-northeast-1 |

#### オブジェクト所有者
| 項目 | 設定値 |
|------|--------|
| オブジェクト所有者 | バケット所有者を優先 |

#### パブリックアクセス設定
| 項目 | 設定値 |
|------|--------|
| パブリックアクセスをすべてブロック | オフ |
| 新しいアクセスコントロールリスト（ACL）を介して付与されたバケットとオブジェクトへのパブリックアクセスをブロックする | オフ |
| 任意のアクセスコントロールリスト（ACL）を介して付与されたバケットとオブジェクトへのパブリックアクセスをブロックする | オフ |
| 新しいパブリックバケットまたはアクセスポイントポリシーを介して付与されたバケットとオブジェクトへのパブリックアクセスをブロックする | オン |
| 任意のパブリックバケットまたはアクセスポイントポリシーを介したバケットとオブジェクトへのパブリックアクセスをブロックおよび制限する | オン |

**警告確認**: パブリックアクセスの設定変更について警告が表示されるので、確認して承認

#### バケットのバージョニング
| 項目 | 設定値 |
|------|--------|
| バケットのバージョニング | 無効 |

#### デフォルト暗号化
| 項目 | 設定値 |
|------|--------|
| 暗号化タイプ | Amazon S3マネージドキー（SSE-S3） |
| バケットキー | 有効 |

### 2.2 CLIから作成（代替手段）
```bash
# バケット作成
aws s3api create-bucket \
  --bucket kyudai-campus-sns-uploads \
  --region ap-northeast-1 \
  --create-bucket-configuration LocationConstraint=ap-northeast-1

# 暗号化設定
aws s3api put-bucket-encryption \
  --bucket kyudai-campus-sns-uploads \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'

# パブリックアクセスブロック設定（部分的）
aws s3api put-public-access-block \
  --bucket kyudai-campus-sns-uploads \
  --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

## 3. バケットポリシー設定

### 3.1 バケットポリシーJSON
以下のポリシーをバケットに適用（バケット名を実際の名前に置換）：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::kyudai-campus-sns-uploads/uploads/*"
    }
  ]
}
```

### 3.2 ポリシーの適用方法

#### コンソールから
1. S3バケットの「アクセス許可」タブへ移動
2. 「バケットポリシー」セクションで「編集」をクリック
3. 上記のJSONを貼り付け（バケット名を置換）
4. 「変更を保存」をクリック

#### CLIから
```bash
# policy.jsonファイルを作成してから実行
aws s3api put-bucket-policy \
  --bucket kyudai-campus-sns-uploads \
  --policy file://policy.json
```

## 4. CORS設定

### 4.1 CORS設定JSON
以下のCORS設定を適用：

```json
[
  {
    "AllowedHeaders": [
      "Content-Type",
      "x-amz-meta-width",
      "x-amz-meta-height",
      "x-amz-meta-sha256"
    ],
    "AllowedMethods": [
      "PUT",
      "GET",
      "HEAD"
    ],
    "AllowedOrigins": [
      "https://kyudai-front.awsapprunner.com",
      "http://localhost:3000"
    ],
    "ExposeHeaders": [
      "ETag",
      "x-amz-version-id"
    ],
    "MaxAgeSeconds": 3000
  }
]
```

**注意**: 本番環境では`http://localhost:3000`を削除し、実際のフロントエンドドメインのみを許可

### 4.2 CORS設定の適用

#### コンソールから
1. S3バケットの「アクセス許可」タブへ移動
2. 「Cross-origin resource sharing (CORS)」セクションで「編集」をクリック
3. 上記のJSONを貼り付け
4. 「変更を保存」をクリック

#### CLIから
```bash
# cors.jsonファイルを作成してから実行
aws s3api put-bucket-cors \
  --bucket kyudai-campus-sns-uploads \
  --cors-configuration file://cors.json
```

## 5. ディレクトリ構造の準備

### 5.1 初期ディレクトリ作成
```bash
# uploadsディレクトリのプレースホルダー作成
echo "" | aws s3 cp - s3://kyudai-campus-sns-uploads/uploads/.keep

# threadsディレクトリ
echo "" | aws s3 cp - s3://kyudai-campus-sns-uploads/uploads/threads/.keep

# commentsディレクトリ
echo "" | aws s3 cp - s3://kyudai-campus-sns-uploads/uploads/comments/.keep
```

## 6. IAMポリシーとロール設定

### 6.1 App Runner用IAMポリシー
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3PresignedUrlGeneration",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::kyudai-campus-sns-uploads/uploads/*"
    },
    {
      "Sid": "S3ListBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::kyudai-campus-sns-uploads"
    }
  ]
}
```

### 6.2 IAMロールへのポリシーアタッチ
```bash
# ポリシー作成
aws iam create-policy \
  --policy-name KyudaiS3UploadPolicy \
  --policy-document file://iam-policy.json

# App RunnerサービスロールへアタッチApp
aws iam attach-role-policy \
  --role-name [AppRunnerServiceRole] \
  --policy-arn arn:aws:iam::[AccountID]:policy/KyudaiS3UploadPolicy
```

## 7. 環境変数設定

App Runnerサービスに以下の環境変数を設定：

```bash
# S3バケット名
S3_BUCKET=kyudai-campus-sns-uploads

# S3リージョン
AWS_REGION=ap-northeast-1

# アップロードパス prefix
S3_UPLOAD_PREFIX=uploads/

# Presigned URL有効期限（秒）
S3_PRESIGNED_URL_EXPIRES=300

# 最大ファイルサイズ（バイト）
MAX_FILE_SIZE=5242880  # 5MB
```

## 8. Presigned URL生成テスト

### 8.1 Python（boto3）での生成例
```python
import boto3
from botocore.exceptions import ClientError
import json

def generate_presigned_url():
    s3_client = boto3.client('s3', region_name='ap-northeast-1')
    
    bucket_name = 'kyudai-campus-sns-uploads'
    object_key = 'uploads/threads/test-image.jpg'
    
    try:
        # PutObject用のPresigned URL生成
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': 'image/jpeg',
                'Metadata': {
                    'width': '1024',
                    'height': '768',
                    'sha256': 'sample-hash'
                }
            },
            ExpiresIn=300
        )
        return response
    except ClientError as e:
        print(f"Error: {e}")
        return None

# テスト実行
url = generate_presigned_url()
print(f"Presigned URL: {url}")
```

### 8.2 cURLでのアップロードテスト
```bash
# Presigned URLを取得後
PRESIGNED_URL="https://kyudai-campus-sns-uploads.s3.ap-northeast-1.amazonaws.com/..."

# ファイルアップロード
curl -X PUT \
  -H "Content-Type: image/jpeg" \
  -H "x-amz-meta-width: 1024" \
  -H "x-amz-meta-height: 768" \
  -H "x-amz-meta-sha256: sample-hash" \
  --data-binary @test-image.jpg \
  "$PRESIGNED_URL"
```

## 9. セキュリティベストプラクティス

### 9.1 アクセス制御
- Presigned URLの有効期限を短く設定（300秒以下）
- CloudFrontを経由した配信を検討
- バケットポリシーで特定のprefixのみ公開

### 9.2 コンテンツ検証
- アップロード前のファイルタイプ検証
- ファイルサイズ制限の実装
- SHA256ハッシュでの整合性確認

### 9.3 監視とログ
- S3アクセスログの有効化
- CloudTrailでのAPI呼び出し記録
- CloudWatchアラームの設定

## 10. トラブルシューティング

### CORS エラー
1. CORS設定のAllowedOriginsを確認
2. ブラウザの開発者ツールでOriginヘッダーを確認
3. プリフライトリクエスト（OPTIONS）が許可されているか確認

### Presigned URLエラー
1. IAMロールの権限を確認
2. URL有効期限が切れていないか確認
3. Content-Typeが一致しているか確認

### アップロード失敗
1. ファイルサイズが制限内か確認
2. ネットワーク接続を確認
3. S3バケットのクォータを確認

### パブリックアクセス不可
1. バケットポリシーが正しく設定されているか確認
2. パブリックアクセスブロック設定を確認
3. オブジェクトのACLを確認

## 11. 運用チェックリスト

### 初期設定時
- [ ] バケットが作成されている
- [ ] CORS設定が適用されている
- [ ] バケットポリシーが設定されている
- [ ] 暗号化が有効になっている
- [ ] IAMロールに必要な権限がある

### 定期確認項目
- [ ] ストレージ使用量の監視
- [ ] 不要なオブジェクトの削除
- [ ] アクセスログの確認
- [ ] セキュリティ設定の見直し

### 本番移行時
- [ ] CORS設定からlocalhostを削除
- [ ] CloudFront経由の配信設定
- [ ] ライフサイクルポリシーの設定
- [ ] バックアップ戦略の確立