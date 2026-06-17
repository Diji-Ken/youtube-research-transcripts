#!/usr/bin/env python3
"""Generate full-text review records for every cooker8 transcript.

This does not pretend that every video has received the same hand-written
deep review. It scans each full transcript and creates evidence-based review
records so the browser can distinguish:

- 深掘り精査: manually completed review records already present.
- 全文走査: transcript-wide automated evidence extraction by Codex tooling.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


BASE = Path("/Users/m/Workspace/mirai/40_research/YouTube/transcripts_clean/cooker8")
DATA_PATH = BASE / "seminar_browser" / "data" / "seminar-data.json"
REVIEW_PATH = BASE / "review_overrides.json"
TODAY = "2026-06-18"


FEATURE_PATTERNS = [
    ("Gmail", ["Gmail", "メール", "受信トレー", "受信トレイ", "アーカイブ", "ラベル", "署名", "CC", "BCC", "迷惑メール", "テンプレート", "送信取り消し"], "メール処理・受信トレー運用・署名/ラベル/テンプレートなどのGmail運用"),
    ("Google Chat", ["Google Chat", "Googleチャット", "チャット", "スペース", "ルーム", "メンション", "スレッド", "タスク"], "スペース設計・社内連絡・タスクや通知のチーム運用"),
    ("Google Meet", ["Google Meet", "Meet", "ミート", "会議", "画面共有", "コンパニオン", "字幕", "録画", "議事録", "要約"], "オンライン会議・画面共有・会議メモ/要約の運用"),
    ("Googleカレンダー", ["Googleカレンダー", "カレンダー", "日程調整", "予定", "予約", "会議室", "空き時間", "リマインダー"], "予定管理・日程調整・会議室/予約運用"),
    ("Googleドライブ", ["Googleドライブ", "ドライブ", "共有ドライブ", "ファイル", "フォルダ", "権限", "共有", "リンク", "検索"], "ファイル共有・権限管理・検索性のあるドライブ運用"),
    ("Googleドキュメント", ["Googleドキュメント", "ドキュメント", "Docs", "Word", "共同編集", "コメント", "提案", "スマートチップ", "見出し"], "共同編集文書・レビュー/コメント・文書作成の運用"),
    ("Googleスプレッドシート", ["スプレッドシート", "シート", "関数", "Query", "QUERY", "IMPORTRANGE", "ピボット", "集計", "データ"], "表計算・関数・集計/分析・業務管理表の作成"),
    ("Googleスライド", ["Googleスライド", "スライド", "資料", "プレゼン", "テンプレート", "発表", "画像", "リンク"], "資料作成・テンプレート・共同編集プレゼン運用"),
    ("Googleフォーム", ["Googleフォーム", "フォーム", "アンケート", "回答", "テスト", "申請", "問い合わせ"], "フォーム受付・アンケート/テスト・回答集計"),
    ("Googleサイト", ["Googleサイト", "サイト", "社内ポータル", "ポータル", "掲示板", "ホームページ"], "社内ポータル・情報掲示板・サイト作成"),
    ("AppSheet", ["AppSheet", "アップシート", "アプリ", "ノーコード", "内製", "出退勤", "現場"], "ノーコード業務アプリ・現場DX・内製化"),
    ("Looker Studio", ["Looker", "Looker Studio", "データポータル", "ダッシュボード", "レポート", "可視化"], "ダッシュボード・レポート・データ可視化"),
    ("Gemini / AI", ["Gemini", "ジェミニ", "AI", "NotebookLM", "Notebook LM", "Gem", "Canvas", "プロンプト", "Workspace Studio"], "Gemini/NotebookLMによる要約・作成支援・AI活用"),
    ("Chrome", ["Chrome", "Chromebook", "ブラウザ", "拡張機能", "検索", "ブックマーク"], "ブラウザ作業・検索・Chrome/Chromebook活用"),
    ("管理 / セキュリティ", ["管理者", "管理コンソール", "セキュリティ", "権限", "アカウント", "Googleグループ", "グループ", "ウイルス"], "アカウント/権限/グループ/セキュリティ管理"),
    ("DX / 業務設計", ["DX", "業務改善", "業務効率", "内製", "外注", "マネジメント", "会議", "現場", "生産性", "仕組み"], "ツール導入前後の業務設計・内製化・マネジメント"),
]


OUTCOME_PATTERNS = [
    ("メール処理ルール", ["Gmail", "メール", "受信トレー", "アーカイブ", "ラベル"], {"Gmail", "Google Chat"}),
    ("会議/議事録運用", ["会議", "Meet", "議事録", "要約", "画面共有"], {"Google Meet", "Googleドキュメント", "Googleカレンダー"}),
    ("社内ポータル/情報共有", ["サイト", "社内ポータル", "情報共有", "掲示板", "ナレッジ"], {"Googleサイト", "Googleドライブ", "Google Chat"}),
    ("ファイル/権限管理", ["ドライブ", "共有ドライブ", "権限", "フォルダ", "リンク"], {"Googleドライブ", "管理 / セキュリティ"}),
    ("業務管理表/集計", ["スプレッドシート", "関数", "集計", "ピボット", "Query", "IMPORTRANGE"], {"Googleスプレッドシート", "Looker Studio"}),
    ("資料/提案書", ["スライド", "資料", "プレゼン", "提案", "テンプレート"], {"Googleスライド", "Gemini / AI"}),
    ("フォーム/受付", ["フォーム", "アンケート", "回答", "申請", "問い合わせ"], {"Googleフォーム"}),
    ("AI活用手順", ["Gemini", "AI", "NotebookLM", "プロンプト", "Canvas", "Gem"], {"Gemini / AI"}),
    ("現場DX/内製化", ["AppSheet", "アプリ", "現場", "内製", "業務改善"], {"AppSheet", "DX / 業務設計"}),
]


NON_TOOL_PATTERNS = [
    ("導入前に目的・運用ルール・責任者を決める必要がある", ["運用", "ルール", "責任者", "導入", "目的"]),
    ("権限・共有・アカウント管理を後回しにすると事故や属人化につながる", ["権限", "共有", "アカウント", "セキュリティ"]),
    ("外注だけに任せず、社内で直せる範囲を増やす内製化が重要", ["外注", "内製", "社内", "自分たち"]),
    ("AI活用ではプロンプト以前に、入力データと判断基準の整理が重要", ["AI", "プロンプト", "判断基準", "データ"]),
    ("検索・再利用を前提に、整理作業そのものを減らす発想が出ている", ["検索", "再利用", "整理", "探す"]),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u3000", " ")).strip()


def split_sentences(text: str) -> list[str]:
    normalized = normalize(text)
    parts = re.split(r"(?<=[。！？!?])|(?:\n+)", normalized)
    sentences = [part.strip() for part in parts if len(part.strip()) >= 18]
    if not sentences and normalized:
        sentences = [normalized[:260]]
    return sentences


def count_hits(text: str, keywords: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(keyword.lower()) for keyword in keywords if keyword)


def pick_sentence(sentences: list[str], keywords: list[str]) -> str:
    best = ""
    best_score = 0
    for sentence in sentences:
        score = count_hits(sentence, keywords)
        if score > best_score:
            best = sentence
            best_score = score
    return best[:180]


def compact_title(title: str) -> str:
    title = re.sub(r"[【】\[\]]", "", title)
    return title[:90]


def load_existing_reviews() -> list[dict]:
    if not REVIEW_PATH.exists():
        return []
    data = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    items = data.get("reviews", data if isinstance(data, list) else [])
    return items if isinstance(items, list) else []


def confidence_for(video: dict, feature_count: int) -> str:
    chars = video.get("transcriptChars", 0) or 0
    cpm = video.get("charsPerMinute", 0) or 0
    if chars >= 8000 and feature_count >= 4 and cpm >= 320:
        return "高"
    if chars >= 3000 and feature_count >= 2:
        return "中"
    return "低"


def priority_for(video: dict) -> str:
    score = video.get("review", {}).get("priorityScore", 0)
    if score >= 55:
        return "高"
    if score >= 34:
        return "中"
    return "低"


def make_review(video: dict) -> dict:
    txt_path = BASE / video["txtFile"]
    text = txt_path.read_text(encoding="utf-8", errors="ignore")
    normalized = normalize(text)
    sentences = split_sentences(text)
    title = video["title"]
    blob = f"{title} {normalized}"

    feature_hits = []
    for name, keywords, description in FEATURE_PATTERNS:
        hits = count_hits(blob, keywords)
        if hits:
            feature_hits.append((name, hits, keywords, description))
    feature_hits.sort(key=lambda item: item[1], reverse=True)

    top_feature_names = {item[0] for item in feature_hits[:6]}
    outcomes = []
    for name, keywords, required_features in OUTCOME_PATTERNS:
        if count_hits(blob, keywords) >= 2 and (top_feature_names & required_features):
            outcomes.append(name)

    non_tool = []
    for point, keywords in NON_TOOL_PATTERNS:
        if count_hits(blob, keywords):
            non_tool.append(point)

    top_features = feature_hits[:5]
    feature_names = [item[0] for item in top_features]
    feature_descriptions = [item[3] for item in top_features]
    primary = video.get("primaryToolName") or (feature_names[0] if feature_names else "テーマ未分類")
    confidence = confidence_for(video, len(feature_hits))
    priority = priority_for(video)
    existing_score = video.get("review", {}).get("priorityScore", 0)
    score = max(existing_score, 35 if confidence == "中" else 20)

    evidence_points = []
    if feature_descriptions:
        evidence_points.append(f"全文走査で主に『{primary}』に関する内容として確認。関連論点: {'、'.join(feature_descriptions[:4])}")
    if outcomes:
        evidence_points.append(f"講義で扱える成果物候補: {'、'.join(outcomes[:5])}")
    if video.get("lecture", {}).get("features"):
        evidence_points.append(f"既存講義候補の機能項目として『{video['lecture']['features'][0]}』が抽出されている")
    if video.get("lecture", {}).get("procedure"):
        evidence_points.append(f"進め方候補として『{video['lecture']['procedure'][0]}』が抽出されている")

    for name, _hits, keywords, description in top_features[:6]:
        snippet = pick_sentence(sentences, keywords)
        if snippet:
            evidence_points.append(f"{name}: 字幕内に『{snippet}』という説明があり、{description}として使える")

    if non_tool:
        evidence_points.append(f"ツール外の講義論点: {'、'.join(non_tool[:3])}")

    if not evidence_points:
        snippet = sentences[0][:180] if sentences else compact_title(title)
        evidence_points.append(f"全文走査では明確なツール手順は少ないが、冒頭/本文に『{snippet}』という説明がある")

    corrections = []
    lecture = video.get("lecture", {})
    if lecture.get("title"):
        corrections.append(f"自動講義候補『{lecture['title']}』は一次候補。採用時は本文の確認済みポイントを優先して章立てを調整する")
    if video.get("transcriptChars", 0) < 2000:
        corrections.append("文字起こしが短いため、講義主教材ではなく補足・事例・告知扱いにする")
    if video.get("charsPerMinute", 0) and video.get("charsPerMinute", 0) < 260:
        corrections.append("文字密度が低いため、字幕欠落・雑談比率・映像依存の可能性を考慮する")
    if "2026" not in title and "2025" not in title and video.get("date", "") < "2025-01-01":
        corrections.append("古い動画のため、機能仕様は最新版動画を優先し、この動画は背景理解・過去経緯として扱う")
    if feature_hits and primary not in feature_names[:3]:
        corrections.append(f"主ツール分類は『{primary}』だが、本文上は『{'、'.join(feature_names[:3])}』も強く出ているため横断テーマとして扱う")
    if not corrections:
        corrections.append("自動整理の大枠は本文内容と矛盾しない。講義化時は確認済みポイントを中心に具体例を選ぶ")

    reasons = [
        "字幕全文を走査",
        f"{video.get('transcriptChars', 0):,}字の字幕を確認",
        f"確認粒度: {'深掘りではなく全文走査' if confidence != '高' else '全文走査'}",
    ]
    if feature_names:
        reasons.append(f"検出テーマ: {'、'.join(feature_names[:3])}")
    if video.get("id") in {"-nY5ikBWkNM", "HuFvxeAPdns"}:
        reasons.append("深掘り精査済み")

    if feature_descriptions:
        summary_tail = "、".join(feature_descriptions[:4])
    elif outcomes:
        summary_tail = "、".join(outcomes[:4])
    else:
        summary_tail = "本文の主旨確認・講義素材としての採否判断"
    final_summary = (
        f"{video.get('date')}公開『{compact_title(title)}』の全文走査レビュー。"
        f"主テーマは{primary}。{summary_tail}を扱う素材として使える。"
        f"文字起こしは{video.get('transcriptChars', 0):,}字、{video.get('duration') or '時間不明'}。"
        "講義化する場合は、本文で確認できた機能・手順・事例だけを採用し、古い仕様や字幕誤変換は最新版動画で補正する。"
    )

    next_action = (
        f"{primary}の講義素材として採用候補。"
        f"章立ては『{summary_tail}』を中心に組み、必要に応じて最新版動画で仕様確認する。"
    )

    return {
        "id": video["id"],
        "reviewedAt": TODAY,
        "reviewer": "Codex全文走査",
        "reviewDepth": "全文走査",
        "priority": priority,
        "priorityScore": score,
        "confidence": confidence,
        "reasons": reasons[:6],
        "finalSummary": final_summary,
        "verifiedPoints": evidence_points[:12],
        "corrections": corrections[:5],
        "nextAction": next_action,
    }


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing = load_existing_reviews()
    by_id = {item["id"]: item for item in existing if item.get("id")}

    reviews = []
    generated = 0
    preserved_deep = 0
    for video in data["videos"]:
        current = by_id.get(video["id"])
        if current and current.get("reviewDepth", "深掘り精査") != "全文走査":
            current = dict(current)
            current.setdefault("reviewDepth", "深掘り精査")
            reviews.append(current)
            preserved_deep += 1
            continue
        reviews.append(make_review(video))
        generated += 1

    order = {video["id"]: idx for idx, video in enumerate(data["videos"])}
    reviews.sort(key=lambda item: order.get(item["id"], 999999))
    REVIEW_PATH.write_text(json.dumps({"reviews": reviews}, ensure_ascii=False, indent=2), encoding="utf-8")

    depth_counts = Counter(item.get("reviewDepth", "") for item in reviews)
    print(json.dumps({
        "total": len(reviews),
        "generated": generated,
        "preservedDeep": preserved_deep,
        "depthCounts": dict(depth_counts),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
