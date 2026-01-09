# 可定制化的 Continue 策略设计

## 一、问题分析

### 1.1 当前实现的局限性

**当前 continue 策略：**
- 固定策略：发送 "continue" prompt
- 固定行为：自动合并结果
- 固定错误处理：失败时抛异常
- 无进度跟踪
- 无延迟控制

**docdance 的定制化需求：**
1. ✅ **自定义 continue prompt**：从配置或模板获取
2. ❌ **进度跟踪**：显示 "继续生成 1/3"
3. ❌ **请求延迟**：随机延迟 1-2 秒，避免请求过快
4. ❌ **错误恢复**：失败时返回部分结果
5. ❌ **自定义历史构建**：手动构建 continue_history（原始 prompt + 已生成文本 + continue prompt）

### 1.2 当前方案是否能满足 docdance？

**部分满足，但不够灵活：**

✅ **已支持：**
- 自定义 continue prompt（`continue_prompt` 参数）
- 流式 continue（`continue_request_stream()`）

❌ **不支持：**
- 进度跟踪回调
- 请求延迟控制
- 灵活的错误处理策略
- 自定义历史构建方式

## 二、设计目标

1. **保持简单 API**：默认行为简单易用
2. **支持高级定制**：通过回调、策略等方式支持定制化
3. **向后兼容**：现有代码不需要修改
4. **可扩展性**：易于添加新的定制化功能

## 三、设计方案

### 3.1 方案 A：回调函数 + 配置参数（推荐）

**核心思想**：通过回调函数和配置参数支持定制化，保持 API 简洁。

```python
# ========== 基础用法（简单）==========
result = chat.complete("Write JSON", max_tokens=100)
# 默认行为：自动 continue，使用 "continue" prompt

# ========== 定制化用法（高级）==========
def on_progress(count, max_count, current_result, all_results):
    print(f"🔄 继续生成 {count}/{max_count}... ({len(current_result.text)} 字符)")

def generate_continue_prompt(count, max_count, current_text, original_prompt):
    if "JSON" in original_prompt:
        return "请继续完成 JSON 响应，确保格式完整。"
    else:
        return f"请继续（第 {count} 次）"

result = chat.complete(
    "Write JSON",
    max_tokens=100,
    max_continues=5,
    continue_prompt=generate_continue_prompt,  # 支持函数
    continue_delay=(1.0, 2.0),  # 随机延迟
    on_progress=on_progress,  # 进度回调
    on_error="return_partial",  # 错误处理策略
)
```

### 3.2 方案 B：策略模式（更灵活，但更复杂）

**核心思想**：通过策略类支持完全定制化的 continue 行为。

```python
class ContinueStrategy:
    """Continue 策略接口"""
    def should_continue(self, result: ChatResult, count: int, max_count: int) -> bool:
        """是否应该继续"""
        ...
    
    def generate_prompt(self, count: int, max_count: int, current_text: str, original_prompt: str) -> str:
        """生成 continue prompt"""
        ...
    
    def get_delay(self, count: int, max_count: int) -> float:
        """获取延迟时间"""
        ...
    
    def handle_error(self, error: Exception, partial_result: ChatResult) -> ChatResult:
        """处理错误"""
        ...

# 使用
strategy = CustomContinueStrategy(...)
result = chat.complete("Write JSON", continue_strategy=strategy)
```

**问题：**
- ❌ 过于复杂，大多数用户不需要
- ❌ 需要定义接口，增加学习成本
- ❌ 不符合 lexilux 的简洁设计哲学

### 3.3 方案 C：混合方案（推荐）

**核心思想**：
- 简单场景：使用配置参数（`continue_prompt`, `continue_delay` 等）
- 高级场景：使用回调函数（`on_progress`, `on_error_callback` 等）
- 极端场景：使用策略类（可选）

## 四、详细设计

### 4.1 增强的 `chat.complete()` API

