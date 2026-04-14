# Performing Mail Merge with the Google Docs API

| 項目 | 内容 |
|------|------|
| **動画URL** | https://www.youtube.com/watch?v=536IF8lJch4 |
| **チャンネル** | Google Workspace |
| **公開日** | 2019年06月04日 |
| **再生時間** | 3:47 |
| **再生回数** | 66,214 |

## 概要
Mail merge, having long been a feature of word processors with the help of spreadsheets or databases, is now possible with the Google Docs API. In this video, Google Developer Advocate Wesley Chun describes the flow of a mail merge system and how to use the Google Docs, Sheets, Drive, and Gmail APIs to implement one.

For the minimal mail merge sample app (mentioned in the video) → https://goo.gle/2HYkaHO 

Additional resources:

Mail merge sample repo → https://goo.gle/2WKKY6R 
Google Docs API overview → https://goo.gle/2X6egtp
Docs API documentation → https://goo.gle/2X6egtp 
Drive API documentation → https://goo.gle/2MuU9UU 
Sheets API documentation → https://goo.gle/2HZ7Qar 
Spreadsheet A1 Notation → https://goo.gle/2K24cic 
Gmail API documentation → https://goo.gle/2MtJdqy   
Build on G Suite → https://goo.gle/2Xukq6I 
Mail Merge with the Google Docs API Blog→ https://goo.gle/2KrPNeG 
G Suite Dev Show → goo.gle/JpBQ40


For the latest updates, subscribe to the G Suite Channel → 
https://goo.gle/GSuite  


Product: Google Docs API, Apps, G Suite, GSuite, Cloud, Docs, Drive, Sheets, Gmail, API, APIs; Fullname: Wesley Chun;

#CustomizingGoogleWorkspace #DocsAPI

---

## 文字起こし

メールマージはおそらく元祖
生産性キラーアプリでしょう。
こんにちは、Googleのウェスリー・チャンです。今日は、
GTA PSがどのように
メールマージを実現するのに役立つかをご紹介します。メールマージは、スプレッド
シートやその他のデータソースから値を取得し、
テンプレート化されたドキュメントに挿入します。
[音楽]
ここに表示されているフォームレターのようなテンプレートである単一のマスタードキュメントを作成し、そこから、マージされる
データでカスタマイズされた多数の類似ドキュメントを生成できます。テンプレートでは、データは
変数プレースホルダーとして表現されます。この
例では、変数名は
二重の中括弧で囲まれています。
結果は必ずしも
メールやフォームレターのみに使用されるわけではなく、顧客請求書のバッチ
生成など、あらゆる目的に使用できます。
次の
要素は、すべての変数のデータソースです。
プレーンテキストでも問題ありませんが、
この種のリレーショナルデータは、ここに表示されているような
データベースまたはスプレッドシートから取得される可能性が高くなります。
魔法は、
テンプレートをコピーして成果物を作成し、
すべてのプレースホルダーを実際のデータに置き換えるときに起こります。では、それを実行しましょう。
最初のステップは、
マスターテンプレートをコピーすることです。これは
明らかにファイル指向の操作です。そのため、
Googleドライブを使用します。  API は、
この擬似コードで示されているように、
サービスエンドポイントまたはドライブ API があり、これを
使用してファイル ID を介して元のフォーム レターをコピーし、
コピーをマージされた
フォーム レターという名前を付けます。API は新しいコピーのファイル ID を返します。
次に、いくつかのデータを取得してみましょう。
データが
スプレッドシートにあり、
Google スプレッドシート API へのサービスエンドポイントがあると仮定します。この
擬似コードは、
最初の 4 つの列、た​​とえば名前、
タイトル、会社、住所を読み込む方法を表しています。
ステップとして、シートのファイル ID が必要です。次に、
列 a から D までの適切なセル範囲を a1 表記で指定します。
対応する行が
API から返されます。悪くないですよね。さて、
パズルの最後のピースは、
新しい Google ドキュメント API のリリースにより、メール マージを実行できるようになりました。
この擬似コードのように、検索と置換コマンドを API に発行します。これは、
この場合、受信者の名前であるプレースホルダー変数を
実際の値に置き換えます。実際には、
すべてのプレースホルダーに対してそのようなリクエストの配列を作成し、
全体を一度に API に送信します。
メール マージが完了すると、
完成したレターまたは 請求書の準備ができたら、各
データ行に対して同じ手順を繰り返し、それぞれに新しいコピーを作成します。
完了したら、
完成したドキュメントをPDFとしてエクスポートし、
郵送またはメールで送信できます。さて、
クイズの時間です。ドキュメントを
PDFとしてエクスポートするには、Docs
APIとDrive APIのどちらを使うべきでしょうか？はい、ファイル
操作なので、Drive APIが
正解です。では、
PDFをメールで送信したい場合はどうでしょうか？
Gmail APIを使うのです。Gmail APIの
活用方法が分かってきましたか？
Gmail APIを使ったメッセージの送信は簡単です。
メールメッセージを作成し、差し込み印刷用のフォームレターPDFなどの添付ファイルを追加します。
次に、
Gmail APIを使用して、作成したメッセージ本文を渡して、
特別なユーザーID「me」を使ってメッセージを送信します。PDF
エクスポートやメール送信機能のない最小限のサンプルメールマージアプレットをご覧になりたい場合は、
以下の説明にあるリンクをご覧ください。まとめると、メールマージは
ワードプロセッサやスプレッドシートの重要なユースケースアプリであり、
Docs APIやその他のG Suite APIのおかげで、これまで以上に
簡単にできるようになりました。
開発者アドボケートのWesley Chunでした。
ハッピーメール あなたを統合します
