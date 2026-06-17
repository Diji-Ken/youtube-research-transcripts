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


LECTURE_MODULE_DEFS = [
    {
        "id": "workspace_intro",
        "name": "Google Workspace導入・全体設計",
        "keywords": ["Google Workspace", "有償版", "無償版", "導入", "全体", "基本", "完全解説", "良さ", "ユーザーの本音"],
        "tools": ["overview", "admin_security", "drive"],
    },
    {
        "id": "ai_work",
        "name": "AI/Gemini/NotebookLM活用",
        "keywords": ["AI", "Gemini", "NotebookLM", "Workspace Studio", "Gem", "Canvas", "プロンプト", "Veo", "要約"],
        "tools": ["gemini_ai", "docs", "slides", "forms", "drive", "chrome"],
    },
    {
        "id": "communication",
        "name": "メール・チャット・コミュニケーション",
        "keywords": ["Gmail", "メール", "Google Chat", "チャット", "問い合わせ", "情報共有", "コミュニケーション"],
        "tools": ["gmail", "chat", "keep_tasks"],
    },
    {
        "id": "meeting",
        "name": "会議・議事録・ファシリテーション",
        "keywords": ["会議", "議事録", "Meet", "ファシリテーション", "ミーティング", "ホワイトボード", "コンパニオン"],
        "tools": ["meet", "docs", "calendar", "chat"],
    },
    {
        "id": "file_docs",
        "name": "ファイル・文書・ペーパーレス",
        "keywords": ["ドライブ", "共有ドライブ", "ファイル", "権限", "ドキュメント", "Word", "契約", "紙", "ペーパーレス"],
        "tools": ["drive", "docs", "admin_security"],
    },
    {
        "id": "data_sheets",
        "name": "スプレッドシート・集計・自動化",
        "keywords": ["スプレッドシート", "Query", "IMPORTRANGE", "関数", "集計", "ピボット", "チェックリスト", "請求", "入金"],
        "tools": ["sheets", "forms", "looker"],
    },
    {
        "id": "forms_tests",
        "name": "フォーム・アンケート・テスト",
        "keywords": ["Googleフォーム", "フォーム", "アンケート", "理解度テスト", "申請", "回答", "テスト"],
        "tools": ["forms", "sheets", "gemini_ai"],
    },
    {
        "id": "appsheet",
        "name": "AppSheet・現場アプリ内製",
        "keywords": ["AppSheet", "アプリ", "現場", "内製", "出退勤", "営業", "在庫", "ノーコード"],
        "tools": ["appsheet", "sheets", "forms"],
    },
    {
        "id": "dashboard",
        "name": "可視化・ダッシュボード・Looker",
        "keywords": ["Looker", "データポータル", "ダッシュボード", "レポート", "可視化", "地図", "Googleマップ"],
        "tools": ["looker", "sheets"],
    },
    {
        "id": "portal_training",
        "name": "社内ポータル・マニュアル・研修",
        "keywords": ["Googleサイト", "サイト", "社内ポータル", "マニュアル", "研修", "教育", "掲示板", "名刺"],
        "tools": ["sites", "docs", "drive", "forms"],
    },
    {
        "id": "admin_security",
        "name": "管理・権限・セキュリティ",
        "keywords": ["管理者", "管理コンソール", "セキュリティ", "権限", "アカウント", "グループ", "ウイルス", "共有設定"],
        "tools": ["admin_security", "drive", "overview"],
    },
    {
        "id": "dx_management",
        "name": "DX推進・内製化・マネジメント",
        "keywords": ["DX", "業務改善", "内製", "外注", "マネジメント", "部下", "上司", "社長", "SNS", "生産性"],
        "tools": ["business_dx", "overview", "chat", "appsheet"],
    },
]


