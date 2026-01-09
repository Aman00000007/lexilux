# Continue Chat 改进计划

## 一、背景分析

### 1.1 重要说明：auto_history 已完全移除

**lexilux v2.0 已经完全移除了 `auto_history` 功能**。根据 CHANGELOG.md：

- ✅ **已移除**：`Chat.__init__()` 中的 `auto_history` 参数
- ✅ **已移除**：`Chat.get_history()` 方法
- ✅ **已移除**：`Chat.clear_history()` 方法
- ✅ **已移除**：所有自动历史管理功能

**当前设计**：所有历史管理都是**显式的**，必须手动创建 `ChatHistory` 实例并传递给所有方法。

```python
# v2.0 的正确用法
history = ChatHistory()
result = chat("Hello", history=history)
if result.finish_reason == "length":
    full_result = ChatContinue.continue_request(chat, result, history=history)
```

**注意**：docdance 代码中仍在使用 `auto_history=True`，这说明：
1. docdance 可能使用的是旧版本的 lexilux（v0.5.x）
2. 或者他们的代码还没有更新到 v2.0
3. 需要迁移到显式历史管理

### 1.2 docdance 为什么自己实现 continue chat？

通过分析 `docdance/docdance/routines/llm_caller/routine.py`，我们发现 docdance team 自己实现了 `_continue_with_streaming_impl` 方法，尽管 lexilux 已经提供了 `ChatContinue.continue_request_stream()`。

**原因分析：**

1. **历史原因**：docdance 的实现可能是在 lexilux v2.0 添加流式 continue 功能之前开发的。从 `LEXILUX_STREAMING_CONTINUE_FEATURE_REQUEST.md` 可以看出，他们曾经提出过这个需求。

2. **特殊需求**：
   - **请求延迟控制**：在多次 continue 之间添加随机延迟（1-2秒），避免请求过快被 API 拒绝
   - **自定义历史构建**：手动构建 continue 历史（原始 prompt + 已生成文本 + continue prompt）
   - **进度提示**：提供详细的进度信息（"继续生成 1/3"）
   - **错误恢复**：如果 continue 失败，返回已合并的部分结果，而不是抛出异常

3. **lexilux 当前实现的不足**：
   - ✅ 已有流式 continue 功能（`continue_request_stream()`）
   - ✅ 已有显式历史管理（v2.0 要求显式传递 history）
   - ❌ 缺少请求延迟控制
   - ❌ 缺少进度回调/提示机制
   - ❌ 错误处理可能不够灵活（失败时直接抛异常）

### 1.2 是否需要实现 docdance 的做法？

**结论：部分需要，但应该以更通用的方式实现。**

**应该实现的功能：**
1. ✅ **进度跟踪**：提供回调或事件机制，让用户知道 continue 的进度
2. ✅ **请求延迟控制**：可配置的延迟机制，避免请求过快
3. ✅ **更灵活的错误处理**：允许部分失败时返回已合并的结果

**不应该直接移植的功能：**
1. ❌ **手动历史构建**：lexilux 的自动历史管理已经足够好，不需要手动构建
2. ❌ **硬编码的延迟逻辑**：应该通过配置参数控制，而不是硬编码

## 二、改进计划

### 2.1 优先级 1：进度跟踪机制

**需求：**
- 用户需要知道 continue 的进度（第几次 continue，总共几次）
- 对于长时间运行的 continue 操作，需要实时反馈

**实现方案：**

#### 方案 A：回调函数（推荐）
```python
def on_continue_progress(
    continue_count: int,
    max_continues: int,
    current_result: ChatResult,
    all_results: list[ChatResult]
) -> None:
    """Continue 进度回调"""
    print(f"🔄 继续生成 {continue_count}/{max_continues}...")

full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=3,
    on_progress=on_continue_progress  # 新增参数
)
```

#### 方案 B：事件/信号机制
```python
# 使用事件系统（更复杂，但更灵活）
continue_iterator = ChatContinue.continue_request_stream(
    chat,
    result,
    history=history,
    max_continues=3,
    emit_events=True  # 发出进度事件
)

for chunk in continue_iterator:
    if chunk.event == "continue_start":
        print(f"🔄 开始第 {chunk.continue_count} 次继续...")
    print(chunk.delta, end="")
```

**推荐：方案 A（回调函数）**，因为：
- 简单直观
- 不需要改变现有 API 结构
- 向后兼容（可选参数）

**实现细节：**
- 在 `continue_request()` 和 `continue_request_stream()` 中添加 `on_progress` 参数
- 回调函数在每次 continue 开始时调用
- 回调函数可以访问当前结果和所有结果列表

### 2.2 优先级 2：请求延迟控制

**需求：**
- 在多次 continue 请求之间添加延迟，避免请求过快被 API 拒绝
- 延迟应该是可配置的

**实现方案：**

```python
full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=3,
    continue_delay=1.0,  # 固定延迟（秒）
    # 或
    continue_delay_range=(1.0, 2.0),  # 随机延迟范围（秒）
)
```

