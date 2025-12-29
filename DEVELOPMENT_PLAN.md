# Lexilux 开发计划

## 1. 项目概述

**Lexilux** 是一个统一的 LLM API 客户端库，提供 Chat、Embedding、Rerank 和 Tokenizer 功能，设计理念是"像函数一样简单调用"。

### 核心特性
- 统一的 `Usage` 和 `ResultBase` 设计
- 可调用对象模式（`chat("hi")`）
- 流式支持（streaming with usage）
- 可选 Tokenizer（依赖 transformers，可离线/在线）
- 极简 API 设计

---

## 2. 项目结构（参考 routilux）

```
lexilux/
├── lexilux/                    # 主包
│   ├── __init__.py            # 导出主要类
│   ├── usage.py                # Usage 和 ResultBase
│   ├── chat.py                 # Chat 和 ChatResult, ChatStreamChunk
│   ├── embed.py                # Embed 和 EmbedResult
│   ├── rerank.py               # Rerank 和 RerankResult
│   └── tokenizer.py            # Tokenizer 和 TokenizeResult
├── tests/                      # 测试套件
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置和 fixtures
│   ├── test_usage.py           # Usage 和 ResultBase 测试
│   ├── test_chat.py            # Chat 功能测试
│   ├── test_chat_stream.py     # Chat 流式测试
│   ├── test_embed.py            # Embed 功能测试
│   ├── test_rerank.py           # Rerank 功能测试
│   ├── test_tokenizer.py       # Tokenizer 功能测试
│   └── test_integration.py     # 集成测试
├── examples/                   # 使用示例
│   ├── README.md
│   ├── basic_chat.py
│   ├── chat_streaming.py
│   ├── embedding_demo.py
│   ├── rerank_demo.py
│   └── tokenizer_demo.py
├── docs/                       # Sphinx 文档
│   ├── source/
│   │   ├── conf.py             # Sphinx 配置（参考 routilux）
│   │   ├── index.rst
│   │   ├── introduction.rst
│   │   ├── installation.rst
│   │   ├── quickstart.rst
│   │   ├── api_reference/
│   │   │   ├── index.rst
│   │   │   ├── usage.rst
│   │   │   ├── chat.rst
│   │   │   ├── embed.rst
│   │   │   ├── rerank.rst
│   │   │   └── tokenizer.rst
│   │   └── examples/
│   │       └── index.rst
│   ├── Makefile
│   └── build/
├── scripts/                    # 发行脚本
│   └── setup_pypi.sh           # PyPI 发布脚本（参考 routilux）
├── pyproject.toml              # 项目配置（参考 routilux 风格）
├── pytest.ini                  # pytest 配置
├── Makefile                    # 常用命令（参考 routilux）
├── MANIFEST.in                 # 打包清单
├── README.md                   # 项目说明
├── LICENSE                     # Apache 2.0
├── CHANGELOG.md                # 变更日志
└── requirements.txt            # 基础依赖
    requirements-dev.txt         # 开发依赖
    requirements-docs.txt        # 文档依赖
```

---

## 3. 代码组织与命名约定

### 3.1 文件命名
- 模块文件：`snake_case.py`（如 `chat.py`, `usage.py`）
- 测试文件：`test_*.py`
- 示例文件：`*_demo.py` 或 `*_example.py`

### 3.2 类命名
- 主要类：`PascalCase`（如 `Chat`, `Usage`, `ChatResult`）
- 类型别名：`PascalCase`（如 `Role`, `MessageLike`）

### 3.3 方法/函数命名
- 公共方法：`snake_case`（如 `__call__`, `stream`）
- 私有方法：`_snake_case`（如 `_make_request`）

### 3.4 代码风格
- 使用类型注解（`typing` 模块）
- 使用 `__future__ import annotations`
- 详细的 Google/NumPy 风格 docstring
- 行长度：100 字符（与 routilux 一致）
- 使用 `TYPE_CHECKING` 避免循环导入

---

