# ai-task-inbox

スマホからGitHub Issueで作業を依頼し、ChatGPTの会話から作業を進める指示箱です。**この構成は追加のAI API課金を使いません。** 現在はIssueを作るだけではAIは自動起動しません。

## 使い方

1. スマホのChatGPTから、このリポジトリにIssueを作る。件名は `【Instagram担当】...` または `【読書担当】...` とする。
2. 同じチャットで「`ai-task-inbox` のIssue #番号を進めて」と依頼する。統括の手順は [agents/coordinator.md](agents/coordinator.md)、担当別の手順は [Instagram](agents/instagram.md) と [読書](agents/reading.md) に記載している。
3. AIが結果を会話に返す。Issueへ記録する場合は公開して問題ない内容か確認する。スマホやPCから結果をレビューする。

最初の依頼は [Instagram #3](https://github.com/zhiyandaqu-bit/ai-task-inbox/issues/3) と [読書 #4](https://github.com/zhiyandaqu-bit/ai-task-inbox/issues/4)。#3にはすでに投稿草案と投稿画面の進捗があるため、続きを行う際は既存コメントから再開する。

## 料金と自動化

GitHub Actionsや有料AI APIを使うワークフローは含めない。ChatGPT Plusでこの会話を使う範囲を想定する。GitHubのIssue作成をきっかけに無人でAIを実行する機能や、別のIssueを自動で並行処理する機能はない。自動化を追加する場合は、利用条件と費用を確認してから別途設計する。

このリポジトリは公開されているため、Issue本文やコメントに個人情報、ログイン情報、書籍本文を載せない。