**实现细节：**
- 添加 `continue_delay` 参数（支持固定延迟或随机延迟范围）
- 只在非第一次 continue 时添加延迟（第一次 continue 不需要延迟）
- 默认值为 0（不延迟），保持向后兼容

### 2.3 优先级 3：Helper 方法

**需求：**
- 提供便捷方法检查是否需要 continue
- 简化常见使用模式

**实现方案：**

```python
# 检查是否需要 continue
if ChatContinue.needs_continue(result):
    full_result = ChatContinue.continue_request(...)

# 或者更简洁的链式调用
full_result = ChatContinue.ensure_complete(
    chat,
    result,
    history=history,
    max_continues=3
)
```

**实现细节：**
- `ChatContinue.needs_continue(result: ChatResult) -> bool`：检查是否需要 continue
- `ChatContinue.ensure_complete(...)`：确保结果完整（类似 `chat.complete()`，但更灵活）

### 2.4 优先级 4：Token 预算估算

**需求：**
- 帮助用户估算需要多少次 continue 才能完成响应
- 基于当前输出长度和 max_tokens 限制

**实现方案：**

```python
# 估算需要多少次 continue
estimate = ChatContinue.estimate_continues_needed(
    current_length=len(result.text),
    desired_length=5000,  # 期望的响应长度
    max_tokens_per_request=100,  # 每次请求的 max_tokens
    avg_chars_per_token=4  # 平均每个 token 的字符数
)
print(f"预计需要 {estimate.continues_needed} 次 continue")
print(f"预计总 token 数: {estimate.total_tokens}")

# 使用估算结果
full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=estimate.continues_needed + 2  # 加一些缓冲
)
```

**实现细节：**
- 创建一个 `ContinueEstimate` 数据类
- 提供 `estimate_continues_needed()` 静态方法
- 考虑不同模型的 token 编码差异（可以通过 Tokenizer 获取更准确的估算）

### 2.5 优先级 5：更灵活的错误处理

**需求：**
- 当 continue 失败时，可以选择返回已合并的部分结果，而不是直接抛异常
- 对于部分失败的情况，提供更灵活的处理方式

**实现方案：**

```python
full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=3,
    on_error="return_partial",  # 或 "raise"（默认）
    # 或使用回调
    on_error_callback=lambda error, partial_result: {
        "action": "return_partial",  # 或 "raise", "retry"
        "result": partial_result
    }
)
```

**实现细节：**
- 添加 `on_error` 参数，支持 "raise"（默认）或 "return_partial"
- 或者使用 `on_error_callback` 提供更灵活的错误处理
- 在 continue 失败时，如果配置了返回部分结果，则返回已合并的结果

### 2.6 优先级 6：Continue 提示词定制化

**需求：**
- 更灵活的 continue 提示词定制
- 支持基于上下文的动态提示词

**实现方案：**

```python
# 方案 A：回调函数生成提示词
def generate_continue_prompt(
    continue_count: int,
    max_continues: int,
    current_text: str,
    original_prompt: str
) -> str:
    if continue_count == 1:
        return "请继续完成你的回答。"
    else:
        return f"请继续完成你的回答（第 {continue_count} 次继续）。"

full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=3,
    continue_prompt=generate_continue_prompt  # 支持函数
)

# 方案 B：模板字符串
full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=3,
    continue_prompt_template="请继续完成你的回答（第 {continue_count}/{max_continues} 次继续）。"
)
```

**实现细节：**
- `continue_prompt` 参数支持字符串或可调用对象
- 如果是可调用对象，传入上下文信息（continue_count, max_continues, current_text 等）
- 保持向后兼容（字符串仍然有效）

## 三、实施路线图

### Phase 1：核心功能（1-2 周）
1. ✅ 进度跟踪机制（回调函数）
2. ✅ 请求延迟控制
3. ✅ Helper 方法（`needs_continue`, `ensure_complete`）

### Phase 2：增强功能（1 周）
4. ✅ Token 预算估算
5. ✅ 更灵活的错误处理

### Phase 3：高级功能（1 周）
6. ✅ Continue 提示词定制化

## 四、API 设计示例

### 4.1 完整的 API 设计