## 4. 模块设计细节

### 4.1 `lexilux/usage.py`
**职责**：定义统一的用量统计和结果基类

**类**：
- `Usage`: 用量统计类
  - `input_tokens: Optional[int]`
  - `output_tokens: Optional[int]`
  - `total_tokens: Optional[int]`
  - `details: Optional[Json]`
  
- `ResultBase`: 所有结果的基类
  - `usage: Usage`
  - `raw: Optional[Json]`

**设计要点**：
- `Usage` 字段允许 `None`（服务端可能不提供）
- `ResultBase` 确保所有结果都有 `usage` 字段

---

### 4.2 `lexilux/chat.py`
**职责**：Chat API 客户端

**类**：
- `Chat`: 可调用对象
  - `__init__`: 初始化（base_url, api_key, model, timeout_s, headers）
  - `__call__`: 非流式调用，返回 `ChatResult`
  - `stream`: 流式调用，返回 `Iterator[ChatStreamChunk]`
  
- `ChatResult(ResultBase)`: 非流式结果
  - `text: str`
  - `usage: Usage`
  - `raw: Optional[Json]`
  - `__str__`: 返回 `text`
  
- `ChatStreamChunk(ResultBase)`: 流式 chunk
  - `delta: str`
  - `done: bool`
  - `usage: Usage`（中间可能为空，最终完整）

**类型别名**：
- `Role = Literal["system", "user", "assistant", "tool"]`
- `MessageLike = Union[str, Dict[str, str]]`
- `MessagesLike = Union[str, Sequence[MessageLike]]`

**设计要点**：
- 支持 `chat("hi")`、`chat([{"role":"user","content":"..."}])`、`system="..."` 参数
- 流式 `usage` 遵循 OpenAI 习惯：`include_usage=True` 时，最终 chunk 才提供完整 usage
- 消息格式灵活转换

---

### 4.3 `lexilux/embed.py`
**职责**：Embedding API 客户端

**类**：
- `Embed`: 可调用对象
  - `__init__`: 初始化
  - `__call__`: 支持单条/批量，返回 `EmbedResult`
  
- `EmbedResult(ResultBase)`: Embedding 结果
  - `vectors: Union[Vector, List[Vector]]`
  - `usage: Usage`
  - `raw: Optional[Json]`

**类型别名**：
- `Vector = List[float]`

**设计要点**：
- 输入 `str` → 返回 `Vector`
- 输入 `List[str]` → 返回 `List[Vector]`
- 统一返回 `EmbedResult`，通过 `vectors` 字段访问

---

### 4.4 `lexilux/rerank.py`
**职责**：Rerank API 客户端

**类**：
- `Rerank`: 可调用对象
  - `__init__`: 初始化
  - `__call__`: 返回 `RerankResult`
  
- `RerankResult(ResultBase)`: Rerank 结果
  - `results: Union[Ranked, RankedWithDoc]`
  - `usage: Usage`
  - `raw: Optional[Json]`

**类型别名**：
- `Ranked = List[Tuple[int, float]]`  # (index, score)
- `RankedWithDoc = List[Tuple[int, float, str]]`  # (index, score, doc)

**设计要点**：
- `include_docs=True` 时返回 `RankedWithDoc`，否则返回 `Ranked`
- 结果按 score 降序排列

---

### 4.5 `lexilux/tokenizer.py`
**职责**：本地 Tokenizer（可选依赖 transformers）

**类**：
- `Tokenizer`: 可调用对象
  - `__init__`: 初始化（model, cache_dir, mode, revision, trust_remote_code, require_transformers）
  - `__call__`: 返回 `TokenizeResult`
  
- `TokenizeResult(ResultBase)`: Tokenize 结果
  - `input_ids: List[List[int]]`
  - `attention_mask: Optional[List[List[int]]]`
  - `usage: Usage`（至少提供 `input_tokens`）
  - `raw: Optional[Json]`