FEATURE_RULES = [
    ("Gmailのラベル・検索・ショートカットでメール処理を高速化する", ["Gmail", "ラベル", "検索", "ショートカット"], ["gmail"]),
    ("GmailとGoogleカレンダー/Meetをつなげて予定・会議化する", ["Gmail", "カレンダー", "Meet", "予定"], ["gmail", "calendar", "meet"]),
    ("問い合わせ窓口・チームアドレスをGoogleグループ/Chatで運用する", ["問い合わせ", "Googleグループ", "グループ", "チャット", "チームアドレス"], ["gmail", "chat", "admin_security"]),
    ("Google Chatのスペースでタスク・通知・会議前後のやり取りを集約する", ["Google Chat", "スペース", "タスク", "通知", "会議"], ["chat"]),
    ("Chat運用ルールを決めて情報共有漏れを減らす", ["チャット", "情報共有", "ルール", "運用", "コミュニケーション"], ["chat", "business_dx"]),
    ("Meetの画面共有・コンパニオンモード・リアルタイム要約を使う", ["Meet", "画面共有", "コンパニオン", "リアルタイム", "要約"], ["meet"]),
    ("会議を報告ではなく意思決定と次アクション整理の場に変える", ["会議", "意思決定", "次アクション", "ファシリテーション", "議事録"], ["meet", "docs", "business_dx"]),
    ("Googleカレンダーで予定・会議室・リソースを管理する", ["カレンダー", "予定", "会議室", "リソース", "予約"], ["calendar"]),
    ("日程調整・予約スケジュールで候補日提示を自動化する", ["日程調整", "予約", "候補日", "Calendly", "アイテマス"], ["calendar"]),
    ("Googleドライブの共有・権限・検索・リンク運用を整える", ["ドライブ", "共有", "権限", "検索", "リンク", "フォルダ"], ["drive"]),
    ("GoogleドライブをAI時代の社内ナレッジ/脳として整備する", ["ドライブ", "脳", "AI", "ナレッジ", "NotebookLM"], ["drive", "gemini_ai"]),
    ("契約書・紙文書・社内資料をDrive中心のペーパーレス運用にする", ["契約", "紙", "文書", "ドライブ", "ペーパーレス"], ["drive", "docs"]),
    ("Googleドキュメントで共同編集・コメント・添削・議事録を作る", ["ドキュメント", "共同編集", "コメント", "添削", "議事録"], ["docs"]),
    ("Wordとの違いを理解してクラウド文書作成に移行する", ["Word", "ドキュメント", "違い", "共同編集"], ["docs"]),
    ("定例会議メモやマニュアル文書を使い回す", ["定例", "会議メモ", "マニュアル", "テンプレート", "使い回し"], ["docs", "drive"]),
    ("スプレッドシートでチェックリスト・進捗・ステータス管理表を作る", ["スプレッドシート", "チェックリスト", "進捗", "ステータス", "管理表"], ["sheets"]),
    ("請求・入金・営業・SNSなどの業務管理シートを作る", ["請求", "入金", "営業", "SNS", "管理", "スプレッドシート"], ["sheets"]),
    ("Query/IMPORTRANGE/ピボット/条件付き書式で集計を自動化する", ["Query", "IMPORTRANGE", "ピボット", "条件付き書式", "集計"], ["sheets"]),
    ("フォーム・スライド・LookerとSheetsを連携して入力から資料化までつなげる", ["フォーム", "スライド", "Looker", "連携", "スプレッドシート"], ["sheets", "forms", "slides", "looker"]),
    ("Googleスライドで共同編集資料・テンプレート・リンク付き資料を作る", ["スライド", "共同編集", "テンプレート", "リンク", "資料作成"], ["slides"]),
    ("スプレッドシートのデータをスライド資料へ反映する", ["スプレッドシート", "スライド", "リンク", "更新", "資料"], ["slides", "sheets"]),
    ("Gemini/Gemを使ってスライド・提案資料を作る", ["Gemini", "Gem", "スライド", "提案資料", "資料作成"], ["slides", "gemini_ai"]),
    ("Googleフォームで問い合わせ・アンケート・申請・理解度テストを作る", ["フォーム", "問い合わせ", "アンケート", "申請", "理解度テスト"], ["forms"]),
    ("フォーム回答をSheetsに集計し、通知・レポート・採点に回す", ["フォーム", "回答", "スプレッドシート", "通知", "採点", "レポート"], ["forms", "sheets"]),
    ("GeminiとGoogleフォームでクイズ/テスト作成を効率化する", ["Gemini", "フォーム", "クイズ", "テスト", "理解度"], ["forms", "gemini_ai"]),
    ("Googleサイトで社内ポータル・マニュアル・研修サイトを作る", ["Googleサイト", "社内ポータル", "マニュアル", "研修", "掲示板"], ["sites"]),
    ("SitesにDrive/Docsを埋め込んで情報の入口を作る", ["サイト", "ドライブ", "ドキュメント", "埋め込み", "入口"], ["sites", "drive", "docs"]),
    ("AppSheetで在庫・勤怠・営業・事故報告などの現場アプリを作る", ["AppSheet", "在庫", "出退勤", "勤怠", "営業", "事故報告"], ["appsheet"]),
    ("AppSheetのデータ・ビュー・自動通知・ワークフローを設計する", ["AppSheet", "データ", "ビュー", "通知", "ワークフロー", "Automation"], ["appsheet"]),
    ("AppSheetで外注依存から現場主導の内製化へ移行する", ["AppSheet", "外注", "内製", "現場", "業務アプリ"], ["appsheet", "business_dx"]),
    ("Looker StudioでSheetsや業務データをダッシュボード化する", ["Looker", "ダッシュボード", "スプレッドシート", "可視化"], ["looker", "sheets"]),
    ("Looker Studioで営業実績・地図・定例レポートを自動更新する", ["Looker", "営業", "地図", "Googleマップ", "レポート"], ["looker"]),
    ("Chromeの検索・拡張機能・ショートカットを業務効率化に使う", ["Chrome", "検索", "拡張機能", "ショートカット"], ["chrome"]),
    ("Gemini in Chromeでブラウザ作業をAI補助に変える", ["Gemini in Chrome", "Chrome", "AI", "ブラウザ"], ["chrome", "gemini_ai"]),
    ("Chromebookの教育・端末管理・セキュリティ運用を扱う", ["Chromebook", "教育", "端末", "管理", "セキュリティ"], ["chrome", "admin_security"]),
    ("Keep/ToDo/Tasksでメモ・チェックリスト・リマインダーを管理する", ["Keep", "ToDo", "Tasks", "タスク", "リマインダー", "メモ"], ["keep_tasks"]),
    ("管理コンソールでアカウント・グループ・共有設定を管理する", ["管理コンソール", "アカウント", "グループ", "共有設定", "権限"], ["admin_security"]),
    ("Workspace標準機能でウイルス対策・情報漏えい対策を考える", ["セキュリティ", "ウイルス", "情報漏えい", "管理者"], ["admin_security"]),
    ("Geminiサイドパネルでメール・文書・スライド・シート作業を支援する", ["Gemini", "サイドパネル", "メール", "ドキュメント", "スライド", "シート"], ["gemini_ai"]),
    ("NotebookLMに社内資料・制度情報・補助金情報を読ませて調査する", ["NotebookLM", "社内資料", "補助金", "年末調整", "制度"], ["gemini_ai"]),
    ("Gemini Canvas/Workspace Studio/Gemで小さな業務アプリや補助ツールを作る", ["Gemini Canvas", "Workspace Studio", "Gem", "アプリ", "ツール"], ["gemini_ai"]),
    ("AIに任せる前に業務要件と判断基準を定義する", ["AI", "要件定義", "判断基準", "業務", "指示"], ["gemini_ai", "business_dx"]),
    ("DXをツール導入ではなく業務フロー・定着・社内発信として設計する", ["DX", "業務フロー", "定着", "社内発信", "導入"], ["business_dx", "overview"]),
    ("外注依存から内製化へ移行する判断軸を整理する", ["外注", "内製", "コンサル", "担当者", "チーム"], ["business_dx"]),
    ("SNS・発信業務を内製化して運用の型を作る", ["SNS", "発信", "内製", "投稿", "運用"], ["business_dx"]),
    ("上司/部下/チームのコミュニケーションとマネジメントを改善する", ["上司", "部下", "マネジメント", "コミュニケーション", "期待値"], ["business_dx", "chat"]),
]