```python
def complete(
    self,
    messages: MessagesLike,
    *,
    history: ChatHistory | None = None,
    max_continues: int = 5,
    
    # ========== Continue Prompt 定制化 ==========
    continue_prompt: str | Callable = "continue",
    # 支持字符串或函数
    # 函数签名：continue_prompt(count: int, max_count: int, current_text: str, original_prompt: str) -> str
    
    # ========== 进度跟踪 ==========
    on_progress: Callable | None = None,
    # 回调函数签名：on_progress(count: int, max_count: int, current_result: ChatResult, all_results: list[ChatResult]) -> None
    
    # ========== 请求延迟控制 ==========
    continue_delay: float | tuple[float, float] = 0.0,
    # 固定延迟（秒）或随机延迟范围 (min, max)
    
    # ========== 错误处理策略 ==========
    on_error: str = "raise",  # "raise" 或 "return_partial"
    on_error_callback: Callable | None = None,
    # 回调函数签名：on_error_callback(error: Exception, partial_result: ChatResult) -> dict
    # 返回：{"action": "raise" | "return_partial" | "retry", "result": ChatResult}
    
    # ========== 高级定制（可选）==========
    continue_strategy: ContinueStrategy | None = None,
    # 如果提供了策略，使用策略；否则使用上述参数
    
    **params: Any,
) -> ChatResult:
    """
    Ensure a complete response with customizable continue strategy.
    
    **Basic Usage:**
    >>> result = chat.complete("Write JSON", max_tokens=100)
    
    **Custom Continue Prompt:**
    >>> def smart_prompt(count, max_count, current_text, original_prompt):
    ...     return f"请继续完成（第 {count}/{max_count} 次）"
    >>> result = chat.complete("Write JSON", continue_prompt=smart_prompt)
    
    **Progress Tracking:**
    >>> def on_progress(count, max_count, current, all_results):
    ...     print(f"继续生成 {count}/{max_count}...")
    >>> result = chat.complete("Write JSON", on_progress=on_progress)
    
    **Request Delay:**
    >>> result = chat.complete("Write JSON", continue_delay=(1.0, 2.0))
    
    **Error Handling:**
    >>> result = chat.complete("Write JSON", on_error="return_partial")
    """
    ...
```

### 4.2 增强的 `ChatContinue.continue_request()` API

```python
@staticmethod
def continue_request(
    chat: Chat,
    last_result: ChatResult,
    *,
    history: ChatHistory | None = None,
    max_continues: int = 1,
    auto_merge: bool = True,
    
    # ========== Continue Prompt 定制化 ==========
    continue_prompt: str | Callable = "continue",
    add_continue_prompt: bool = True,
    
    # ========== 进度跟踪 ==========
    on_progress: Callable | None = None,
    
    # ========== 请求延迟控制 ==========
    continue_delay: float | tuple[float, float] = 0.0,
    
    # ========== 错误处理策略 ==========
    on_error: str = "raise",
    on_error_callback: Callable | None = None,
    
    **params: Any,
) -> ChatResult | list[ChatResult]:
    """
    Continue generation with customizable strategy.
    
    **Examples:**
    >>> # Basic usage
    >>> result = ChatContinue.continue_request(chat, result, history=history)
    
    >>> # With progress tracking
    >>> def on_progress(count, max_count, current, all_results):
    ...     print(f"继续 {count}/{max_count}")
    >>> result = ChatContinue.continue_request(
    ...     chat, result, history=history,
    ...     on_progress=on_progress
    ... )
    
    >>> # With custom prompt and delay
    >>> result = ChatContinue.continue_request(
    ...     chat, result, history=history,
    ...     continue_prompt=lambda c, m, t, p: f"继续（{c}/{m}）",
    ...     continue_delay=(1.0, 2.0)
    ... )
    """
    ...
```

### 4.3 实现细节

#### 4.3.1 Continue Prompt 定制化

```python
def _get_continue_prompt(
    continue_prompt: str | Callable,
    continue_count: int,
    max_continues: int,
    current_text: str,
    original_prompt: str,
) -> str:
    """获取 continue prompt（支持字符串或函数）"""
    if callable(continue_prompt):
        return continue_prompt(continue_count, max_continues, current_text, original_prompt)
    else:
        return continue_prompt
```

#### 4.3.2 进度跟踪

