# LOOP.md

# ===========================================================

# Claude Code Development Loop

# ===========================================================

Version: 2.0

Purpose:

Claude 必须严格遵循本循环完成所有开发任务。

任何阶段失败，都必须自动回退到修复阶段。

禁止跳过任何步骤。

============================================================

# Overall Loop

```
PLAN
 ↓
ANALYZE
 ↓
DESIGN
 ↓
TEST
 ↓
IMPLEMENT
 ↓
VERIFY
 ↓
FIX
 ↓
REVERIFY
 ↓
REVIEW
 ↓
COMMIT
```

任何一步失败：

立即进入：

```
FIX
 ↓
VERIFY
 ↓
REVIEW
```

直到全部通过。

============================================================

# Phase 1

## PLAN

首先：

理解需求。

必须完成：

✓ 阅读需求

✓ 阅读已有代码

✓ 阅读相关模块

✓ 理解架构

✓ 理解依赖关系

输出：

- Goal
- Scope
- Risks
- Files
- Test Plan

禁止：

直接写代码。

============================================================

# Phase 2

## ANALYZE

分析：

是否影响：

API

Database

Cache

MQ

Authentication

Authorization

Configuration

Frontend

Backend

Shared Library

输出：

Impact Analysis

============================================================

# Phase 3

## DESIGN

设计：

修改方案。

包括：

新增模块

修改模块

删除模块

数据流

接口变化

风险点

============================================================

# Phase 4

## TEST FIRST

严格执行 TDD。

首先：

编写：

Unit Test

Integration Test

Playwright Test（如果涉及 UI）

必须：

先失败。

没有 Fail：

说明测试无效。

重新编写。

============================================================

# Phase 5

## IMPLEMENT

开始实现。

原则：

只实现：

通过测试所需代码。

禁止：

增加需求外功能。

遵循：

SOLID

DRY

KISS

YAGNI

============================================================

# Phase 6

## VERIFY

执行：

Unit Test

↓

Integration Test

↓

Type Check

↓

Lint

↓

Build

↓

Playwright

全部必须通过。

============================================================

# Unit Test

检查：

✓ 正常流程

✓ 边界条件

✓ 空值

✓ Null

✓ Exception

✓ Error

✓ Permission

============================================================

# Integration Test

验证：

API

Database

Redis

MQ

Repository

Service

Third-party API

============================================================

# Browser E2E

如果：

涉及：

Web

Admin

Dashboard

React

Vue

Angular

Next

Nuxt

必须：

使用：

Playwright

真实浏览器：

Chromium

============================================================

Playwright 必须：

启动项目

等待 Ready

打开页面

检查：

HTTP

Console

Network

DOM

============================================================

执行真实用户流程：

登录

输入

点击

滚动

分页

新增

编辑

删除

上传

下载

退出

============================================================

必须验证：

页面正常

元素存在

Console 无 Error

Network 无 Failed Request

HTTP Status 正常

数据正确

Loading 消失

Toast 正确

Dialog 正确

============================================================

必须截图：

首页

主要页面

成功页面

异常页面

============================================================

任何失败：

进入：

FIX

============================================================

# Phase 7

## FIX

读取：

错误日志

Console

Network

StackTrace

Test Result

定位原因。

修改代码。

禁止：

忽略错误。

============================================================

# Phase 8

## REVERIFY

重新执行：

Unit Test

↓

Integration Test

↓

Playwright

↓

Build

↓

Lint

↓

Regression

直到：

全部 PASS。

============================================================

# Regression

重新验证：

所有已有功能。

确保：

没有新增 Bug。

============================================================

# Phase 9

## REVIEW

Review：

代码风格

命名

复杂度

重复代码

异常处理

日志

安全

性能

============================================================

Review Checklist：

□ SOLID

□ DRY

□ KISS

□ Error Handling

□ Logging

□ Security

□ Performance

□ Maintainability

============================================================

# Security Review

检查：

SQL Injection

XSS

CSRF

权限

Token

Cookie

Secret

Sensitive Data

============================================================

# Performance Review

检查：

N+1

重复请求

重复渲染

内存泄漏

死循环

慢 SQL

大对象

============================================================

# Phase 10

## COMMIT

Commit 前：

确认：

Build PASS

Lint PASS

Type PASS

Test PASS

Playwright PASS

Regression PASS

============================================================

Commit Message：

必须：

Conventional Commit

例如：

feat(user): add login page

fix(api): fix token refresh

refactor(auth): simplify middleware

test(user): improve login coverage

============================================================

# Failure Loop

任何失败：

```
Read Error
      ↓
Reason
      ↓
Fix
      ↓
Verify
      ↓
Still Fail？
      ↓
Yes────────────┐
↑              │
└──────────────┘
```

直到：

PASS。

============================================================

# Browser Acceptance Standard

最终验收：

✓ 页面可访问

✓ 页面无白屏

✓ Console 无 Error

✓ Network 全部成功

✓ JS 无异常

✓ 用户流程完成

✓ 数据正确

✓ 页面响应正常

✓ 权限正常

✓ 无新增 Bug

============================================================

# Completion Criteria

任务只有在满足以下条件后才算完成：

✓ Requirement 完成

✓ Code 完成

✓ Unit Test PASS

✓ Integration PASS

✓ Playwright PASS

✓ Regression PASS

✓ Build PASS

✓ Lint PASS

✓ Type Check PASS

✓ Security Review PASS

✓ Performance Review PASS

✓ Commit Ready

否则：

任务未完成。

============================================================

# Claude Working Principle

Claude 必须遵循：

Think First

↓

Design

↓

Test First

↓

Implement

↓

Verify

↓

Fix

↓

Verify Again

↓

Review

↓

Deliver

============================================================

Never stop at:

"代码已经完成。"

Only stop at:

"所有测试、浏览器验收、回归验证均已通过，可直接合并。"

============================================================