DELIVERABLE_RULES = [
    ("在庫管理アプリ/在庫管理表", ["在庫"], ["appsheet", "sheets"]),
    ("TODOリスト/タスク管理表", ["TODO", "ToDo", "タスク", "チェックリスト"], ["keep_tasks", "chat", "sheets"]),
    ("請求書自動発行/請求・入金管理", ["請求", "入金"], ["sheets", "docs"]),
    ("ガントチャート/進捗管理表", ["ガント", "進捗"], ["sheets"]),
    ("会議室・備品・予定管理", ["会議室", "備品", "予定管理"], ["calendar", "sheets", "appsheet"]),
    ("休日・定休日カレンダー", ["休日", "定休日", "土日祝"], ["calendar", "sheets"]),
    ("申請承認フロー", ["申請", "承認"], ["forms", "appsheet", "sheets"]),
    ("備品管理/QR管理", ["備品", "QR"], ["appsheet", "sheets"]),
    ("出退勤/勤怠管理アプリ", ["出退勤", "勤怠"], ["appsheet", "sheets"]),
    ("事故報告/現場報告アプリ", ["事故報告", "報告"], ["appsheet", "forms"]),
    ("営業実績管理/売上管理", ["営業", "売上", "実績"], ["sheets", "appsheet", "looker"]),
    ("SNS運用管理表", ["SNS", "投稿"], ["sheets", "business_dx"]),
    ("マニュアル/研修サイト", ["マニュアル", "研修"], ["sites", "docs", "drive", "forms"]),
    ("社内ポータル/掲示板", ["社内ポータル", "掲示板"], ["sites", "drive"]),
    ("議事録/会議メモ", ["議事録", "会議メモ"], ["docs", "meet", "gemini_ai"]),
    ("理解度テスト/確認テスト", ["理解度", "テスト", "クイズ"], ["forms", "gemini_ai"]),
    ("アンケート集計/回答レポート", ["アンケート", "回答"], ["forms", "sheets", "looker"]),
    ("Looker Studioダッシュボード", ["Looker", "ダッシュボード", "可視化"], ["looker"]),
    ("予約受付/日程調整ページ", ["予約", "日程調整"], ["calendar", "forms"]),
    ("契約フロー/契約書管理", ["契約"], ["drive", "docs"]),
    ("見積書/契約書/PDF資料", ["見積", "契約書", "PDF"], ["docs", "drive", "slides"]),
    ("問い合わせ窓口/チーム受付", ["問い合わせ"], ["gmail", "chat", "forms"]),
    ("AI議事録/要約メモ", ["AI", "要約", "議事録"], ["gemini_ai", "meet", "docs"]),
    ("プレゼン/提案資料", ["スライド", "プレゼン", "提案資料"], ["slides", "gemini_ai"]),
    ("Workspace導入・運用ルール", ["導入", "運用ルール", "有償版", "無償版"], ["overview", "admin_security", "business_dx"]),
]