**类型别名**：
- `TokenizerMode = Literal["online", "auto_offline", "force_offline"]`

**设计要点**：
- **Lazy import**: 只在需要时导入 `transformers`
- **模式行为**：
  - `force_offline`: `local_files_only=True`，本地无则失败
  - `auto_offline`: 先尝试本地，失败才联网
  - `online`: 允许联网下载
- **依赖开关**：`require_transformers=True` 时，未安装则立即报错；`False` 时延迟到首次使用
- **extras 设计**：`pip install lexilux[tokenizer]` 安装 transformers

---

### 4.6 `lexilux/__init__.py`
**职责**：导出主要类

**导出内容**：
```python
from lexilux.usage import Usage, ResultBase
from lexilux.chat import Chat, ChatResult, ChatStreamChunk
from lexilux.embed import Embed, EmbedResult
from lexilux.rerank import Rerank, RerankResult
from lexilux.tokenizer import Tokenizer, TokenizeResult, TokenizerMode

__all__ = [
    "Usage",
    "ResultBase",
    "Chat",
    "ChatResult",
    "ChatStreamChunk",
    "Embed",
    "EmbedResult",
    "Rerank",
    "RerankResult",
    "Tokenizer",
    "TokenizeResult",
    "TokenizerMode",
]

__version__ = "0.1.0"
```

---

## 5. 依赖管理

### 5.1 基础依赖（`requirements.txt`）
```
# 最小依赖：Chat/Embed/Rerank 不需要 transformers
requests>=2.28.0
```

### 5.2 可选依赖（`pyproject.toml`）
```toml
[project.optional-dependencies]
tokenizer = [
    "transformers>=4.30.0",
    "tokenizers>=0.13.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "mypy>=0.991",
]
docs = [
    "sphinx>=5.0.0",
    "sphinx-rtd-theme>=1.0.0",
    "furo>=2024.1.0",
    "sphinx-autodoc-typehints>=1.19.0",
    "sphinx-copybutton>=0.5.0",
    "sphinx-design>=0.5.0",
]
```

### 5.3 开发依赖（`requirements-dev.txt`）
```
-r requirements.txt
-r requirements-docs.txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
black>=22.0.0
flake8>=5.0.0
mypy>=0.991
```

---

## 6. 测试策略

### 6.1 测试结构
- **单元测试**：每个模块独立测试
- **集成测试**：模拟 API 调用（使用 `pytest-mock`）
- **流式测试**：测试 streaming 行为
- **错误处理测试**：网络错误、API 错误等

### 6.2 测试文件组织
```
tests/
├── conftest.py              # Fixtures: mock_requests, sample_responses
├── test_usage.py            # Usage 和 ResultBase 测试
├── test_chat.py             # Chat 非流式测试
├── test_chat_stream.py      # Chat 流式测试
├── test_embed.py            # Embed 测试
├── test_rerank.py           # Rerank 测试
├── test_tokenizer.py        # Tokenizer 测试（mock transformers）
└── test_integration.py      # 端到端集成测试
```

### 6.3 Mock 策略
- 使用 `pytest-mock` 和 `responses` 库 mock HTTP 请求
- Tokenizer 测试：mock `transformers` 库（避免实际下载模型）
- 测试不同 API 响应格式（兼容多种服务端）

---

## 7. 文档结构（Sphinx）

### 7.1 文档组织（参考 routilux）
```
docs/source/
├── index.rst                # 首页（grid 布局）
├── introduction.rst         # 介绍
├── installation.rst         # 安装说明
├── quickstart.rst           # 快速开始
├── api_reference/           # API 参考
│   ├── index.rst
│   ├── usage.rst
│   ├── chat.rst
│   ├── embed.rst
│   ├── rerank.rst
│   └── tokenizer.rst
└── examples/                # 示例
    ├── index.rst
    ├── basic_chat.rst
    ├── chat_streaming.rst
    ├── embedding.rst
    ├── rerank.rst
    └── tokenizer.rst
```

