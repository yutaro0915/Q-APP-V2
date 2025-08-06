06_frontend_design_nextjs_v1.md — フロントエンド設計（v1）
Stack: Next.js 14 App Router / Tailwind + shadcn/ui
前提：閲覧は認証不要（SSR可）、作成系は Bearer 必須。画像はクライアント縮小→S3直PUT。

1. ルーティング & データ取得
bash
コピーする
編集する
/                        # TL（Hot/New 切替・SSR）
/search                  # 検索（SSR: qで初回、以後CSRページング）
/thread/[id]             # スレ詳細（SSR: 本文+最初のコメント20件）※コメント続きはCSR
/settings/profile        # プロフィール編集（CSR、要Bearer）
SSR方針：GETは公開エンドポイントなのでSSRで初回表示可能。

CSR方針：投稿/コメント/リアクション/解決/プロフィール更新は CSR で fetch。

ページング：nextCursor がある限り“もっと見る”。カーソルは状態に保持。

2. グローバル
HTTPクライアント：薄い apiClient（Authorization ヘッダを必要時のみ付与）。

トークン管理：bootstrap 成功時に localStorage 保存（token）。閲覧は不要なので SSR 影響なし。

エラーUI：ErrorResponse を解釈してトースト/バナー表示。requestId は詳細展開に表示。

ローディング：Skeleton コンポーネント（TLカード/コメント行用）。

i18n：日本語固定（v1）。

3. コンポーネント構成 & Props
php
コピーする
編集する
components/
  ThreadCard.tsx
    props: {
      id, title, excerpt, tags: TagDTO[], heat, replies, saves,
      createdAt, lastReplyAt?, hasImage, imageThumbUrl?,
      authorAffiliation?: { faculty?: string; year?: number } | null,
      liked?: boolean, saved?: boolean
    }

  ThreadList.tsx
    props: { items: ThreadCardProps[], onLoadMore?: () => void, hasMore?: boolean }

  ThreadView.tsx
    props: {
      thread: ThreadDetailDTO & { authorAffiliation?: {...} | null },
      firstPageComments: CommentDTO[],   // SSR 渡し
      initialNextCursor?: string | null
    }

  CommentItem.tsx
    props: {
      id, body, createdAt, upCount,
      hasImage, imageUrl?, liked?,
      authorAffiliation?: { faculty?: string; year?: number } | null
    }

  HeatChip.tsx         # 0..100
  TagChips.tsx         # 固定4キー表示
  ImageViewer.tsx      # フルスクリーン
  NewThreadForm.tsx
    - title（必須・60）
    - body（2000）
    - tags（チップUI：種別/場所/締切/授業コード）
    - image 1枚（下記アップロードフロー）
  NewCommentForm.tsx   # body 1000 / image 1枚
4. 画像アップロード（クライアント）
手順：POST /uploads/presign → 返却 url, headers, key → PUT（fetch(url, { method:'PUT', headers, body:blob })）→ imageKey=key を作成APIに渡す。

縮小/EXIF除去：

ts
コピーする
編集する
// pseudo
const img = await createImageBitmap(file)
const {w, h} = fitLongEdge(img.width, img.height, 2048)
const canvas = new OffscreenCanvas(w, h)
const ctx = canvas.getContext('2d')
ctx.drawImage(img, 0, 0, w, h)
const blob = await canvas.convertToBlob({ type: 'image/webp', quality: 0.9 })
サムネ：TLは CSS object-cover で 16:9。詳細/コメントは等比→クリックで ImageViewer 全画面。

5. 画面ごとの受け渡し項目（API依存）
TL（GET /threads）→ ThreadCard[]

表示：タイトル / 1行プレビュー / タグ ≤3 / heat / 返信数 / 保存数 / 作成相対時刻 / 著者チップ（任意）

スレ詳細（GET /threads/{id}, GET /threads/{id}/comments）

表示：本文 / タグ / up/save カウント / 解決ピン / コメント（時系列）

アクション：Up/保存（スレ）・Up（コメント）・解決設定/解除（スレ主）・削除

検索（GET /search）→ ThreadCard[]（並び違いのみ）

プロフィール設定（GET|PATCH /auth/me/profile）

フォーム：学部（≤50）/ 学年（1..10）/ 公開スイッチ×2

6. UI仕様（要点）
TLカード：全体クリックで遷移、右下に♡保存ボタン（ログイン時のみ有効）。

コメント並び：時系列 ASC 固定。解決コメントは最上段にピン表示（仕様通り）。

未読導線：v1では簡易（参加中スレのバッジのみ）。

アクセシビリティ：ボタンに aria-label、キーボード操作対応（Enter/Space）。

フォーム検証：入力直後に即時フィードバック（title 1..60、body 文字数カウンタ）。

7. API クライアント薄ラッパ（例）
ts
コピーする
編集する
// lib/apiClient.ts
export async function api<T>(path: string, init: RequestInit = {}, needAuth = false): Promise<T> {
  const headers: any = { 'Content-Type': 'application/json', ...(init.headers||{}) }
  if (needAuth) {
    const token = localStorage.getItem('token')
    if (!token) throw new Error('UNAUTHORIZED')
    headers['Authorization'] = `Bearer ${token}`
  }
  const r = await fetch(`/api/v1${path}`, { ...init, headers, cache: 'no-store' })
  if (!r.ok) {
    const e = await r.json().catch(() => ({}))
    throw Object.assign(new Error(e?.error?.message || r.statusText), { status: r.status, requestId: r.headers.get('X-Request-Id'), details: e?.error?.details })
  }
  return r.status === 204 ? (undefined as any) : r.json()
}
8. ページング（無限スクロール）
nextCursor を state に保持。onLoadMore で追い読み。

タブ切替（Hot↔New）/検索語変更でカーソル破棄→先頭から再取得。

戻る時は 前回 items をメモリに保持（最大100件）→リスト復元。

9. プロフィール公開表示
著者チップ：authorAffiliation が null でなければ [工学部][B3] のように表示（学部→日本語ラベル化はそのまま文字列表示、学年は B{n}/M{n}/D{n} などの表記はv1は数字のみでOK）。

/settings/profile で編集→保存成功でトースト表示→TL/スレは次回取得時に反映。

10. スタイル & コンポーネント
Tailwind で余白確保、shadcn/ui の Button/Input/Badge/Sheet を採用。

カードは 単一カラム、モバイル主導でPCは横幅 680–760px の中央寄せ。

ダイアログは最小限（削除確認のみ）。