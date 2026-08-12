CLAUDE.md

# =====================================================

# Project AI Development Specification

# =====================================================

本文件为 Claude Code 唯一入口文件。

Claude 在开始任何任务之前，必须首先阅读并遵循以下规范。

## Required Specifications

必须按以下顺序加载：

1. ./LOOP.md
2. ./COMMANDS.md

所有规范均具有同等优先级。

如果多个规范冲突：

优先级如下：

```
User Prompt
    ↓
CLAUDE.md
    ↓
LOOP.md
    ↓
COMMANDS.md
```

任何开发任务都必须同时遵循：

✓ CLAUDE.md

✓ LOOP.md

✓ COMMANDS.md

不得仅遵循其中某一份规范。

所有开发工作均采用：

> Test Driven Development (TDD)
> Integration Testing
> Browser E2E Validation
> Self-Healing Verification

---

## Development Workflow

所有需求必须遵循以下流程：

Requirement
↓
Analysis
↓
Design
↓
Unit Test
↓
Test Fail
↓
Implementation
↓
Unit Test Pass
↓
Refactor
↓
Integration Test
↓
Playwright E2E
↓
Regression Test
↓
Acceptance Verify
↓
Commit

禁止：

❌ 直接开始写代码

❌ 跳过测试

❌ 跳过浏览器验证

❌ 跳过回归测试

❌ 修改无关代码

❌ 提交未经验证代码

---

# Requirement Analysis

开始开发之前必须：

1. 阅读需求
2. 理解已有代码
3. 阅读相关模块
4. 分析影响范围
5. 输出开发计划

包括：

- 修改文件
- 新增文件
- 删除文件
- 风险分析
- 测试方案

---

# Coding Principles

始终遵循：

- SOLID
- DRY
- KISS
- YAGNI

禁止：

重复代码

过度设计

魔法数字

硬编码

---

# Test Driven Development

任何功能必须：

Step 1

先写测试

包括：

- Unit Test

不得：

先写实现

---

Step 2

运行测试

必须失败

(Test Fail)

如果测试未失败：

说明测试无效

重新编写

---

Step 3

实现功能

只实现：

能够通过测试

不要增加额外逻辑。

---

Step 4

重新运行：

全部 Unit Test

必须：

PASS

---

# Unit Test Requirements

新增代码必须具有：

覆盖率：

> =90%

包括：

正常流程

边界条件

异常流程

空值

非法输入

权限

错误处理

---

# Integration Test

涉及：

API

数据库

缓存

MQ

第三方接口

文件系统

均必须执行：

Integration Test

验证：

API

Service

Repository

Database

整体流程

---

# Browser End-to-End Testing

如果涉及：

Web

React

Vue

Angular

Next.js

Nuxt

后台管理

Dashboard

登录

用户操作

页面交互

必须执行：

Playwright Browser Testing

---

# Playwright Rules

Claude 必须：

启动项目

等待服务 Ready

启动 Playwright

使用真实浏览器：

Chromium

执行真实用户操作：

点击

输入

滚动

选择

上传

下载

拖拽

跳转

---

必须验证：

页面成功加载

所有关键元素存在

Console 无 Error

Console 无 Warning（严重）

Network 无 Failed Request

HTTP Status 正常

数据正常展示

Loading 正确结束

按钮可点击

表单可提交

跳转正确

权限正确

Toast 正确

Dialog 正确

---

必须截图：

首页

关键流程

提交成功

异常页面

保存失败截图

---

Playwright 验收失败：

禁止结束任务。

---

# Self-Healing Workflow

如果：

Unit Test

Integration Test

Playwright

任意失败：

Claude 必须：

分析失败日志

定位问题

修改代码

重新运行测试

重复执行

直到：

全部通过。

不得：

把失败结果交给用户自行修复。

---

# Regression Testing

每完成一个 Feature：

必须重新执行：

全部 Unit Test

全部 Integration Test

全部 Playwright

确认：

已有功能没有损坏。

---

# Code Quality

提交之前必须检查：

Lint

Format

Type Check

Build

Test

全部通过。

例如：

npm run lint

npm run typecheck

npm run build

npm run test

---

# Security Check

检查：

SQL Injection

XSS

CSRF

权限绕过

敏感信息泄露

Token

Cookie

输入校验

---

# Performance Check

检查：

重复渲染

无效请求

慢查询

内存泄漏

死循环

重复计算

---

# Logging

新增代码：

必须：

记录关键日志

禁止：

输出敏感信息：

密码

Token

Cookie

密钥

---

# Git Rules

Commit 必须符合：

Conventional Commit

例如：

feat:

fix:

refactor:

test:

docs:

perf:

style:

chore:

---

Commit Message 必须说明：

修改内容

影响范围

---

# Forbidden Operations

禁止：

删除测试

绕过测试

注释掉失败代码

忽略异常

吞掉异常

关闭类型检查

关闭 Lint

关闭 Build

---

# Required Deliverables

每完成一个任务：

Claude 必须输出：

---

## Requirement Summary

一句话描述需求

---

## Design

修改方案

---

## Changed Files

新增：

修改：

删除：

---

## Unit Test

新增测试：

覆盖率：

PASS

---

## Integration Test

执行结果：

PASS

---

## Playwright

浏览器：

URL：

测试流程：

截图：

Console：

Network：

最终结果：

PASS

---

## Regression

执行结果：

PASS

---

## Code Quality

Lint：

PASS

Type Check：

PASS

Build：

PASS

---

## Security Check

PASS

---

## Performance Check

PASS

---

## Commit Message

feat(xxx): xxxxxxxxx

---

# Working Style

Claude 应像一名资深软件工程师工作：

先思考

后编码

持续验证

自动修复

直到所有验证全部通过。

不要猜测。

不要跳步。

不要提前结束任务。

必须完成整个开发闭环。

---

# Final Goal

每一次开发任务都必须达到：

✓ 代码正确

✓ 测试通过

✓ 浏览器验收通过

✓ 无回归问题

✓ 可直接提交生产环境

========================================================
