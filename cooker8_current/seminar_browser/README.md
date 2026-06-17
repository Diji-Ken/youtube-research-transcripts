# cooker8 Google Workspace セミナー素材ブラウザ

cooker8 by 明治クッカーの現行公開動画560本の文字起こしを、Google Workspace / JWS セミナー企画用に整理した静的ブラウザです。

## 内容

- `index.html`: 検索ブラウザ本体
- `data/seminar-data.json`: 560本の分類・抜粋・検索用テキスト
- `docs/tool_index.md`: ツール別の整理
- `docs/latest_priority.md`: 最新版優先・重複テーマ整理
- `docs/quality_report.md`: 文字起こし品質チェック

## ローカルで見る

このフォルダの親ディレクトリをHTTPサーバーで開きます。

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory /Users/m/Workspace/mirai/40_research/YouTube/transcripts_clean/cooker8
```

ブラウザで開くURL:

```text
http://127.0.0.1:8765/seminar_browser/
```

`index.html` を直接開くと、ブラウザの制約で `seminar-data.json` を読めない場合があります。

## 確認済み

- 対象動画: 560本
- 文字起こしあり: 560本
- 800字未満の短い文字起こし: 3本
- 最新動画: 2026-06-17