```python
def _call_progress_callback(
    on_progress: Callable | None,
    continue_count: int,
    max_continues: int,
    current_result: ChatResult,
    all_results: list[ChatResult],
):
    """调用进度回调"""
    if on_progress:
        try:
            on_progress(continue_count, max_continues, current_result, all_results)
        except Exception as e:
            # 回调失败不应该影响主流程
            logger.warning(f"Progress callback failed: {e}")
```

#### 4.3.3 请求延迟控制

```python
def _apply_continue_delay(
    continue_delay: float | tuple[float, float],
    continue_count: int,
):
    """应用 continue 延迟"""
    if continue_count <= 1:
        return  # 第一次 continue 不需要延迟
    
    if isinstance(continue_delay, tuple):
        # 随机延迟范围
        import random
        delay = random.uniform(continue_delay[0], continue_delay[1])
    else:
        # 固定延迟
        delay = continue_delay
    
    if delay > 0:
        import time
        time.sleep(delay)
```

#### 4.3.4 错误处理策略

```python
def _handle_continue_error(
    error: Exception,
    partial_result: ChatResult,
    all_results: list[ChatResult],
    on_error: str,
    on_error_callback: Callable | None,
) -> ChatResult:
    """处理 continue 错误"""
    if on_error_callback:
        try:
            response = on_error_callback(error, partial_result)
            action = response.get("action", "raise")
            if action == "return_partial":
                return ChatContinue.merge_results(*all_results)
            elif action == "retry":
                # 可以重试（需要额外实现）
                raise NotImplementedError("Retry not implemented yet")
            # else: "raise" - fall through
        except Exception as callback_error:
            logger.warning(f"Error callback failed: {callback_error}")
            # Fall through to default behavior
    
    if on_error == "return_partial":
        return ChatContinue.merge_results(*all_results)
    else:  # "raise"
        raise
```

### 4.4 完整的实现示例

```python
def complete(
    self,
    messages: MessagesLike,
    *,
    history: ChatHistory | None = None,
    max_continues: int = 5,
    continue_prompt: str | Callable = "continue",
    on_progress: Callable | None = None,
    continue_delay: float | tuple[float, float] = 0.0,
    on_error: str = "raise",
    on_error_callback: Callable | None = None,
    **params: Any,
) -> ChatResult:
    """完整响应，支持定制化 continue 策略"""
    from lexilux.chat.continue_ import ChatContinue
    from lexilux.chat.exceptions import ChatIncompleteResponseError
    
    # 1. 创建 working history（immutable）
    working_history = history.clone() if history is not None else ChatHistory()
    
    # 2. 获取原始 prompt（用于自定义 continue prompt）
    original_prompt = messages if isinstance(messages, str) else str(messages)
    
    # 3. 做一次 API 调用
    result = self(messages, history=working_history, **params)
    
    # 4. 如果被截断，使用定制化策略进行 continue
    if result.finish_reason == "length":
        try:
            result = ChatContinue.continue_request(
                self,
                result,
                history=working_history,
                max_continues=max_continues,
                continue_prompt=continue_prompt,
                on_progress=on_progress,
                continue_delay=continue_delay,
                on_error=on_error,
                on_error_callback=on_error_callback,
                original_prompt=original_prompt,  # 传递给 continue_request
                **params,
            )
        except Exception as e:
            # 使用错误处理策略
            if on_error == "return_partial" or (on_error_callback and ...):
                result = _handle_continue_error(e, result, [result], on_error, on_error_callback)
            else:
                raise ChatIncompleteResponseError(...) from e
    
    # 5. 如果仍然被截断，抛出异常
    if result.finish_reason == "length":
        raise ChatIncompleteResponseError(...)
    
    return result
```

## 五、与 docdance 需求的对比

| docdance 需求 | 当前实现 | 改进后 |
|--------------|---------|--------|
| 自定义 continue prompt | ✅ 支持字符串 | ✅ 支持字符串和函数 |
| 进度跟踪 | ❌ 无 | ✅ `on_progress` 回调 |
| 请求延迟控制 | ❌ 无 | ✅ `continue_delay` 参数 |
| 错误恢复 | ❌ 直接抛异常 | ✅ `on_error` 策略 |
| 自定义历史构建 | ❌ 固定方式 | ⚠️ 可通过策略类支持（高级） |