CASE_RULES = [
    ("明治クッカー/牛乳屋の現場改善事例として使える", ["牛乳屋", "明治クッカー", "クッカー"]),
    ("大企業事例として社内展開・利用実態の話に使える", ["ANA", "サンゲツ", "TBS", "潜入"]),
    ("学校/教育現場でのWorkspace・Chromebook活用事例として使える", ["学校", "教育", "Chromebook"]),
    ("中小企業・老舗企業のDX/内製化事例として使える", ["中小企業", "老舗", "社長", "現場"]),
    ("クリエイティブ/制作業務のAI・Workspace活用事例として使える", ["クリエイティブ", "FMX", "Adobe"]),
]


NON_TOOL_RULES = [
    ("ツール導入前に、何を減らしたいか・何を見える化したいかを定義する", ["業務", "要件定義", "目的", "課題"]),
    ("導入後に使われるよう、運用ルール・責任者・更新頻度を決める", ["運用", "ルール", "定着", "責任者"]),
    ("外注だけに任せず、社内で直せる範囲を増やす内製化の設計が重要", ["外注", "内製", "自分たち"]),
    ("コミュニケーションはツールではなく期待値・発信先・返信ルールまで設計する", ["コミュニケーション", "期待値", "返信", "発信"]),
    ("上司・部下・チームの動き方を変えるマネジメント講義に転用できる", ["上司", "部下", "マネジメント"]),
    ("AI活用ではプロンプト以前に、入力する社内データと判断基準の整理が必要", ["AI", "判断基準", "社内データ", "プロンプト"]),
    ("情報共有では入口を一つにし、Drive/Docs/Sites/Chatの役割を分ける", ["情報共有", "入口", "Drive", "Docs", "Sites", "Chat"]),
    ("権限・共有・アカウント管理を後回しにすると情報漏えいや属人化の原因になる", ["権限", "共有", "アカウント", "情報漏えい"]),
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


def unique(items: list[str], limit: int | None = None) -> list[str]:
    seen = set()
    result = []
    for item in items:
        item = normalize_text(item)
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
        if limit and len(result) >= limit:
            break
    return result


def contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords if keyword)


def keyword_stats(text: str, keywords: list[str]) -> tuple[int, int]:
    lower = text.lower()
    distinct = 0
    total = 0
    for keyword in keywords:
        if not keyword:
            continue
        count = lower.count(keyword.lower())
        if count:
            distinct += 1
            total += count
    return distinct, total


def rule_matches(
    row: dict,
    rules: list[tuple],
    video_tools: list[str] | None = None,
    limit: int = 8,
    min_distinct: int = 1,
    min_total: int = 1,
) -> list[str]:
    title_blob = row.get("title", "")
    transcript = row.get("transcript", "")[:12000]
    matched = []
    for rule in rules:
        label = rule[0]
        keywords = rule[1]
        tools = rule[2] if len(rule) >= 3 else []
        title_distinct, _ = keyword_stats(title_blob, keywords)
        transcript_distinct, transcript_total = keyword_stats(transcript, keywords)
        strong_title = title_distinct > 0
        enough_body = transcript_distinct >= min_distinct or transcript_total >= min_total
        if not strong_title and not enough_body:
            continue
        if tools and video_tools:
            has_related_tool = bool(set(tools).intersection(video_tools))
            if not has_related_tool and not strong_title:
                continue
        matched.append(label)
    return unique(matched, limit)


