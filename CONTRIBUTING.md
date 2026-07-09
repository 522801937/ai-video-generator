# 🤝 Contributing to AI Video Generator

Thanks for your interest in contributing! This document outlines how to get involved.

> 🇨🇳 [中文版见下方](#中文版)

## 🚀 Quick Contribution Guide

### Reporting Bugs
- Search [existing issues](https://github.com/522801937/ai-video-generator/issues) first
- Use the Bug Report template
- Include: OS version, Python version, steps to reproduce, error logs

### Suggesting Features
- Use the Feature Request template
- Describe the use case and why it matters
- Tag with `enhancement`

### Pull Requests
1. **Fork** the repository
2. **Create a branch**: `feat/your-feature` or `fix/your-bug`
3. **Keep it focused**: One PR = one feature or fix
4. **Write clear commit messages** (follow [Conventional Commits](https://www.conventionalcommits.org/))
5. **Test before submitting**: Make sure `python app.py` works
6. **Open a PR** with a clear description and screenshots if UI-related

## 🛠 Development Setup

```bash
git clone https://github.com/522801937/ai-video-generator.git
cd ai-video-generator
pip install -r requirements.txt
python -m playwright install chromium
python app.py
```

## 📋 Style Guide

- **Python**: Follow PEP 8, use type hints where helpful
- **TypeScript/React**: Follow existing patterns in `web/src/`
- **Comments**: Explain the "why", not the "what"
- **Naming**: Descriptive over clever

## 🎯 Priority Areas

| Area | Difficulty | Impact |
|------|-----------|--------|
| New scene types (flowchart, timeline) | Medium | High |
| Scene transition effects | Easy | High |
| Background music integration | Medium | Medium |
| i18n / multi-language UI | Medium | Medium |
| Test coverage | Easy | High |
| macOS/Linux packaging | Medium | Medium |

## 📝 Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add flowchart scene type
fix: correct subtitle timing offset
docs: update README with voice options
refactor: extract animation primitives
build: update PyInstaller exclusions
```

## 🙋 Questions?

Open a [Discussion](https://github.com/522801937/ai-video-generator/discussions) or comment on relevant issues.

---

## 🇨🇳 中文版

### 提交 Bug
- 先搜索[已有 Issues](https://github.com/522801937/ai-video-generator/issues)
- 使用 Bug Report 模板
- 包含：操作系统版本、Python 版本、复现步骤、错误日志

### 功能建议
- 使用 Feature Request 模板
- 描述使用场景和为什么重要

### 提交 PR
1. **Fork** 仓库
2. **创建分支**: `feat/功能名` 或 `fix/修复内容`
3. **保持聚焦**: 一个 PR = 一个功能或修复
4. **清晰的 commit message**（遵循 Conventional Commits）
5. **提交前测试**: 确保 `python app.py` 正常运行
6. **提交 PR**: 附上清晰描述，涉及 UI 改动请加截图

### 问题咨询
在 [Discussions](https://github.com/522801937/ai-video-generator/discussions) 发帖或在相关 Issue 下留言。