```python
class ChatContinue:
    @staticmethod
    def needs_continue(result: ChatResult) -> bool:
        """检查是否需要 continue"""
        return result.finish_reason == "length"
    
    @staticmethod
    def estimate_continues_needed(
        current_length: int,
        desired_length: int,
        max_tokens_per_request: int,
        avg_chars_per_token: float = 4.0
    ) -> ContinueEstimate:
        """估算需要多少次 continue"""
        ...
    
    @staticmethod
    def continue_request(
        chat: Chat,
        last_result: ChatResult,
        *,
        history: ChatHistory | None = None,
        add_continue_prompt: bool = True,
        continue_prompt: str | Callable = "continue",
        max_continues: int = 1,
        auto_merge: bool = True,
        continue_delay: float | tuple[float, float] = 0.0,  # 新增
        on_progress: Callable | None = None,  # 新增
        on_error: str = "raise",  # 新增： "raise" 或 "return_partial"
        **params: Any,
    ) -> ChatResult | list[ChatResult]:
        """
        Continue generation request (enhanced version).
        
        Args:
            ...
            continue_delay: 继续请求之间的延迟（秒）。可以是固定值或 (min, max) 元组（随机延迟）
            on_progress: 进度回调函数，接收 (continue_count, max_continues, current_result, all_results)
            on_error: 错误处理策略，"raise"（默认）或 "return_partial"
            ...
        """
        ...
    
    @staticmethod
    def ensure_complete(
        chat: Chat,
        result: ChatResult,
        *,
        history: ChatHistory,
        max_continues: int = 3,
        **kwargs: Any,
    ) -> ChatResult:
        """
        确保结果完整（如果被截断则自动 continue）。
        
        这是 continue_request 的便捷包装，类似于 chat.complete()。
        """
        if not ChatContinue.needs_continue(result):
            return result
        return ChatContinue.continue_request(
            chat, result, history=history, max_continues=max_continues, **kwargs
        )
```

### 4.2 使用示例

```python
# 示例 1：带进度跟踪和延迟控制
def on_progress(count, max_count, current, all_results):
    print(f"🔄 继续生成 {count}/{max_count}... ({len(current.text)} 字符)")

full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=5,
    continue_delay=(1.0, 2.0),  # 随机延迟 1-2 秒
    on_progress=on_progress
)

# 示例 2：使用 ensure_complete（更简洁）
full_result = ChatContinue.ensure_complete(
    chat,
    result,
    history=history,
    max_continues=3,
    continue_delay=1.0,
    on_progress=lambda c, m, curr, all: print(f"继续 {c}/{m}")
)

# 示例 3：Token 预算估算
estimate = ChatContinue.estimate_continues_needed(
    current_length=len(result.text),
    desired_length=5000,
    max_tokens_per_request=100
)
print(f"预计需要 {estimate.continues_needed} 次 continue")

# 示例 4：动态 continue 提示词
def smart_continue_prompt(count, max_count, current_text, original_prompt):
    if "JSON" in original_prompt:
        return "请继续完成 JSON 响应，确保格式完整。"
    else:
        return f"请继续（第 {count} 次）"

full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    continue_prompt=smart_continue_prompt
)

# 示例 5：错误处理
full_result = ChatContinue.continue_request(
    chat,
    result,
    history=history,
    max_continues=3,
    on_error="return_partial"  # 失败时返回部分结果
)
```

## 五、与 docdance 实现的对比

| 功能 | docdance 实现 | lexilux 当前 (v2.0) | lexilux 改进后 |
|------|--------------|---------------------|----------------|
| 流式 continue | ✅ 手动实现 | ✅ `continue_request_stream()` | ✅ 保持 |
| 进度跟踪 | ✅ 硬编码 print | ❌ 无 | ✅ 回调函数 |
| 请求延迟 | ✅ 硬编码随机延迟 | ❌ 无 | ✅ 可配置延迟 |
| 错误处理 | ✅ 返回部分结果 | ❌ 直接抛异常 | ✅ 可配置策略 |
| 历史管理 | ✅ 手动构建 | ✅ **显式管理**（v2.0 要求） | ✅ 保持显式 |
| auto_history | ✅ 使用（旧版本） | ❌ **已完全移除** | ❌ 不再支持 |
| Helper 方法 | ❌ 无 | ❌ 无 | ✅ `needs_continue`, `ensure_complete` |
| Token 估算 | ❌ 无 | ❌ 无 | ✅ `estimate_continues_needed` |
| 提示词定制 | ✅ 固定模板 | ✅ 固定字符串 | ✅ 支持函数/模板 |

## 六、总结

### 6.1 为什么 docdance 自己实现？

1. **历史原因**：可能在 lexilux v2.0 之前开发，且可能仍在使用旧版本（v0.5.x）
2. **特殊需求**：需要进度跟踪、延迟控制、错误恢复等
3. **lexilux 的不足**：当时缺少这些高级功能
4. **API 变化**：lexilux v2.0 移除了 `auto_history`，docdance 代码可能需要迁移

### 6.2 是否需要实现 docdance 的做法？

**部分需要**，但应该：
- ✅ 以更通用、可配置的方式实现
- ✅ 保持 API 的一致性和简洁性
- ✅ 向后兼容现有代码
- ❌ 不直接移植硬编码的逻辑

### 6.3 改进优先级

1. **高优先级**：进度跟踪、请求延迟控制、Helper 方法
2. **中优先级**：Token 估算、错误处理
3. **低优先级**：提示词定制化

### 6.4 实施建议

1. **Phase 1** 实现核心功能（进度跟踪、延迟控制、Helper 方法）
2. **Phase 2** 实现增强功能（Token 估算、错误处理）
3. **Phase 3** 实现高级功能（提示词定制化）

实施完成后，docdance 可以迁移到 lexilux 的标准 API，减少代码重复和维护成本。
