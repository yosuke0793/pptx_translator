# PPTX Translator

日本語PowerPoint（`.pptx`）を英訳し、可能な限り元のレイアウトと書式を維持した英語版PowerPointを生成するCLIツールです。

## 概要

- **通常テキスト処理**: 通常のテキストボックス、図形、表のセル、発表者ノートの日本語を抽出・文章単位へ再構成して英訳・置換。
- **画像内日本語処理**: 画像内の日本語をOCR（PaddleOCR対応）で検出し、画像から日本語を除去（背景修復/inpainting）した上で、編集可能なPowerPointテキストボックスとして元の位置に重層。
- **翻訳インターフェース**: OpenAI Chat Completions API等のLLMプロバイダおよびテスト用Dummyプロバイダを統合。用語集（Glossary）適用・キャッシュ対応。
- **レイアウトと検証**: フォントサイズの自動調整、未翻訳箇所の検査、LibreOfficeによるプレビュー画像レンダリング、`report.json` レポート出力。

---

## インストール・セットアップ

### 前提条件
- Python 3.9 以上 (推奨 3.11 以上)
- (任意) LibreOffice (`soffice`): スライドの画像化・プレビュー出力に使用
- (任意) PaddleOCR: 高精度な画像OCR検出に使用 (未導入時は自動フォールバック)

### セットアップ手順

```bash
# 仮想環境の作成と有効化
python3 -m venv .venv
source .venv/bin/activate

# パッケージと依存関係のインストール
pip install -e .
```

---

## 使い方 (CLI)

### 1. 翻訳実行 (`translate`)

```bash
pptx-translator translate input.pptx \
  --output output/translated.pptx \
  --config config.yaml \
  --glossary glossary.yaml
```

**オプション:**
- `--dry-run`: 抽出と翻訳計画の確認のみを行い、PPTXの書き換えを行いません。
- `--config`: 設定YAMLファイルの指定。
- `--glossary`: 用語集YAMLファイルの指定。

### 2. テキスト・構造抽出インスペクト (`inspect`)

```bash
pptx-translator inspect input.pptx --output inspection.json
```

### 3. プレビューレンダリング (`render`)

```bash
pptx-translator render output/translated.pptx --output-dir preview/
```

### 4. 翻訳結果のレイアウト・未翻訳検証 (`validate`)

```bash
pptx-translator validate output/translated.pptx --report report.json
```

---

## 設定と用語集の例

### 設定ファイル (`config.yaml`)

```yaml
provider: "gemini" # "dummy" または "llm" / "openai" / "gemini"（デフォルト: gemini）
model: "gemini-2.5-flash" # openaiの場合は例: "gpt-4o-mini"
ocr_lang: "japan"
ocr_confidence_threshold: 0.90
min_font_size: 8.0
inpainting_method: "telea" # "telea", "ns", "solid"
translate_notes: true
target_lang: "en"
cache_dir: ".cache"
libreoffice_path: "soffice"
log_level: "INFO"
```

### 用語集ファイル (`glossary.yaml`)

```yaml
terms:
  均質化解析: homogenization analysis
  代表体積要素: representative volume element
  有限要素法: finite element method

protected_terms:
  - FFT
  - RVE
  - Python
```

環境変数でAPIキーを設定する場合：
```bash
# OpenAIを使用する場合
export OPENAI_API_KEY="your-api-key-here"

# Geminiを使用する場合（GEMINI_API_KEYも利用可）
export GEMINI_NPI_KEY="your-gemini-api-key-here"
```

---

## 受入条件・動作テスト

プロジェクトには各種ユニットテストおよび統合テストが含まれています。

```bash
# テストの実行
pytest

# Lint・フォーマットチェック
ruff check src tests

# 型チェック
mypy src
```

---

## 制約事項 (MVP対象外)

以下の要素は検出・警告の対象となりますが、MVPでの自動置換対象外となります。

- SmartArt 内部の完全な書き換え
- 埋め込み Excel / グラフオブジェクト内部データ
- 動画 / 音声メディア
- 数式オブジェクト (`MathXML`)
- 縦書き日本語テキストの高度なレイアウト再現
- 複雑な WordArt 変換
- 超低解像度・極端な幾何歪み画像中の文字

---

## トラブルシューティング

1. **`OPENAI_API_KEY` / `GEMINI_NPI_KEY` が設定されていない**:
   - 警告ログが出力され、自動的にダミー翻訳 (`[EN] 原文`) にフォールバックします。

2. **PaddleOCRがインストールされていない**:
   - 軽量/モック検出器に切り替わり、CLI全体は正常に継続動作します。

3. **LibreOfficeが検出されない**:
   - スライドプレビュー画像のレンダリングのみスキップされ、翻訳PPTXおよび `report.json` は正常に出力されます。