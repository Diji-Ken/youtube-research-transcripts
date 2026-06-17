#!/usr/bin/env python3
"""Build a Google Workspace seminar research browser from cooker8 transcripts."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


BASE = Path("/Users/m/Workspace/mirai/40_research/YouTube/transcripts_clean/cooker8")
MANIFEST = BASE / "manifest.json"
OUT = BASE / "seminar_browser"
DATA = OUT / "data"
DOCS = OUT / "docs"


TOOL_DEFS = [
    {
        "id": "overview",
        "name": "Google Workspace全体",
        "keywords": ["有償版", "無償版", "最新情報", "アップデート", "全体", "基本", "導入", "完全解説", "良さ", "ユーザーの本音"],
        "capabilities": [
            "Googleの複数ツールを組み合わせ、情報共有、会議、資料作成、データ管理を一体運用する",
            "毎月のアップデートを追い、従来の使い方からAI前提の使い方へ移行する",
            "社内のルール、権限、運用設計まで含めて業務基盤として整える",
        ],
    },
    {
        "id": "gemini_ai",
        "name": "Gemini / AI / NotebookLM",
        "keywords": ["Gemini", "AI", "NotebookLM", "Workspace Studio", "Gem", "Canvas", "Cinematic", "日本語要約", "プロンプト", "Veo"],
        "capabilities": [
            "会議、資料、文書、フォーム、チャットなどの作成・要約・整理をAIで補助する",
            "NotebookLMで社内資料や制度情報を読み込み、業務理解や年末調整、補助金確認に使う",
            "Workspace StudioやGemini Canvasで業務アプリ、理解度テスト、集計補助を素早く作る",
        ],
    },
    {
        "id": "gmail",
        "name": "Gmail",
        "keywords": ["Gmail", "メール", "ショートカット", "署名", "受信トレイ", "問い合わせ", "アドレス", "ラベル"],
        "capabilities": [
            "メール処理をショートカット、ラベル、検索、連携で高速化する",
            "問い合わせ窓口やチームアドレスをGoogle Chat/グループと組み合わせて運用する",
            "移動中の資料作成やコミュニケーションをGmailから始められるようにする",
        ],
    },
    {
        "id": "chat",
        "name": "Google Chat",
        "keywords": ["Google Chat", "Googleチャット", "チャット", "スペース", "ルーム", "社内コミュニケーション", "情報共有", "タスク管理", "ToDo"],
        "capabilities": [
            "社内連絡、タスク、会議前後のやり取りをスペースに集約する",
            "Gmailやフォームと連携し、問い合わせや通知をチームで処理する",
            "情報共有がうまくいかない原因を、運用ルールと発信設計で改善する",
        ],
    },
    {
        "id": "meet",
        "name": "Google Meet",
        "keywords": ["Google Meet", "GoogleMeet", "Meet", "ミート", "会議", "ウェブ会議", "画面共有", "コンパニオン", "議事録", "要約", "リアルタイム"],
        "capabilities": [
            "オンライン会議、画面共有、共同作業、会議要約を効率化する",
            "会議を報告の場ではなく、意思決定と論点整理の場に変える",
            "会議前後の議事録、メモ、資料共有をWorkspace内で接続する",
        ],
    },
    {
        "id": "calendar",
        "name": "Googleカレンダー",
        "keywords": ["Googleカレンダー", "カレンダー", "日程調整", "予定", "アイテマス", "Calendly", "予約", "会議室", "土日祝"],
        "capabilities": [
            "日程調整、予定管理、会議室管理、定休日表示を効率化する",
            "Meetや外部日程調整ツールと連携し、候補日提示や予約を自動化する",
            "チームの予定を見える化して、会議や現場対応の抜け漏れを減らす",
        ],
    },
    {
        "id": "drive",
        "name": "Googleドライブ",
        "keywords": ["Googleドライブ", "ドライブ", "共有ドライブ", "ファイル", "フォルダ", "権限", "検索", "リンク", "契約", "脳"],
        "capabilities": [
            "ファイル保管、共有、検索、権限管理を整えて情報の迷子を減らす",
            "契約フローや社内資料を紙からドライブ中心に移行する",
            "AI時代に、ドライブを社内知識の入口として活用する",
        ],
    },
    {
        "id": "docs",
        "name": "Googleドキュメント",
        "keywords": ["Googleドキュメント", "ドキュメント", "Docs", "Word", "議事録", "マニュアル", "スマートキャンバス", "紙文書"],
        "capabilities": [
            "議事録、マニュアル、共同編集文書をクラウドで一元管理する",
            "Wordとの違いを理解し、共同編集・コメント・AI活用を前提に文書作成する",
            "会議メモや定例資料を使い回し、複数ファイル作成を減らす",
        ],
    },
    {
        "id": "sheets",
        "name": "Googleスプレッドシート",
        "keywords": ["スプレッドシート", "シート", "関数", "Query", "IMPORTRANGE", "集計", "チェックリスト", "請求", "入金", "ピボット", "データ分析"],
        "capabilities": [
            "チェックリスト、請求入金管理、実績集計、データ連携を作る",
            "Query、IMPORTRANGE、ピボットなどで複数データを統合する",
            "フォームやスライド、Looker Studioと連携して集計と資料化を自動化する",
        ],
    },
    {
        "id": "slides",
        "name": "Googleスライド",
        "keywords": ["Googleスライド", "スライド", "プレゼン", "資料作成", "リンク", "テンプレート", "発表"],
        "capabilities": [
            "資料作成だけでなく、リンク更新やテンプレートで定例資料を効率化する",
            "スプレッドシートや画像素材と連携し、手作業の更新を減らす",
            "セミナー資料、提案資料、社内説明資料を共同編集で作る",
        ],
    },
    {
        "id": "forms",
        "name": "Googleフォーム",
        "keywords": ["Googleフォーム", "フォーム", "アンケート", "回答", "理解度テスト", "テスト", "問い合わせ", "申請"],
        "capabilities": [
            "問い合わせ、アンケート、理解度テスト、申請受付を作る",
            "スプレッドシートやGeminiと組み合わせて集計、採点、レポート化する",
            "研修や評価に使えるステップ配信型テストや回答通知を設計する",
        ],
    },
    {
        "id": "sites",
        "name": "Googleサイト",
        "keywords": ["Googleサイト", "サイト", "社内ポータル", "ポートフォリオ", "名刺", "掲示板"],
        "capabilities": [
            "社内ポータル、マニュアル、情報掲示板、ポートフォリオサイトを作る",
            "検索性と導線を整え、使われるサイトに改善する",
            "Googleドライブやドキュメントと連携して情報の入口を作る",
        ],
    },
    {
        "id": "appsheet",
        "name": "AppSheet / 業務アプリ",
        "keywords": ["AppSheet", "アプリ", "内製化", "業務アプリ", "出退勤", "現場", "モバイルフレームワーク", "ノーコード"],
        "capabilities": [
            "現場主導で出退勤、営業、チェック、管理系の業務アプリを作る",
            "外注に頼らず、Googleデータと連携した小さな業務改善を内製化する",
            "アプリ構築ステップを整理し、ミスや二重入力を減らす",
        ],
    },
    {
        "id": "looker",
        "name": "Looker Studio / データポータル",
        "keywords": ["データポータル", "Looker", "Looker Studio", "ダッシュボード", "レポート", "可視化", "地図", "Googleマップ"],
        "capabilities": [
            "スプレッドシートや業務データをダッシュボード化する",
            "営業実績、地図、複数シートの集計を見える化する",
            "レポート作成を定例作業から自動更新の仕組みに変える",
        ],
    },
    {
        "id": "chrome",
        "name": "Chrome / Chromebook",
        "keywords": ["Chrome", "Chromebook", "ブラウザ", "拡張機能", "検索", "ショートカット", "Gemini in Chrome"],
        "capabilities": [
            "ブラウザ作業、検索、拡張機能、教育現場の端末管理を効率化する",
            "Gemini in Chromeでブラウザ上の作業をAI補助に変える",
            "日常的な小技を積み上げて、調べる・探す・入力する時間を削る",
        ],
    },
    {
        "id": "keep_tasks",
        "name": "Keep / ToDo / Tasks",
        "keywords": ["Google Keep", "Keep", "ToDo", "タスク", "メモ", "チェック", "リマインダー"],
        "capabilities": [
            "メモ、チェックリスト、ToDo、リマインダーを軽量に管理する",
            "会議や現場で発生したタスクをその場で拾い、Chatやカレンダーとつなげる",
            "個人のメモ魔的な運用から、チームタスク管理まで広げる",
        ],
    },
    {
        "id": "admin_security",
        "name": "管理 / セキュリティ / Googleグループ",
        "keywords": ["管理者", "セキュリティ", "ウイルス", "Googleグループ", "グループ", "権限", "共有設定", "アカウント", "管理コンソール"],
        "capabilities": [
            "アカウント、共有、権限、セキュリティを管理し、事故や情報漏れを防ぐ",
            "Googleグループでチームアドレスや権限単位を整える",
            "高額な対策ツールに頼る前にWorkspace標準機能で守りを固める",
        ],
    },
    {
        "id": "business_dx",
        "name": "DX / 業務設計 / マネジメント",
        "keywords": ["DX", "業務効率", "業務改善", "内製", "会議", "マネジメント", "コミュニケーション", "コンサル", "生産性", "SNS", "外注", "社長", "牛乳屋"],
        "capabilities": [
            "ツール単体ではなく、会議、情報共有、現場改善、社内発信まで業務として設計する",
            "外注依存から内製化へ移行し、社内に改善チームを作る",
            "セミナー訴求に使える実例、失敗談、組織変革の文脈を提供する",
        ],
    },
]


USE_CASE_DEFS = [
    ("meeting", "会議・議事録", ["会議", "議事録", "Meet", "ミーティング", "ファシリテーション", "ホワイトボード", "要約"]),
    ("knowledge", "情報共有・社内ポータル", ["情報共有", "社内ポータル", "掲示板", "マニュアル", "ナレッジ", "検索"]),
    ("data", "集計・分析・可視化", ["集計", "分析", "可視化", "レポート", "ダッシュボード", "データ", "Query", "ピボット"]),
    ("automation", "自動化・連携", ["自動化", "連携", "自動", "ワークフロー", "通知", "リンク", "IMPORTRANGE"]),
    ("ai", "AI活用", ["AI", "Gemini", "NotebookLM", "プロンプト", "要約", "Gem", "Canvas"]),
    ("paperless", "ペーパーレス・契約・文書", ["紙", "契約", "文書", "ドキュメント", "Word", "印刷"]),
    ("training", "研修・教育・テスト", ["研修", "教育", "テスト", "理解度", "学習", "セミナー", "講義"]),
    ("field", "現場DX・内製アプリ", ["現場", "AppSheet", "アプリ", "内製", "出退勤", "営業現場"]),
    ("communication", "コミュニケーション・マネジメント", ["コミュニケーション", "チャット", "部下", "上司", "マネジメント", "SNS", "社内発信"]),
    ("admin", "管理・セキュリティ", ["管理者", "セキュリティ", "権限", "アカウント", "グループ", "ウイルス"]),
]


STOPWORDS = {
    "Google",
    "Workspace",
    "GoogleWorkspace",
    "Worksapce",
    "https",
    "http",
    "www",
    "com",
    "forms",
    "gle",
    "amzn",
    "cooker8",
    "meijicooker",
    "nisshy",
    "youtube",
    "channel",
    "instagram",
    "twitter",
    "tiktok",
    "これ",
    "それ",
    "ため",
    "よう",
    "こと",
    "もの",
    "さん",
    "動画",
    "紹介",
    "解説",
    "完全",
    "最新",
    "活用",
    "使い方",
    "方法",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def compact(text: str, max_len: int = 160) -> str:
    text = normalize_text(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return datetime(1900, 1, 1)


def load_rows() -> list[dict]:
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for row in rows:
        txt_path = BASE / row["txt_file"]
        transcript = txt_path.read_text(encoding="utf-8", errors="ignore")
        row["transcript"] = normalize_text(transcript)
        row["description"] = normalize_text(row.get("description", ""))
        row["search_blob"] = normalize_text(
            " ".join([row.get("title", ""), row["transcript"]])
        )
    return rows


def count_keywords(blob: str, keywords: list[str]) -> int:
    total = 0
    lower = blob.lower()
    for keyword in keywords:
        if not keyword:
            continue
        total += lower.count(keyword.lower())
    return total


def score_tool(row: dict, tool: dict) -> int:
    keywords = tool["keywords"]
    title_score = count_keywords(row["title"], keywords) * 24
    desc_score = min(count_keywords(row.get("description", ""), keywords), 2)
    transcript_score = min(count_keywords(row["transcript"], keywords), 8)
    score = title_score + desc_score + transcript_score

    # Broad management/DX terms should not overwhelm concrete product names.
    if tool["id"] == "business_dx":
        score = min(score, 60) + count_keywords(row["title"], ["DX", "業務", "内製", "外注", "会議", "マネジメント", "SNS"]) * 12
    if tool["id"] == "overview":
        score = title_score + min(count_keywords(row["transcript"], keywords), 3)
    return score


def score_use_case(row: dict, keywords: list[str]) -> int:
    title_score = count_keywords(row["title"], keywords) * 16
    transcript_hits = count_keywords(row["transcript"], keywords)
    return title_score + min(transcript_hits, 10)


def classify(row: dict) -> tuple[list[str], str, list[str]]:
    tool_scores = []
    for tool in TOOL_DEFS:
        score = score_tool(row, tool)
        if score:
            tool_scores.append((score, tool["id"]))
    tool_scores.sort(reverse=True)
    tools = [tool_id for _, tool_id in tool_scores[:4]]
    if not tools:
        tools = ["business_dx"]
    primary = tools[0]

    use_scores = []
    for use_id, _, keywords in USE_CASE_DEFS:
        score = score_use_case(row, keywords)
        if score >= 4:
            use_scores.append((score, use_id))
    use_scores.sort(reverse=True)
    use_cases = [use_id for _, use_id in use_scores[:4]]
    if not use_cases:
        use_cases = ["knowledge" if primary in {"sites", "drive", "docs"} else "automation" if primary in {"sheets", "forms", "appsheet"} else "communication"]
    return tools, primary, use_cases


def extract_snippets(row: dict, keywords: list[str], max_count: int = 3) -> list[str]:
    text = row["transcript"]
    snippets = []
    lower = text.lower()
    for keyword in keywords:
        idx = lower.find(keyword.lower())
        if idx == -1:
            continue
        start = max(0, idx - 80)
        end = min(len(text), idx + len(keyword) + 140)
        snippet = text[start:end].strip()
        snippet = re.sub(r"\s+", " ", snippet)
        if snippet and snippet not in snippets:
            snippets.append(snippet)
        if len(snippets) >= max_count:
            break
    if not snippets:
        snippets.append(compact(row["transcript"], 220))
    return snippets


def extract_terms(rows: list[dict], tool_id: str) -> list[str]:
    tool = next(t for t in TOOL_DEFS if t["id"] == tool_id)
    text = " ".join(row["title"] for row in rows)
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9+.#/-]{2,}|[一-龠ぁ-んァ-ンー]{3,}", text)
    counter = Counter()
    for term in candidates:
        cleaned = term.strip("._-/").lower()
        if term in STOPWORDS:
            continue
        if cleaned in STOPWORDS:
            continue
        if "://" in term or term.startswith("www") or "." in term:
            continue
        if len(term) > 32:
            continue
        if any(term.lower() == keyword.lower() for keyword in tool["keywords"]):
            continue
        counter[term] += 1
    return [term for term, _ in counter.most_common(16)]


def infer_video_summary(row: dict) -> str:
    title = row["title"]
    primary = row["primaryToolName"]
    use_names = "・".join(row["useCaseNames"][:2])
    if "最新" in title or "アップデート" in title:
        return f"{primary}周辺の最新アップデートを確認する動画。セミナーでは、古い運用から新しい機能前提の運用へ切り替える導入パートに使いやすい。"
    if "完全版" in title or "決定版" in title or "基本" in title:
        return f"{primary}の基本から実務利用までを俯瞰する動画。初学者向けの講義、またはツール別入門セクションの主教材候補。"
    if "実演" in title or "作" in title or "手順" in title or "ステップ" in title:
        return f"{primary}を使って実際に作る・設定する流れを確認できる動画。{use_names}のワークショップ題材に向く。"
    if "事例" in title or "牛乳屋" in title or "現場" in title or "ANA" in title:
        return f"{primary}を業務現場に落とし込む事例動画。セミナーの導入、成功イメージ、社内説得用の具体例として使える。"
    return f"{primary}に関連する{use_names}の論点を扱う動画。セミナー企画時は該当ツールの補足教材として参照しやすい。"


def build_revision_groups(videos: list[dict]) -> list[dict]:
    patterns = [
        ("Google Workspace最新情報", ["最新情報", "アップデート"], ["overview", "gemini_ai"]),
        ("Gmail完全版・基本", ["Gmail"], ["gmail"]),
        ("Googleドライブ完全版・活用", ["ドライブ"], ["drive"]),
        ("Googleドキュメント完全版・文書活用", ["ドキュメント", "Word"], ["docs"]),
        ("Googleスライド資料作成", ["スライド"], ["slides"]),
        ("Googleフォーム活用・テスト・アンケート", ["フォーム", "理解度テスト", "アンケート"], ["forms"]),
        ("Googleカレンダー・日程調整", ["カレンダー", "日程調整"], ["calendar"]),
        ("Google Chat・社内コミュニケーション", ["チャット", "Google Chat", "情報共有"], ["chat"]),
        ("AppSheet・内製アプリ", ["AppSheet", "アプリ", "内製"], ["appsheet"]),
        ("Gemini/NotebookLM/AI活用", ["Gemini", "NotebookLM", "AI"], ["gemini_ai"]),
        ("会議・議事録・Meet", ["会議", "議事録", "Meet"], ["meet", "docs"]),
        ("スプレッドシート集計・関数", ["スプレッドシート", "関数", "Query", "集計"], ["sheets"]),
    ]
    groups = []
    for name, keywords, tool_ids in patterns:
        matched = [
            v
            for v in videos
            if any(k.lower() in v["title"].lower() for k in keywords)
            and (v["primaryTool"] in tool_ids or any(t in v["tools"][:2] for t in tool_ids))
        ]
        matched = sorted(matched, key=lambda v: v["date"], reverse=True)
        if len(matched) >= 2:
            groups.append(
                {
                    "name": name,
                    "count": len(matched),
                    "latest": matched[0],
                    "older": matched[1:8],
                    "note": "同テーマの動画は最新版を主教材にし、古い動画は変遷・背景・基本確認として扱う。",
                }
            )
    return groups


def make_docs(tool_summaries: list[dict], videos: list[dict], revision_groups: list[dict]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Google Workspace セミナー企画用 ツール別整理",
        "",
        "cooker8 by 明治クッカーの現行公開動画560本を、セミナー企画で使いやすいようにツール別・用途別に整理したものです。",
        "",
        "## 全体方針",
        "",
        "- 受講者には「ツール名」ではなく「業務で何が楽になるか」から見せる",
        "- 同じテーマの動画は最新版を優先し、古い動画は背景理解・変遷確認として扱う",
        "- セミナー構成は、全体像 → 個別ツール → 連携 → 現場事例 → 自社での次アクション、の順が使いやすい",
        "",
        "## ツール別",
        "",
    ]
    for tool in tool_summaries:
        lines.append(f"### {tool['name']} ({tool['videoCount']}本)")
        lines.append("")
        lines.append("できること:")
        for cap in tool["capabilities"]:
            lines.append(f"- {cap}")
        lines.append("")
        lines.append("代表動画:")
        for video in tool["topVideos"][:8]:
            lines.append(f"- {video['date']} [{video['title']}]({video['url']})")
        lines.append("")
    (DOCS / "tool_index.md").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        "# 最新版優先・重複テーマ整理",
        "",
        "同じツール/テーマで複数年にわたり動画が出ているものは、原則として最新投稿を正として扱います。",
        "",
    ]
    for group in revision_groups:
        latest = group["latest"]
        lines.append(f"## {group['name']} ({group['count']}本)")
        lines.append("")
        lines.append(f"- 最新優先: {latest['date']} [{latest['title']}]({latest['url']})")
        lines.append(f"- 扱い: {group['note']}")
        lines.append("")
        lines.append("過去動画:")
        for video in group["older"]:
            lines.append(f"- {video['date']} [{video['title']}]({video['url']})")
        lines.append("")
    (DOCS / "latest_priority.md").write_text("\n".join(lines), encoding="utf-8")

    latest = sorted(videos, key=lambda v: v["date"], reverse=True)[:30]
    short = [v for v in videos if v["transcriptChars"] < 800]
    lines = [
        "# 文字起こし品質チェック",
        "",
        f"- 対象動画: {len(videos)}本",
        f"- 文字起こしあり: {sum(1 for v in videos if v['transcriptChars'] > 0)}本",
        f"- 800字未満の短い文字起こし: {len(short)}本",
        "",
        "## 最新30本",
        "",
    ]
    for video in latest:
        lines.append(f"- {video['date']} `{video['id']}` {video['title']} ({video['transcriptChars']}字)")
    lines.append("")
    lines.append("## 短い文字起こし")
    lines.append("")
    for video in sorted(short, key=lambda v: v["transcriptChars"])[:80]:
        lines.append(f"- {video['date']} `{video['id']}` {video['title']} ({video['transcriptChars']}字)")
    (DOCS / "quality_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = load_rows()
    tool_name = {tool["id"]: tool["name"] for tool in TOOL_DEFS}
    use_case_name = {use_id: name for use_id, name, _ in USE_CASE_DEFS}

    videos = []
    for row in rows:
        tools, primary, use_cases = classify(row)
        primary_def = next(tool for tool in TOOL_DEFS if tool["id"] == primary)
        snippets = extract_snippets(row, primary_def["keywords"])
        video = {
            "index": row["index"],
            "id": row["id"],
            "title": row["title"],
            "date": row["upload_date"],
            "url": row["url"],
            "duration": row["duration"],
            "description": compact(row.get("description", ""), 700),
            "transcriptChars": row["transcript_chars"],
            "tools": tools,
            "toolNames": [tool_name[t] for t in tools],
            "primaryTool": primary,
            "primaryToolName": tool_name[primary],
            "useCases": use_cases,
            "useCaseNames": [use_case_name.get(u, u) for u in use_cases],
            "summary": "",
            "snippets": snippets,
            "searchText": compact(row["search_blob"], 10000),
            "mdFile": row["md_file"],
            "txtFile": row["txt_file"],
            "year": row["upload_date"][:4],
            "isRecent": row["upload_date"] >= "2025-01-01",
        }
        video["summary"] = infer_video_summary(video)
        videos.append(video)

    videos.sort(key=lambda v: v["date"], reverse=True)

    tool_summaries = []
    for tool in TOOL_DEFS:
        matched = [v for v in videos if v["primaryTool"] == tool["id"]]
        related = [v for v in videos if tool["id"] in v["tools"]]
        matched.sort(key=lambda v: (v["date"], v["transcriptChars"]), reverse=True)
        use_counter = Counter(use for v in matched for use in v["useCases"])
        tool_summaries.append(
            {
                "id": tool["id"],
                "name": tool["name"],
                "videoCount": len(matched),
                "relatedCount": len(related),
                "capabilities": tool["capabilities"],
                "keywords": tool["keywords"],
                "topTerms": extract_terms(matched, tool["id"]) if matched else [],
                "topUseCases": [
                    {"id": use_id, "name": use_case_name.get(use_id, use_id), "count": count}
                    for use_id, count in use_counter.most_common(6)
                ],
                "latestVideo": matched[0] if matched else None,
                "topVideos": matched[:12],
            }
        )
    tool_summaries.sort(key=lambda t: t["videoCount"], reverse=True)

    use_summaries = []
    for use_id, name, _ in USE_CASE_DEFS:
        matched = [v for v in videos if use_id in v["useCases"]]
        use_summaries.append(
            {
                "id": use_id,
                "name": name,
                "videoCount": len(matched),
                "topVideos": sorted(matched, key=lambda v: v["date"], reverse=True)[:10],
            }
        )
    use_summaries.sort(key=lambda u: u["videoCount"], reverse=True)

    revision_groups = build_revision_groups(videos)

    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": "2026-06-18",
        "channel": {
            "name": "cooker8 by 明治クッカー",
            "url": "https://www.youtube.com/@cooker8/videos",
            "videoCount": len(videos),
        },
        "tools": tool_summaries,
        "useCases": use_summaries,
        "videos": videos,
        "revisionGroups": revision_groups,
        "seminarAngles": [
            {
                "title": "Google Workspaceで仕事のムダを削る入門",
                "target": "中小企業の管理職・バックオフィス",
                "tools": ["overview", "drive", "gmail", "chat", "calendar"],
                "pitch": "メール、ファイル、会議、日程調整のムダをなくす入口として訴求する。",
            },
            {
                "title": "AI時代のGoogle Workspace活用",
                "target": "AI活用に関心がある経営者・担当者",
                "tools": ["gemini_ai", "docs", "slides", "forms", "drive"],
                "pitch": "Gemini、NotebookLM、Workspace Studioを軸に、既存業務がどう変わるかを見せる。",
            },
            {
                "title": "現場DX・内製化ワークショップ",
                "target": "現場改善を進めたい企業",
                "tools": ["appsheet", "forms", "sheets", "looker"],
                "pitch": "フォーム、シート、AppSheetを組み合わせて小さな業務アプリを作る体験にする。",
            },
            {
                "title": "会議と情報共有の再設計",
                "target": "会議が長い、情報共有が弱い組織",
                "tools": ["meet", "docs", "chat", "sites", "drive"],
                "pitch": "会議前後の情報整理、議事録、社内ポータル、チャット運用をセットで改善する。",
            },
        ],
    }
    (DATA / "seminar-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    make_docs(tool_summaries, videos, revision_groups)
    print(json.dumps({
        "videos": len(videos),
        "tools": len(tool_summaries),
        "useCases": len(use_summaries),
        "revisionGroups": len(revision_groups),
        "out": str(OUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