def prioritize_title_matches(row: dict, labels: list[str], rules: list[tuple]) -> list[str]:
    keywords_by_label = {rule[0]: rule[1] for rule in rules}
    title = row.get("title", "")
    lower_title = title.lower()

    def score(label: str) -> tuple[int, int, int]:
        keywords = keywords_by_label.get(label, [])
        distinct, total = keyword_stats(title, keywords)
        longest = max((len(keyword) for keyword in keywords if keyword and keyword.lower() in lower_title), default=0)
        return distinct, total, longest

    return sorted(labels, key=score, reverse=True)


def infer_lecture_module(row: dict, video: dict) -> dict:
    scores = []
    blob = " ".join([row.get("title", ""), row.get("description", ""), row.get("transcript", "")])
    for module in LECTURE_MODULE_DEFS:
        score = 0
        if video["primaryTool"] in module["tools"]:
            score += 28
        score += len(set(video["tools"]).intersection(module["tools"])) * 8
        score += count_keywords(row.get("title", ""), module["keywords"]) * 18
        score += min(count_keywords(blob, module["keywords"]), 10)
        if module["id"] == "dx_management" and video["primaryTool"] == "business_dx":
            score += 10
        scores.append((score, module))
    scores.sort(key=lambda item: item[0], reverse=True)
    module = scores[0][1] if scores and scores[0][0] > 0 else LECTURE_MODULE_DEFS[-1]
    return {"id": module["id"], "name": module["name"]}


def infer_lecture_type(row: dict) -> str:
    title = row.get("title", "")
    if contains_any(title, ["最新", "アップデート", "新機能", "リリース"]):
        return "最新アップデート講義"
    if contains_any(title, ["完全版", "決定版", "保存版", "基本", "入門", "初心者", "新人"]):
        return "基本・全体像講義"
    if contains_any(title, ["実演", "作り方", "作成", "作る", "ステップ", "構築", "やってみた", "3分", "5分", "10分"]):
        return "ハンズオン講義"
    if contains_any(title, ["事例", "潜入", "大公開", "リアル", "本音", "牛乳屋", "ANA", "サンゲツ", "TBS"]):
        return "事例研究"
    if contains_any(title, ["研修", "講義", "セミナー", "教育", "理解度テスト"]):
        return "研修・ワークショップ設計"
    if contains_any(title, ["なぜ", "理由", "注意", "NG", "問題", "限界", "罠", "やめ", "本当に"]):
        return "考え方・注意点講義"
    return "実務活用講義"


def infer_difficulty(row: dict, primary: str) -> str:
    title = row.get("title", "")
    title_blob = title
    advanced_blob = " ".join([title_blob, row.get("transcript", "")[:1800]])
    if primary == "admin_security" or contains_any(title_blob, ["管理者", "管理コンソール", "セキュリティ", "権限", "アカウント", "Googleグループ"]):
        return "管理者・管理職"
    if primary == "business_dx" or contains_any(title_blob, ["マネジメント", "上司", "部下", "社長", "経営", "組織"]):
        return "経営・管理職"
    if primary in {"appsheet", "looker"} or contains_any(advanced_blob, ["Query", "IMPORTRANGE", "AppSheet", "Looker", "Workspace Studio", "Gemini Canvas", "Automation", "API"]):
        return "応用"
    if contains_any(title, ["初心者", "新人", "基本", "入門", "完全版", "保存版", "はじめて"]):
        return "入門"
    return "実務"


def infer_audience(video: dict) -> str:
    primary = video["primaryTool"]
    use_cases = set(video["useCases"])
    if primary == "admin_security":
        return "情シス・管理者・経営層"
    if primary == "business_dx":
        return "経営者・管理職・DX推進担当"
    if primary == "appsheet" or "field" in use_cases:
        return "現場リーダー・業務改善担当"
    if primary in {"sheets", "forms", "looker"} or "data" in use_cases:
        return "バックオフィス・集計担当・DX担当"
    if primary in {"meet", "chat", "gmail", "calendar"}:
        return "管理職・チームリーダー・全社員"
    if primary in {"sites", "docs", "drive"}:
        return "総務・教育担当・情報共有担当"
    if primary == "gemini_ai":
        return "AI活用推進担当・管理職・実務担当"
    return "Google Workspace利用者"


