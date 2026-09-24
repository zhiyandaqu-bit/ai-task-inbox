# ai-task-inbox

スマホからGitHub Issueで作業を依頼し、ChatGPTの会話から作業を進める指示箱です。追加のAI API課金を使いません。

## 使い方

1. [新しいIssue](https://github.com/zhiyandaqu-bit/ai-task-inbox/issues/new/choose)を作り、件名の先頭を `【Instagram担当】`、`【読書担当】`、`【LINEスタンプ担当】` のいずれかにする。依頼内容と完了条件を書く。
2. Issueが作成されるとGitHub Actionsが受付コメントを付け、担当ラベルを付ける。これは受付だけで、AIによる本文の作業はまだ始まっていない。
3. ChatGPTで「`ai-task-inbox の Issue #番号を進めて`」と依頼する。統括の手順は [agents/coordinator.md](agents/coordinator.md)、担当別の手順は [Instagram](agents/instagram.md)、[読書](agents/reading.md)、[LINEスタンプ](agents/line-sticker.md) にある。
4. 会話で成果物を確認する。Issueへの記録が必要なら、公開してよい内容だけをコメントする。

既存の依頼は [Instagram #3](https://github.com/zhiyandaqu-bit/ai-task-inbox/issues/3) と [読書 #4](https://github.com/zhiyandaqu-bit/ai-task-inbox/issues/4)。#3は既存コメントから続ける。LINEスタンプ制作には [詳細テンプレート](templates/line-sticker-issue.md) も使える。

## 自動化と費用

`.github/workflows/issue-intake.yml` は新しいIssueの受付と分類だけを行う。対象はリポジトリ所有者が作成したIssueに限る。既存Issueへの遡及実行はない。公開リポジトリの標準GitHubランナーで動き、有料AI APIや外部の認証情報を使わない。GitHub Actionsが無効な場合や、リポジトリのトークン権限が制限されている場合は受付が動かない。Actions画面で実行結果を確認する。

IssueだけでAIを無人起動して成果物を作る機能はない。現行のChatGPT Plus会話をGitHub Actionsから無人起動する設定もない。担当エージェントの手順ファイルは、チャットで依頼されたときに参照するもの。

公開リポジトリのIssue本文やコメントには個人情報、ログイン情報、書籍本文を載せない。

## LINEスタンプ担当

最初に基準となる1枚を作り、会話で承認された後に残りへ展開する。完成ファイルは申請前に検査できる。

```bash
python3 scripts/validate_line_stickers.py path/to/sticker-directory
python3 scripts/validate_line_stickers.py path/to/stickers.zip
```

検査対象はファイル名、PNG/APNG形式、寸法、容量、透過、APNGの宣言フレーム数と実フレーム数、ZIPの破損。実際のLINE Creators Marketの最新条件も申請時に確認する。