## 六、使用示例

### 6.1 docdance 风格的实现

```python
# docdance 的需求
def docdance_style_complete(chat, prompt, history=None):
    """docdance 风格的 complete"""
    
    def on_progress(count, max_count, current, all_results):
        print(f"\n🔄[继续生成 {count}/{max_count}]", end="", flush=True)
    
    def generate_continue_prompt(count, max_count, current_text, original_prompt):
        # 从配置或模板获取
        from docdance.routines.extraction_prompt_builder.prompt_template import get_continue_prompt
        return get_continue_prompt()
    
    def handle_error(error, partial_result):
        # 返回部分结果
        return {"action": "return_partial", "result": partial_result}
    
    result = chat.complete(
        prompt,
        history=history,
        max_continues=5,
        continue_prompt=generate_continue_prompt,
        on_progress=on_progress,
        continue_delay=(1.0, 2.0),  # 随机延迟 1-2 秒
        on_error_callback=handle_error,
    )
    
    return result
```

### 6.2 简单场景（默认行为）

```python
# 最简单的用法
result = chat.complete("Write JSON", max_tokens=100)
# 自动处理截断，使用默认 "continue" prompt
```

### 6.3 中等定制化

```python
# 自定义 prompt 和进度跟踪
def on_progress(count, max_count, current, all_results):
    print(f"继续生成 {count}/{max_count}...")

result = chat.complete(
    "Write JSON",
    max_tokens=100,
    continue_prompt="请继续完成你的回答",
    on_progress=on_progress,
    continue_delay=1.0,  # 固定延迟 1 秒
)
```

### 6.4 高级定制化

```python
# 完全定制化的策略
def smart_continue_prompt(count, max_count, current_text, original_prompt):
    if "JSON" in original_prompt:
        return "请继续完成 JSON 响应，确保格式完整。"
    elif count > 2:
        return f"请继续（第 {count} 次，还有 {max_count - count} 次机会）"
    else:
        return "请继续"

def on_progress(count, max_count, current, all_results):
    total_length = sum(len(r.text) for r in all_results)
    print(f"🔄 继续生成 {count}/{max_count}... ({total_length} 字符)")

def handle_error(error, partial_result):
    logger.error(f"Continue failed: {error}")
    return {"action": "return_partial", "result": partial_result}

result = chat.complete(
    "Write a long JSON response",
    max_tokens=100,
    max_continues=5,
    continue_prompt=smart_continue_prompt,
    on_progress=on_progress,
    continue_delay=(1.0, 2.0),
    on_error_callback=handle_error,
)
```

## 七、实施建议

### 7.1 Phase 1：基础定制化（1-2 周）
1. ✅ 支持 `continue_prompt` 为函数
2. ✅ 添加 `on_progress` 回调
3. ✅ 添加 `continue_delay` 参数

### 7.2 Phase 2：错误处理（1 周）
4. ✅ 添加 `on_error` 策略
5. ✅ 添加 `on_error_callback` 回调

### 7.3 Phase 3：高级功能（可选）
6. ⚠️ 考虑添加策略类支持（如果用户需要）

## 八、总结

### 8.1 设计原则

1. **简单默认**：默认行为简单易用
2. **灵活定制**：通过回调函数支持高级定制
3. **向后兼容**：现有代码不需要修改
4. **渐进增强**：从简单到复杂，逐步支持更多功能

### 8.2 优势

1. ✅ **满足 docdance 需求**：支持所有 docdance 需要的定制化功能
2. ✅ **保持 API 简洁**：默认用法仍然简单
3. ✅ **易于扩展**：通过回调函数易于添加新功能
4. ✅ **向后兼容**：现有代码继续工作

### 8.3 与当前方案的关系

- **API_REDESIGN_PROPOSAL.md**：关注 API 结构（`chat()` vs `chat.complete()`）
- **本文档**：关注 continue 策略的定制化
- **两者结合**：完整的改进方案