def infer_deliverables(row: dict, video: dict) -> list[str]:
    deliverables = rule_matches(row, DELIVERABLE_RULES, [video["primaryTool"]], limit=6, min_distinct=2, min_total=4)
    strong_deliverables = []
    for label, keywords, *_ in DELIVERABLE_RULES:
        distinct, _ = keyword_stats(row.get("title", ""), keywords)
        required = 1 if len(keywords) == 1 else 2
        if distinct >= required:
            strong_deliverables.append(label)
    fallback = {
        "overview": ["Workspace導入・運用ルール"],
        "gemini_ai": ["AI活用手順書/プロンプト例", "要約メモ/調査メモ"],
        "gmail": ["メール処理ルール/問い合わせ窓口"],
        "chat": ["Chatスペース設計/通知フロー"],
        "meet": ["会議運営ルール/議事録テンプレート"],
        "calendar": ["日程調整・予約運用"],
        "drive": ["共有ドライブ設計/権限表"],
        "docs": ["議事録/マニュアル文書"],
        "sheets": ["業務管理シート/集計表"],
        "slides": ["提案資料/研修スライド"],
        "forms": ["入力フォーム/アンケート/テスト"],
        "sites": ["社内ポータル/マニュアルサイト"],
        "appsheet": ["現場業務アプリ"],
        "looker": ["業務ダッシュボード/定例レポート"],
        "chrome": ["ブラウザ作業効率化チェックリスト"],
        "keep_tasks": ["タスク/メモ管理ルール"],
        "admin_security": ["アカウント・権限管理表"],
        "business_dx": ["DX推進ロードマップ/業務改善テーマ一覧"],
    }
    fallback_items = fallback.get(video["primaryTool"], [])
    if strong_deliverables:
        return unique(strong_deliverables + deliverables + fallback_items, 6)
    return unique(fallback_items + deliverables, 6)


def infer_procedure(row: dict, video: dict, deliverables: list[str]) -> list[str]:
    primary = video["primaryTool"]
    procedures = {
        "overview": ["現状の業務課題と利用中ツールを棚卸しする", "Workspace各ツールの役割を業務フローに割り当てる", "共有・権限・運用ルールを決めて小さく試す"],
        "gemini_ai": ["対象業務と入力データを決める", "Gemini/NotebookLMに渡す情報と指示を整える", "出力を確認し、判断基準や社内ルールに合わせて修正する"],
        "gmail": ["受信トレイの処理ルールを決める", "ラベル・検索・ショートカット・署名を設定する", "必要に応じてChat/Calendar/グループへ接続する"],
        "chat": ["スペースの目的と参加者を決める", "投稿ルール・通知・タスクの扱いを決める", "会議前後や問い合わせ対応の流れに組み込む"],
        "meet": ["会議の目的・議題・資料を事前に揃える", "Meet/Docs/Chatを使って議事録と決定事項を残す", "次アクションを担当者・期限つきで共有する"],
        "calendar": ["予定種別と共有範囲を決める", "予約枠・会議室・Meetリンクなどを設定する", "チームで予定を確認し、抜け漏れを減らす"],
        "drive": ["フォルダ/共有ドライブの設計を決める", "権限・命名・検索しやすい置き方を整える", "Docs/Sites/NotebookLMなどの入口として活用する"],
        "docs": ["文書の目的とテンプレートを決める", "共同編集・コメント・議事録の運用を決める", "Drive/Sites/Meetとつないで再利用する"],
        "sheets": ["入力項目とマスターデータを決める", "関数・Query・IMPORTRANGE・ピボットで集計する", "フォーム/Looker/Slidesと連携して見える化する"],
        "slides": ["資料の用途とテンプレートを決める", "リンク・画像・データ連携で更新しやすくする", "共同編集と発表導線を確認する"],
        "forms": ["設問・分岐・必須項目を設計する", "回答先のスプレッドシートと通知を設定する", "集計・採点・レポート化まで確認する"],
        "sites": ["利用者と入口に置く情報を決める", "Docs/Drive/Formsなどを埋め込んでページを作る", "検索性・更新担当・掲載ルールを整える"],
        "appsheet": ["対象業務と現場入力項目を決める", "Sheetsなどのデータ構造を整える", "ビュー・アクション・通知を作り、現場で試す"],
        "looker": ["見たい指標とデータ元を決める", "グラフ・表・フィルタを配置する", "定例レポートとして自動更新・共有する"],
        "chrome": ["日常のブラウザ作業を洗い出す", "検索・拡張機能・ショートカット・AI補助を設定する", "チームで使う標準手順にする"],
        "keep_tasks": ["メモ/タスクの入口を決める", "チェックリスト・リマインダー・共有方法を整える", "Chat/Calendarと連携して漏れを減らす"],
        "admin_security": ["アカウント・グループ・共有範囲を棚卸しする", "管理コンソールで権限とセキュリティを設定する", "退職/異動/外部共有の運用ルールを決める"],
        "business_dx": ["現場の困りごとを業務フローで分解する", "ツール・担当者・データの流れを決める", "小さな改善を内製し、定着ルールまで作る"],
    }
    steps = procedures.get(primary, ["業務課題を整理する", "使うツールとデータを決める", "小さく作って現場で試す"])
    if deliverables:
        steps = [f"{deliverables[0]}の目的と利用者を決める"] + steps[1:]
    return steps[:4]


