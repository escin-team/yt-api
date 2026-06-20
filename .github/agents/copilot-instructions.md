# YTSearch Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-08

## Active Technologies

- Python 3.12 (pyproject 要求 >=3.12) + FastAPI、Pydantic、requests、anyio、redis；HTML/JSON 解析沿用 ytInitialData 抽取與 `continuation` token 迭代，不新增額外解析套件 (003-playlist-metadata)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12 (pyproject 要求 >=3.12): Follow standard conventions

## Recent Changes

- 003-playlist-metadata: Added Python 3.12 (pyproject 要求 >=3.12) + FastAPI、Pydantic、requests、anyio、redis；HTML/JSON 解析沿用 ytInitialData 抽取與 `continuation` token 迭代，不新增額外解析套件

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