### 7.2 Sphinx 配置（参考 routilux）
- 使用 Furo 主题
- 启用 `sphinx.ext.autodoc`, `sphinx.ext.napoleon`
- 启用 `sphinx_copybutton`, `sphinx_design`
- 配置 intersphinx（Python 标准库）

---

## 8. 配置文件

### 8.1 `pyproject.toml`（参考 routilux 风格）
- 项目元数据（name, version, description, authors）
- 依赖配置（dependencies, optional-dependencies）
- 工具配置（black, pytest, mypy, flake8）
- setuptools 配置（packages, package-data, py.typed）

### 8.2 `pytest.ini`（参考 routilux）
- 测试路径、文件模式
- 输出选项（-v, --tb=short）
- Coverage 配置

### 8.3 `Makefile`（参考 routilux）
- `install`, `dev-install`
- `test`, `test-cov`
- `lint`, `format`, `check`
- `build`, `sdist`, `wheel`
- `docs`, `html`
- `upload`, `upload-test`
- `clean`, `clean-docs`

### 8.4 `MANIFEST.in`
- 包含 README, LICENSE, CHANGELOG
- 包含文档和示例
- 排除构建产物

---

## 9. 实施步骤

### Phase 1: 项目骨架（1-2 天）
1. ✅ 创建项目目录结构
2. ✅ 复制并修改 `pyproject.toml`（从 routilux）
3. ✅ 复制并修改 `Makefile`（从 routilux）
4. ✅ 复制并修改 `pytest.ini`（从 routilux）
5. ✅ 复制并修改 `MANIFEST.in`（从 routilux）
6. ✅ 创建 `lexilux/__init__.py`（导出占位）
7. ✅ 创建基础 README.md

### Phase 2: 核心模块 - Usage（0.5 天）
1. ✅ 实现 `lexilux/usage.py`
   - `Usage` 类
   - `ResultBase` 类
2. ✅ 编写测试 `tests/test_usage.py`
3. ✅ 验证通过

### Phase 3: Chat 模块（2-3 天）
1. ✅ 实现 `lexilux/chat.py`
   - 类型别名（Role, MessageLike, MessagesLike）
   - `ChatResult` 类
   - `ChatStreamChunk` 类
   - `Chat` 类（`__init__`, `__call__`, `stream`）
   - 消息格式转换逻辑
   - HTTP 请求处理
   - 流式解析逻辑
2. ✅ 编写测试
   - `tests/test_chat.py`（非流式）
   - `tests/test_chat_stream.py`（流式）
3. ✅ 编写示例 `examples/basic_chat.py`, `examples/chat_streaming.py`
4. ✅ 验证通过

### Phase 4: Embed 模块（1-2 天）
1. ✅ 实现 `lexilux/embed.py`
   - `EmbedResult` 类
   - `Embed` 类（`__init__`, `__call__`）
   - 单条/批量处理逻辑
2. ✅ 编写测试 `tests/test_embed.py`
3. ✅ 编写示例 `examples/embedding_demo.py`
4. ✅ 验证通过

### Phase 5: Rerank 模块（1-2 天）
1. ✅ 实现 `lexilux/rerank.py`
   - `RerankResult` 类
   - `Rerank` 类（`__init__`, `__call__`）
   - 结果排序逻辑
2. ✅ 编写测试 `tests/test_rerank.py`
3. ✅ 编写示例 `examples/rerank_demo.py`
4. ✅ 验证通过

### Phase 6: Tokenizer 模块（2-3 天）
1. ✅ 实现 `lexilux/tokenizer.py`
   - `TokenizeResult` 类
   - `Tokenizer` 类（`__init__`, `__call__`）
   - Lazy import transformers
   - 三种模式实现（force_offline, auto_offline, online）
   - 缓存目录处理
2. ✅ 编写测试 `tests/test_tokenizer.py`（mock transformers）
3. ✅ 编写示例 `examples/tokenizer_demo.py`
4. ✅ 验证通过