def infer_recommended_use(row: dict, video: dict, lecture_type: str) -> str:
    title = row.get("title", "")
    if video["transcriptChars"] < 800:
        return "短尺・告知寄りの可能性があるため、補足確認用"
    if lecture_type == "最新アップデート講義":
        return "最新情報・既存講義の差し替え確認"
    if lecture_type == "基本・全体像講義":
        return "ツール別講義の主教材候補"
    if lecture_type == "ハンズオン講義":
        return "デモ/ワークショップの実演パート"
    if lecture_type == "事例研究":
        return "導入事例・社内説得パート"
    if lecture_type == "考え方・注意点講義":
        return "導入前の注意点・失敗回避パート"
    if contains_any(title, ["研修", "講義", "セミナー"]):
        return "研修設計の参考"
    return "補足教材・検索参照用"


def build_lecture_candidate(row: dict, video: dict) -> dict:
    lecture_type = infer_lecture_type(row)
    module = infer_lecture_module(row, video)
    deliverables = infer_deliverables(row, video)
    features = rule_matches(row, FEATURE_RULES, video["tools"][:2], limit=10, min_distinct=2, min_total=3)
    features = prioritize_title_matches(row, features, FEATURE_RULES)
    if not features:
        primary_def = next(tool for tool in TOOL_DEFS if tool["id"] == video["primaryTool"])
        features = primary_def["capabilities"][:2]
    case_points = rule_matches(row, CASE_RULES, limit=4)
    non_tool_points = rule_matches(row, NON_TOOL_RULES, limit=5, min_distinct=2, min_total=3)
    procedure = infer_procedure(row, video, deliverables)

    outcomes = [
        f"{video['primaryToolName']}を使って業務で何ができるかを成果物ベースで説明できる",
    ]
    if deliverables:
        outcomes.append(f"受講者が「{deliverables[0]}」の作り方・使いどころをイメージできる")
    if features:
        outcomes.append(f"講義内で「{features[0]}」を具体例として扱える")
    if non_tool_points:
        outcomes.append(f"ツール以外の論点として「{non_tool_points[0]}」を扱える")

    title_base = deliverables[0] if deliverables else video["primaryToolName"]
    return {
        "title": f"{video['primaryToolName']}で{title_base}を作る/運用する講義",
        "module": module,
        "type": lecture_type,
        "difficulty": infer_difficulty(row, video["primaryTool"]),
        "audience": infer_audience(video),
        "recommendedUse": infer_recommended_use(row, video, lecture_type),
        "outcomes": unique(outcomes, 4),
        "deliverables": deliverables,
        "features": features,
        "procedure": procedure,
        "casePoints": case_points,
        "nonToolPoints": non_tool_points,
        "evidence": extract_snippets(row, next(m["keywords"] for m in LECTURE_MODULE_DEFS if m["id"] == module["id"]), 3),
    }


def build_lecture_summaries(videos: list[dict]) -> dict:
    modules = []
    for module in LECTURE_MODULE_DEFS:
        matched = [v for v in videos if v["lecture"]["module"]["id"] == module["id"]]
        tool_counter = Counter(v["primaryToolName"] for v in matched)
        type_counter = Counter(v["lecture"]["type"] for v in matched)
        modules.append(
            {
                "id": module["id"],
                "name": module["name"],
                "videoCount": len(matched),
                "ratio": round(len(matched) / len(videos) * 100, 1) if videos else 0,
                "topTools": [{"name": name, "count": count} for name, count in tool_counter.most_common(6)],
                "topTypes": [{"name": name, "count": count} for name, count in type_counter.most_common(5)],
                "topVideos": sorted(matched, key=lambda v: v["date"], reverse=True)[:10],
            }
        )
    modules.sort(key=lambda item: item["videoCount"], reverse=True)

    feature_counter = Counter()
    feature_tools = defaultdict(Counter)
    feature_videos = defaultdict(list)
    for video in videos:
        for feature in video["lecture"]["features"]:
            feature_counter[feature] += 1
            feature_tools[feature][video["primaryToolName"]] += 1
            if len(feature_videos[feature]) < 8:
                feature_videos[feature].append(video)

    feature_catalog = []
    for feature, count in feature_counter.most_common():
        feature_catalog.append(
            {
                "name": feature,
                "count": count,
                "ratio": round(count / len(videos) * 100, 1) if videos else 0,
                "tools": [{"name": name, "count": tool_count} for name, tool_count in feature_tools[feature].most_common(5)],
                "videos": feature_videos[feature],
            }
        )

    type_counter = Counter(v["lecture"]["type"] for v in videos)
    difficulty_counter = Counter(v["lecture"]["difficulty"] for v in videos)
    audience_counter = Counter(v["lecture"]["audience"] for v in videos)

    return {
        "lectureModules": modules,
        "lectureTypes": [{"name": name, "count": count, "ratio": round(count / len(videos) * 100, 1)} for name, count in type_counter.most_common()],
        "lectureDifficulties": [{"name": name, "count": count, "ratio": round(count / len(videos) * 100, 1)} for name, count in difficulty_counter.most_common()],
        "lectureAudiences": [{"name": name, "count": count, "ratio": round(count / len(videos) * 100, 1)} for name, count in audience_counter.most_common()],
        "featureCatalog": feature_catalog,
    }


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


