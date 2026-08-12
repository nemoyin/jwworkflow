# COMMANDS.md

# ==========================================================

# Claude Code Command Specification

# ==========================================================

Version: 2.0

Purpose

Claude 必须优先使用本文件定义的命令。

禁止自行猜测命令。

如果项目已有 package.json、Makefile、Taskfile、Justfile、pom.xml、
build.gradle、Cargo.toml 等，应优先使用项目已有命令。

==========================================================

# General Rules

执行顺序：

Discover
↓

Install

↓

Lint

↓

Type Check

↓

Build

↓

Unit Test

↓

Integration Test

↓

Playwright

↓

Coverage

↓

Security Scan

↓

Performance

==========================================================

# Package Manager Priority

Node：

1. pnpm
2. yarn
3. npm

Python：

1. uv
2. poetry
3. pip
4. 

Go：

go

Rust：

cargo

==========================================================

# Project Discovery

Claude 首先检查：

package.json

pnpm-lock.yaml

yarn.lock

package-lock.json

pyproject.toml

requirements.txt

go.mod

Cargo.toml

pom.xml

build.gradle

build.gradle.kts

Makefile

Taskfile.yml

Justfile

docker-compose.yml

compose.yaml

==========================================================

# Install

Node

pnpm install

或：

yarn install

或：

npm install

Python

uv sync

或：

poetry install

或：

pip install -r requirements.txt

Java

./mvnw install

或：

./gradlew build

==========================================================

# Lint

Node

pnpm lint

Python

ruff check .

Java

./gradlew checkstyleMain

Go

golangci-lint run

Rust

cargo clippy

==========================================================

# Formatter

Node

pnpm format

Python

ruff format .

Java

spotlessApply

Go

gofmt

Rust

cargo fmt

==========================================================

# Type Check

Node

pnpm typecheck

或：

tsc --noEmit

Python

mypy .

==========================================================

# Build

Node

pnpm build

Python

python -m build

Java

./gradlew build

Go

go build ./...

Rust

cargo build

==========================================================

# Unit Test

Node

pnpm test

Python

pytest

Go

go test ./...

Rust

cargo test

==========================================================

# Coverage

Node

pnpm test:coverage

Python

pytest --cov

Go

go test -cover ./...

Rust

cargo llvm-cov

目标：

Coverage >=90%

==========================================================

# Integration Test

Node

pnpm test:integration

Python

pytest integration/

Java

integrationTest

Go

go test ./integration

==========================================================

# Playwright

如果发现：

playwright.config.ts

或：

@playwright/test

则：

优先执行：

pnpm playwright

否则：

pnpm exec playwright test

如果没有：

npm exec playwright test

==========================================================

Playwright 必须：

启动服务

等待 Ready

执行：

Chromium

Firefox（可选）

WebKit（可选）

==========================================================

必须验证：

Console

Network

DOM

Screenshot

==========================================================

# Docker

如果发现：

docker-compose.yml

compose.yaml

必须：

docker compose up -d

等待：

Health Check

==========================================================

# Database

如果：

存在 migration

必须：

执行：

Migration

Seed

==========================================================

# Security Scan

Node

pnpm audit

Python

pip-audit

dependency-check

==========================================================

# Performance

如果项目存在：

Lighthouse

必须：

执行：

Lighthouse

==========================================================

目标：

Performance >90

Accessibility >90

SEO >90

==========================================================

# Git

Status

git status

Diff

git diff

Branch

git branch

Commit

git commit

Push

禁止：

git push --force

==========================================================

# Commit Format

必须：

Conventional Commit

例如：

feat(auth):

fix(api):

docs:

refactor:

perf:

test:

style:

chore:

==========================================================

# Self-Healing

任何命令失败：

Claude 必须：

读取：

stderr

stdout

exit code

Stack Trace

分析原因。

自动：

修改代码

重新执行。

循环：

直到：

PASS。

==========================================================

# Retry Strategy

最多：

3 次自动修复。

仍失败：

输出：

失败原因

修复建议

阻塞项

==========================================================

# Output

Claude 每次执行命令后必须输出：

Command

Exit Code

Duration

Summary

==========================================================

例如：

Command:

pnpm test

Exit Code:

0

Duration:

12.8s

Summary:

126 Passed

0 Failed

==========================================================

Command:

pnpm playwright

Exit Code:

0

Duration:

58s

Summary:

12 Browser Tests Passed

==========================================================

# Command Priority

Claude 应优先：

Taskfile

↓

Justfile

↓

Makefile

↓

package.json scripts

↓

Framework Default Commands

↓

Manual Commands

==========================================================

# Never Do

不要：

跳过 Build

跳过 Lint

跳过 Type Check

跳过 Playwright

跳过 Coverage

跳过 Regression

==========================================================

# Completion Standard

只有当以下命令全部成功时：

✓ Install

✓ Lint

✓ Format

✓ Type Check

✓ Build

✓ Unit Test

✓ Integration Test

✓ Playwright

✓ Coverage

✓ Security

Claude 才认为：

任务完成。

==========================================================