### Phase 7: 集成与完善（1-2 天）
1. ✅ 更新 `lexilux/__init__.py`（完整导出）
2. ✅ 编写集成测试 `tests/test_integration.py`
3. ✅ 错误处理完善（网络错误、API 错误、格式错误）
4. ✅ 代码格式化（black）
5. ✅ Lint 检查（flake8）
6. ✅ 类型检查（mypy，可选）

### Phase 8: 文档（2-3 天）
1. ✅ 复制并修改 Sphinx 配置（从 routilux）
2. ✅ 编写文档
   - `introduction.rst`
   - `installation.rst`
   - `quickstart.rst`
   - API 参考（usage, chat, embed, rerank, tokenizer）
   - 示例文档
3. ✅ 构建文档验证
4. ✅ 本地预览

### Phase 9: 发布准备（1 天）
1. ✅ 编写 CHANGELOG.md
2. ✅ 完善 README.md
3. ✅ 创建 `scripts/setup_pypi.sh`
4. ✅ 测试打包（`make build`）
5. ✅ 测试安装（`pip install -e .`）
6. ✅ 最终检查清单

---

## 10. 关键设计决策

### 10.1 消息格式转换
- `chat("hi")` → `[{"role": "user", "content": "hi"}]`
- `chat([{"role": "user", "content": "..."}])` → 直接使用
- `system="..."` → 自动前置 system message

### 10.2 流式 Usage 处理
- 遵循 OpenAI 习惯：`include_usage=True` 时，最终 chunk 才提供完整 usage
- 中间 chunk 的 `usage` 字段存在但可能为空/None
- 用户需要检查 `chunk.done` 来获取最终 usage

### 10.3 Tokenizer 离线模式
- `force_offline`: 严格离线，失败即报错
- `auto_offline`: 智能回退（先本地，失败才联网）
- `online`: 允许联网

### 10.4 错误处理
- 网络错误：`requests.RequestException`
- API 错误：解析响应中的错误信息，抛出自定义异常
- 格式错误：清晰的错误消息

### 10.5 类型安全
- 使用 `typing` 模块完整类型注解
- 支持 `mypy` 类型检查
- 提供 `py.typed` 标记文件

---

## 11. 测试覆盖目标

- **单元测试覆盖率**：≥ 90%
- **关键路径**：100% 覆盖（Chat, Embed, Rerank 的核心逻辑）
- **错误处理**：覆盖所有错误场景
- **边界情况**：空输入、None 值、异常响应等

---

## 12. 后续优化（v0.2+）

- 异步支持（`async/await`）
- 重试机制（exponential backoff）
- 请求去重（idempotency）
- 批量请求优化
- 更多服务端兼容（OpenAI, Anthropic, 等）

---

## 13. 参考资源

- **routilux**: 项目结构、代码风格、文档配置
- **OpenAI Python SDK**: API 设计参考
- **transformers**: Tokenizer 使用参考
- **requests**: HTTP 请求库

---

## 14. 开发检查清单

### 代码质量
- [ ] 所有代码通过 `black` 格式化
- [ ] 所有代码通过 `flake8` 检查
- [ ] 所有代码通过 `mypy` 类型检查（可选）
- [ ] 所有函数/类有完整 docstring
- [ ] 所有公共 API 有类型注解

### 测试
- [ ] 所有测试通过
- [ ] 测试覆盖率 ≥ 90%
- [ ] 包含单元测试、集成测试
- [ ] 包含错误场景测试

### 文档
- [ ] README.md 完整
- [ ] API 文档完整
- [ ] 示例代码可运行
- [ ] 文档可本地构建

### 发布
- [ ] `pyproject.toml` 配置正确
- [ ] `MANIFEST.in` 包含必要文件
- [ ] 版本号正确
- [ ] 可以成功打包
- [ ] 可以成功安装

---

**预计总开发时间**：10-15 天

**开始实施**：按照 Phase 1 → Phase 9 的顺序逐步实施