def make_docs(tool_summaries: list[dict], videos: list[dict], revision_groups: list[dict], lecture_summaries: dict) -> None:
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

    lines = [
        "# 講義候補一覧・全560本対応",
        "",
        "cooker8 by 明治クッカーの現行公開動画560本を、講義化する前提で1本ずつ整理したものです。",
        "各動画について、講義候補、扱える機能、作る/見せる成果物、手順、事例・注意点を付与しています。",
        "",
        "## 講義モジュール別比率",
        "",
    ]
    for module in lecture_summaries["lectureModules"]:
        lines.append(f"- {module['name']}: {module['videoCount']}本 ({module['ratio']}%)")
    lines.extend(["", "## 講義タイプ別比率", ""])
    for item in lecture_summaries["lectureTypes"]:
        lines.append(f"- {item['name']}: {item['count']}本 ({item['ratio']}%)")
    lines.extend(["", "## 難易度/対象別比率", ""])
    for item in lecture_summaries["lectureDifficulties"]:
        lines.append(f"- {item['name']}: {item['count']}本 ({item['ratio']}%)")
    lines.extend(["", "## 動画別講義候補", ""])
    for video in sorted(videos, key=lambda v: v["date"], reverse=True):
        lecture = video["lecture"]
        lines.append(f"### {video['date']} {video['title']}")
        lines.append("")
        lines.append(f"- YouTube: {video['url']}")
        lines.append(f"- 主ツール: {video['primaryToolName']}")
        lines.append(f"- 講義モジュール: {lecture['module']['name']}")
        lines.append(f"- 講義タイプ: {lecture['type']}")
        lines.append(f"- 難易度: {lecture['difficulty']}")
        lines.append(f"- 想定対象: {lecture['audience']}")
        lines.append(f"- 使いどころ: {lecture['recommendedUse']}")
        lines.append(f"- 講義候補: {lecture['title']}")
        lines.append("- 学習ゴール:")
        for outcome in lecture["outcomes"]:
            lines.append(f"  - {outcome}")
        lines.append("- 作る/見せる成果物:")
        for deliverable in lecture["deliverables"]:
            lines.append(f"  - {deliverable}")
        lines.append("- 扱う機能・操作:")
        for feature in lecture["features"]:
            lines.append(f"  - {feature}")
        lines.append("- 進め方:")
        for step in lecture["procedure"]:
            lines.append(f"  - {step}")
        if lecture["casePoints"]:
            lines.append("- 事例として使える観点:")
            for point in lecture["casePoints"]:
                lines.append(f"  - {point}")
        if lecture["nonToolPoints"]:
            lines.append("- ツール以外の重要論点:")
            for point in lecture["nonToolPoints"]:
                lines.append(f"  - {point}")
        lines.append("")
    (DOCS / "lecture_candidates.md").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        "# 機能カタログ",
        "",
        "文字起こし全体から、講義で扱える機能・操作・考え方を抽出した一覧です。",
        "",
    ]
    for item in lecture_summaries["featureCatalog"]:
        tools = "、".join(f"{tool['name']} {tool['count']}本" for tool in item["tools"])
        lines.append(f"## {item['name']} ({item['count']}本 / {item['ratio']}%)")
        lines.append("")
        lines.append(f"- 主なツール: {tools}")
        lines.append("- 代表動画:")
        for video in item["videos"][:8]:
            lines.append(f"  - {video['date']} [{video['title']}]({video['url']})")
        lines.append("")
    (DOCS / "feature_catalog.md").write_text("\n".join(lines), encoding="utf-8")


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
        video["lecture"] = build_lecture_candidate(row, video)
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
    lecture_summaries = build_lecture_summaries(videos)

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
        **lecture_summaries,
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
    make_docs(tool_summaries, videos, revision_groups, lecture_summaries)
    print(json.dumps({
        "videos": len(videos),
        "tools": len(tool_summaries),
        "useCases": len(use_summaries),
        "revisionGroups": len(revision_groups),
        "lectureModules": len(lecture_summaries["lectureModules"]),
        "featureCatalog": len(lecture_summaries["featureCatalog"]),
        "out": str(OUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
