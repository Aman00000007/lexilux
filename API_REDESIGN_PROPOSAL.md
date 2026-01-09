# API 重新设计提案：明确区分"一次响应"和"完整响应"

## 一、问题分析

### 1.1 当前设计的问题

**当前使用模式（不清晰）：**
```python
# 用户想要完整响应，但需要手动判断
history = ChatHistory()
result = chat("Write a long JSON", history=history, max_tokens=100)
if result.finish_reason == "length":  # 需要手动判断
    full_result = ChatContinue.continue_request(chat, result, history=history)
    json_data = json.loads(full_result.text)
else:
    json_data = json.loads(result.text)
```

**问题：**
1. ❌ 用户意图不明确：代码看不出用户想要"一次响应"还是"完整响应"
2. ❌ 代码重复：每次都需要判断 `finish_reason`
3. ❌ 容易出错：忘记判断或处理截断情况
4. ❌ API 混乱：`chat()`, `chat.complete()`, `chat.continue_if_needed()` 职责不清

### 1.2 用户需求

用户应该能够明确表达意图：

1. **"我要一次响应"** → 即使被截断也接受，用于：
   - 流式输出场景（用户可以看到实时输出）
   - 不需要完整响应的场景
   - 性能优先的场景

2. **"我要完整响应"** → 自动处理截断，用于：
   - JSON 提取
   - 需要完整内容的场景
   - 可靠性优先的场景

## 二、改进方案

### 2.1 核心设计原则

1. **明确性**：API 名称和参数应该清楚表达用户意图
2. **简洁性**：减少用户需要写的代码
3. **一致性**：流式和非流式 API 保持一致的设计

### 2.2 新的 API 设计

#### 方案 A：明确的方法分离（推荐）

**核心思想**：`chat()` 和 `chat.complete()` 是完全不同的方法，职责清晰。

```python
# ========== 场景 1：一次响应（即使被截断也接受）==========
history = ChatHistory()
result = chat("Hello", history=history)
# 结果可能被截断，但用户接受这种情况
print(result.text)  # 可能不完整

# 流式版本
for chunk in chat.stream("Hello", history=history):
    print(chunk.delta, end="")
# 流式输出可能被截断，但用户接受


# ========== 场景 2：完整响应（自动处理截断）==========
history = ChatHistory()
result = chat.complete("Write a long JSON", history=history, max_tokens=100)
# 自动处理截断，保证返回完整响应（或抛出异常）
json_data = json.loads(result.text)  # 保证完整

# 流式版本
for chunk in chat.complete_stream("Write a long JSON", history=history, max_tokens=100):
    print(chunk.delta, end="")
# 自动处理截断，保证完整响应
result = chunk_iterator.result.to_chat_result()
json_data = json.loads(result.text)  # 保证完整
```

**关键改进：**
1. ✅ `chat()` 和 `chat.stream()` 明确表示"一次响应"，不处理截断
2. ✅ `chat.complete()` 和 `chat.complete_stream()` 明确表示"完整响应"，自动处理截断
3. ✅ 移除 `chat.continue_if_needed()`（功能被 `complete()` 覆盖）
4. ✅ `ChatContinue.continue_request()` 保留，但仅用于高级场景

#### 方案 B：通过参数控制（不推荐）

```python
# 通过参数控制行为
result = chat("Hello", history=history, ensure_complete=True)  # 完整响应
result = chat("Hello", history=history, ensure_complete=False)  # 一次响应
```

**问题：**
- ❌ 参数名不够直观
- ❌ 默认值选择困难（True 还是 False？）
- ❌ 不够明确，用户可能忘记设置

### 2.3 详细 API 设计

#### 2.3.1 `chat()` - 一次响应

```python
def __call__(
    self,
    messages: MessagesLike,
    *,
    history: ChatHistory | None = None,
    model: str | None = None,
    system: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    **params: Any,
) -> ChatResult:
    """
    Make a single chat completion request.
    
    **Behavior**: Returns the response from a single API call, even if truncated.
    Does NOT automatically continue if the response is cut off.
    
    Use this when:
    - You accept partial responses
    - You want to handle truncation manually
    - Performance is more important than completeness
    
    For complete responses, use `chat.complete()` instead.
    
    Args:
        messages: Input messages.
        history: Optional ChatHistory instance.
        **params: Additional parameters.
    
    Returns:
        ChatResult (may be truncated if finish_reason == "length").
    
    Examples:
        >>> history = ChatHistory()
        >>> result = chat("Hello", history=history)
        >>> print(result.text)  # May be incomplete if truncated
        >>> if result.finish_reason == "length":
        ...     print("Response was truncated")
    """
    # 实现：只做一次 API 调用，不处理截断
    ...
```

#### 2.3.2 `chat.complete()` - 完整响应

```python
def complete(
    self,
    messages: MessagesLike,
    *,
    history: ChatHistory | None = None,  # 可选，如果不提供则内部创建
    max_continues: int = 5,
    continue_prompt: str = "continue",
    **params: Any,
) -> ChatResult:
    """
    Ensure a complete response, automatically handling truncation.
    
    **Behavior**: Automatically continues generation if the response is truncated,
    ensuring the returned result is complete (or raises an exception).
    
    **History Management**:
    - If `history` is provided, uses it (for multi-turn conversations)
    - If `history` is None, creates a new history internally (for single-turn conversations)
    - The history is automatically updated with the prompt and response
    
    Use this when:
    - You need a complete response (e.g., JSON extraction)
    - You cannot accept partial responses
    - Reliability is more important than performance
    
    For single responses (even if truncated), use `chat()` instead.
    
    Args:
        messages: Input messages.
        history: Optional ChatHistory instance. If None, creates a new one internally.
        max_continues: Maximum number of continuation attempts.
        continue_prompt: Prompt for continuation requests.
        **params: Additional parameters.
    
    Returns:
        Complete ChatResult (never truncated, unless max_continues exceeded).
    
    Raises:
        ChatIncompleteResponseError: If response is still truncated after max_continues.
    
    Examples:
        # Single-turn conversation (no history needed)
        >>> result = chat.complete("Write a long JSON", max_tokens=100)
        >>> json_data = json.loads(result.text)  # Guaranteed complete
        
        # Multi-turn conversation (provide history)
        >>> history = ChatHistory()
        >>> result1 = chat.complete("First question", history=history)
        >>> result2 = chat.complete("Follow-up question", history=history)
    """
    # 实现：
    # 1. 如果 history 为 None，创建一个新的
    # 2. 调用 chat()，传入 history（会自动记录 prompt 和 response）
    # 3. 如果被截断，使用这个 history 进行 continue
    ...
```

#### 2.3.3 `chat.stream()` - 流式一次响应

```python
def stream(
    self,
    messages: MessagesLike,
    *,
    history: ChatHistory | None = None,
    **params: Any,
) -> StreamingIterator:
    """
    Stream a single chat completion response.
    
    **Behavior**: Streams the response from a single API call, even if truncated.
    Does NOT automatically continue if the response is cut off.
    
    Use this when:
    - You want real-time output
    - You accept partial responses
    - You want to handle truncation manually
    
    For complete streaming responses, use `chat.complete_stream()` instead.
    
    Args:
        messages: Input messages.
        history: Optional ChatHistory instance.
        **params: Additional parameters.
    
    Returns:
        StreamingIterator (may be truncated if finish_reason == "length").
    
    Examples:
        >>> history = ChatHistory()
        >>> iterator = chat.stream("Hello", history=history)
        >>> for chunk in iterator:
        ...     print(chunk.delta, end="")
        >>> result = iterator.result.to_chat_result()
        >>> if result.finish_reason == "length":
        ...     print("Response was truncated")
    """
    # 实现：只做一次流式调用，不处理截断
    ...
```

#### 2.3.4 `chat.complete_stream()` - 流式完整响应

```python
def complete_stream(
    self,
    messages: MessagesLike,
    *,
    history: ChatHistory | None = None,  # 可选，如果不提供则内部创建
    max_continues: int = 5,
    continue_prompt: str = "continue",
    **params: Any,
) -> StreamingIterator:
    """
    Stream a complete response, automatically handling truncation.
    
    **Behavior**: Automatically continues streaming if the response is truncated,
    ensuring the final result is complete (or raises an exception).
    
    Use this when:
    - You need a complete response with real-time output
    - You cannot accept partial responses
    - You want both streaming and completeness
    
    For single streaming responses (even if truncated), use `chat.stream()` instead.
    
    Args:
        messages: Input messages.
        history: Optional ChatHistory instance. If None, creates a new one internally.
        max_continues: Maximum number of continuation attempts.
        continue_prompt: Prompt for continuation requests.
        **params: Additional parameters.
    
    Returns:
        StreamingIterator (guaranteed complete, unless max_continues exceeded).
    
    Raises:
        ChatIncompleteResponseError: If response is still truncated after max_continues.
    
    Examples:
        # Single-turn conversation (no history needed)
        >>> iterator = chat.complete_stream("Write a long JSON", max_tokens=100)
        >>> for chunk in iterator:
        ...     print(chunk.delta, end="")
        >>> result = iterator.result.to_chat_result()
        >>> json_data = json.loads(result.text)  # Guaranteed complete
        
        # Multi-turn conversation (provide history)
        >>> history = ChatHistory()
        >>> iterator1 = chat.complete_stream("First question", history=history)
        >>> iterator2 = chat.complete_stream("Follow-up", history=history)
    """
    # 实现：自动处理截断，保证完整响应
    ...
```

### 2.4 移除的方法

以下方法应该被移除，因为功能已被 `complete()` 覆盖：

1. ❌ `chat.continue_if_needed()` → 用 `chat.complete()` 替代
2. ❌ `chat.continue_if_needed_stream()` → 用 `chat.complete_stream()` 替代

**保留的方法（高级场景）：**
- ✅ `ChatContinue.continue_request()` - 用于需要手动控制 continue 的场景
- ✅ `ChatContinue.continue_request_stream()` - 流式版本

### 2.5 关键设计决策：history 参数的可选性

**为什么 `complete()` 的 `history` 参数应该是可选的？**

1. **单次对话场景**（最常见）：
   ```python
   # 用户只想要一个完整的响应，不需要多轮对话
   result = chat.complete("Write a JSON", max_tokens=100)
   # 内部自动创建 history，记录 prompt → response
   # 如果被截断，使用这个 history 进行 continue
   ```

2. **多轮对话场景**（需要上下文）：
   ```python
   # 用户需要多轮对话，必须提供 history 来保持上下文
   history = ChatHistory()
   result1 = chat.complete("First question", history=history)
   result2 = chat.complete("Follow-up question", history=history)
   ```

**实现逻辑：**
- 如果 `history=None`：内部创建新的 `ChatHistory()`，用于单次对话
- 如果提供了 `history`：使用它，用于多轮对话
- 无论哪种情况，`chat()` 调用会自动更新 history（添加 prompt 和 response）
- Continue 时使用这个 history 来保持上下文

### 2.5 API 对比表

| 场景 | 当前 API | 新 API | 说明 |
|------|---------|--------|------|
| 一次响应（非流式） | `chat()` | `chat()` | 保持不变，但文档更明确 |
| 一次响应（流式） | `chat.stream()` | `chat.stream()` | 保持不变，但文档更明确 |
| 完整响应（非流式） | `chat.complete()` | `chat.complete()` | **改进**：`history` 参数改为可选 |
| 完整响应（流式） | `chat.complete_stream()` | `chat.complete_stream()` | **改进**：`history` 参数改为可选 |
| 条件性继续 | `chat.continue_if_needed()` | ❌ **移除** | 用 `chat.complete()` 替代 |
| 条件性继续（流式） | `chat.continue_if_needed_stream()` | ❌ **移除** | 用 `chat.complete_stream()` 替代 |
| 手动继续 | `ChatContinue.continue_request()` | `ChatContinue.continue_request()` | 保留，用于高级场景 |

## 三、迁移指南

### 3.1 从旧 API 迁移

#### 旧代码（需要判断 finish_reason）：
```python
# ❌ 旧方式：需要手动判断
history = ChatHistory()
result = chat("Write JSON", history=history, max_tokens=100)
if result.finish_reason == "length":
    full_result = ChatContinue.continue_request(chat, result, history=history)
    json_data = json.loads(full_result.text)
else:
    json_data = json.loads(result.text)
```

#### 新代码（明确意图，更简洁）：
```python
# ✅ 新方式：明确表达意图，history 可选
result = chat.complete("Write JSON", max_tokens=100)
json_data = json.loads(result.text)  # 保证完整

# 如果需要多轮对话，提供 history
history = ChatHistory()
result1 = chat.complete("First question", history=history)
result2 = chat.complete("Follow-up", history=history)
```

#### 旧代码（使用 continue_if_needed）：
```python
# ❌ 旧方式
history = ChatHistory()
result = chat("Write JSON", history=history, max_tokens=100)
full_result = chat.continue_if_needed(result, history=history)
```

#### 新代码：
```python
# ✅ 新方式：直接使用 complete
history = ChatHistory()
result = chat.complete("Write JSON", history=history, max_tokens=100)
```

### 3.2 使用场景示例

#### 场景 1：流式输出，接受截断
```python
# 用户想要实时看到输出，即使被截断也接受
history = ChatHistory()
for chunk in chat.stream("Tell me a story", history=history):
    print(chunk.delta, end="", flush=True)
# 如果被截断，用户可以看到部分输出，这是可接受的
```

#### 场景 2：需要完整 JSON
```python
# 用户需要完整的 JSON，不能接受截断
# 单次对话，不需要提供 history
result = chat.complete("Extract data as JSON", max_tokens=100)
json_data = json.loads(result.text)  # 保证完整，不会被截断
```

#### 场景 3：流式 + 完整响应
```python
# 用户想要实时输出，但也要保证完整
# 单次对话，不需要提供 history
iterator = chat.complete_stream("Write a long article", max_tokens=100)
for chunk in iterator:
    print(chunk.delta, end="", flush=True)
result = iterator.result.to_chat_result()
# 保证完整，不会被截断
```

#### 场景 4：多轮对话 + 完整响应
```python
# 用户需要多轮对话，每轮都要完整响应
history = ChatHistory()
result1 = chat.complete("First question", history=history)
result2 = chat.complete("Follow-up question", history=history)
# 每轮都保证完整，且保持上下文
```

## 四、实现细节

### 4.1 重要：History 的 Immutability（不可变性）

**当前实现的问题：**
当前实现**直接修改**传入的 `history` 参数：
- `chat()` 中：`history.add_user()`, `history.append_result()` - 直接修改
- `chat.stream()` 中：`history.add_user()`, 流式更新 - 直接修改
- `ChatContinue.continue_request()` 中：`history.add_user()` - 直接修改

**问题：**
- ❌ 违反了函数式编程的 immutability 原则
- ❌ 用户传入的 history 被意外修改，可能导致意外的副作用
- ❌ 难以进行并发操作（多个线程同时使用同一个 history）

**改进方案：**

所有接收 `history` 参数的接口应该：
1. **如果提供了 history**：使用 `history.clone()` 创建副本，修改副本
2. **如果没有提供 history**：内部创建新的 `ChatHistory()`

**实现示例：**
```python
def __call__(self, messages, *, history=None, **params) -> ChatResult:
    # 如果提供了 history，创建副本（immutable）
    if history is not None:
        working_history = history.clone()  # 创建副本
    else:
        working_history = ChatHistory()  # 创建新的
    
    # 使用 working_history 进行操作
    # ... 修改 working_history，不影响原始 history
```

**或者更激进的方式（推荐）：**
```python
def __call__(self, messages, *, history=None, **params) -> ChatResult:
    # 总是创建新的 history（如果提供了，从它克隆；否则创建新的）
    working_history = history.clone() if history is not None else ChatHistory()
    
    # 使用 working_history 进行操作
    # ... 修改 working_history，不影响原始 history
    
    # 如果需要返回更新后的 history，可以返回 working_history
    # 但默认情况下，不返回（保持 API 简洁）
```

**对于 `complete()` 的特殊处理：**
```python
def complete(self, messages, *, history=None, max_continues=5, **params) -> ChatResult:
    # 如果提供了 history，创建副本
    if history is not None:
        working_history = history.clone()
    else:
        working_history = ChatHistory()
    
    # 使用 working_history 进行操作
    result = self(messages, history=working_history, **params)
    
    # 如果被截断，使用 working_history 进行 continue
    if result.finish_reason == "length":
        result = ChatContinue.continue_request(
            self, result, history=working_history, ...
        )
    
    return result
```

**注意：** 如果用户需要获取更新后的 history，可以考虑：
1. 返回更新后的 history（但会增加 API 复杂度）
2. 提供 `return_history` 参数（可选）
3. 或者让用户自己管理 history（推荐）

### 4.2 `chat()` 的实现

```python
def __call__(self, messages, *, history=None, **params) -> ChatResult:
    """
    一次响应，不处理截断。
    
    **History Immutability**: 如果提供了 history，会创建副本进行操作，
    不会修改原始 history。
    """
    # 创建 working history（immutable）
    working_history = history.clone() if history is not None else ChatHistory()
    
    # 只做一次 API 调用
    # 使用 working_history（不影响原始 history）
    # 不检查 finish_reason
    # 不自动 continue
    # 返回结果（可能被截断）
    ...
```

### 4.3 `chat.complete()` 的实现

```python
def complete(self, messages, *, history: ChatHistory | None = None, max_continues=5, **params) -> ChatResult:
    """
    完整响应，自动处理截断。
    
    **History Immutability**: 如果提供了 history，会创建副本进行操作，
    不会修改原始 history。
    """
    # 1. 创建 working history（immutable）
    #    如果提供了 history，创建副本；否则创建新的
    working_history = history.clone() if history is not None else ChatHistory()
    
    # 2. 做一次 API 调用（会自动更新 working_history：添加 prompt 和 response）
    result = self(messages, history=working_history, **params)
    
    # 3. 如果被截断，自动 continue（使用已更新的 working_history）
    if result.finish_reason == "length":
        result = ChatContinue.continue_request(
            self, result, history=working_history,
            max_continues=max_continues, **params
        )
    
    # 4. 如果仍然被截断，抛出异常
    if result.finish_reason == "length":
        raise ChatIncompleteResponseError(...)
    
    # 5. 返回完整结果
    # 注意：working_history 包含更新后的历史，但不返回（保持 API 简洁）
    # 如果用户需要，可以自己管理 history
    return result
```

### 4.4 关键改进点

1. **History Immutability（不可变性）**：
   - ✅ 所有接收 `history` 参数的接口都应该是 immutable 的
   - ✅ 如果提供了 history，使用 `history.clone()` 创建副本
   - ✅ 修改副本，不影响原始 history
   - ✅ 避免意外的副作用，支持并发操作

2. **`complete()` 的 `history` 参数改为可选**：
   - 如果提供，用于多轮对话（保持上下文）
   - 如果不提供，内部自动创建（用于单次对话）
   - 这样用户不需要手动创建 history，使用更简单

3. **`chat()` 的 `history` 参数保持可选**：
   - 因为不需要 continue，history 只是用于记录对话
   - 如果不需要记录，可以不提供

4. **自动 history 管理（在副本上）**：
   - `chat()` 调用会自动更新 working_history（添加 prompt 和 response）
   - `complete()` 利用这个机制，即使内部创建 history，也能正确进行 continue
   - 但不会修改用户传入的原始 history

### 4.5 关于返回更新后的 History

**问题：** 如果 history 是 immutable 的，用户如何获取更新后的 history？

**方案 A：不返回（推荐，保持 API 简洁）**
```python
# 用户自己管理 history
history = ChatHistory()
result = chat("Hello", history=history)
# 如果用户需要更新后的 history，可以手动添加：
history.add_user("Hello")
history.append_result(result)
```

**方案 B：返回更新后的 history（可选）**
```python
def complete(self, messages, *, history=None, return_history=False, ...):
    working_history = history.clone() if history is not None else ChatHistory()
    result = self(messages, history=working_history, ...)
    # ...
    if return_history:
        return result, working_history
    return result
```

**推荐：方案 A**，因为：
- API 更简洁
- 用户有完全的控制权
- 符合函数式编程原则（单一返回值）

3. **文档明确说明行为**：
   - `chat()` 的文档明确说明"可能被截断"
   - `chat.complete()` 的文档明确说明"保证完整"

## 五、优势

### 5.1 对用户的好处

1. ✅ **意图清晰**：代码直接表达用户意图
2. ✅ **代码简洁**：不需要手动判断 `finish_reason`
3. ✅ **减少错误**：不会忘记处理截断情况
4. ✅ **易于理解**：API 名称直接说明行为
5. ✅ **History Immutability**：传入的 history 不会被修改，避免意外副作用
6. ✅ **支持并发**：多个线程可以安全地使用同一个 history

### 5.2 对库的好处

1. ✅ **职责清晰**：每个方法职责单一
2. ✅ **易于维护**：减少方法数量，逻辑更清晰
3. ✅ **易于测试**：测试用例更明确
4. ✅ **易于文档化**：文档结构更清晰
5. ✅ **函数式设计**：History immutability 符合函数式编程原则
6. ✅ **线程安全**：不修改传入参数，支持并发操作

## 六、定制化 Continue 策略

### 6.1 问题：当前 continue 策略不够灵活

**当前实现的局限性：**
- ❌ 固定策略：只能发送 "continue" prompt
- ❌ 无进度跟踪：用户不知道 continue 进度
- ❌ 无延迟控制：无法避免请求过快
- ❌ 固定错误处理：失败时直接抛异常

**docdance 等团队的需求：**
- ✅ 自定义 continue prompt（从配置或模板获取）
- ✅ 进度跟踪（显示 "继续生成 1/3"）
- ✅ 请求延迟控制（随机延迟 1-2 秒）
- ✅ 灵活的错误处理（失败时返回部分结果）

### 6.2 解决方案：支持定制化参数

**增强的 `chat.complete()` API：**

```python
result = chat.complete(
    "Write JSON",
    max_tokens=100,
    
    # 自定义 continue prompt（支持字符串或函数）
    continue_prompt=lambda count, max_count, current_text, original_prompt: 
        f"请继续完成（第 {count}/{max_count} 次）",
    
    # 进度跟踪回调
    on_progress=lambda count, max_count, current, all_results:
        print(f"🔄 继续生成 {count}/{max_count}..."),
    
    # 请求延迟控制（随机延迟 1-2 秒）
    continue_delay=(1.0, 2.0),
    
    # 错误处理策略
    on_error="return_partial",  # 或 "raise"
)
```

**详细设计请参考：** `CUSTOMIZABLE_CONTINUE_STRATEGY.md`

### 6.3 实施优先级

1. **Phase 1**：基础定制化（`continue_prompt` 支持函数，`on_progress` 回调，`continue_delay`）
2. **Phase 2**：错误处理（`on_error` 策略）
3. **Phase 3**：高级功能（策略类支持，可选）

## 七、总结

### 7.1 核心改进

1. **明确区分两种场景**：
   - `chat()` / `chat.stream()` → 一次响应（可能截断）
   - `chat.complete()` / `chat.complete_stream()` → 完整响应（保证完整）

2. **移除冗余方法**：
   - 移除 `continue_if_needed()` 系列方法
   - 保留 `ChatContinue.continue_request()` 用于高级场景

3. **支持定制化**：
   - 通过回调函数和配置参数支持定制化 continue 策略
   - 满足 docdance 等团队的高级需求

4. **History Immutability**：
   - 所有接收 `history` 参数的接口都是 immutable 的
   - 避免意外的副作用，支持并发操作

5. **强化文档**：
   - 每个方法的文档明确说明行为
   - 明确说明使用场景

### 6.2 符合最佳实践

✅ **单一职责原则**：每个方法只做一件事
✅ **明确性优于隐式**：用户意图在代码中清晰表达
✅ **简洁性**：减少用户需要写的代码
✅ **一致性**：流式和非流式 API 保持一致的设计

### 7.4 实施建议

1. **Phase 1**：实现 History Immutability
   - 修改所有接收 `history` 参数的方法，使用 `history.clone()` 创建副本
   - 更新 `chat()`, `chat.stream()`, `chat.complete()`, `chat.complete_stream()`
   - 更新 `ChatContinue.continue_request()` 和 `ChatContinue.continue_request_stream()`

2. **Phase 2**：实现基础定制化
   - 支持 `continue_prompt` 为函数
   - 添加 `on_progress` 回调
   - 添加 `continue_delay` 参数

3. **Phase 3**：实现错误处理定制化
   - 添加 `on_error` 策略
   - 添加 `on_error_callback` 回调

4. **Phase 4**：更新文档
   - 明确说明 `chat()` 和 `chat.complete()` 的区别
   - 明确说明 History Immutability 原则
   - 明确说明定制化 continue 策略
   - 更新所有示例代码

5. **Phase 5**：标记 `continue_if_needed()` 为 deprecated

6. **Phase 6**：移除 `continue_if_needed()` 方法

### 7.5 需要修改的方法清单

**需要实现 History Immutability 的方法：**
1. ✅ `Chat.__call__()` - 使用 `history.clone()` 创建副本
2. ✅ `Chat.stream()` - 使用 `history.clone()` 创建副本
3. ✅ `Chat.complete()` - 使用 `history.clone()` 创建副本，支持定制化参数
4. ✅ `Chat.complete_stream()` - 使用 `history.clone()` 创建副本，支持定制化参数
5. ✅ `ChatContinue.continue_request()` - 使用 `history.clone()` 创建副本，支持定制化参数
6. ✅ `ChatContinue.continue_request_stream()` - 使用 `history.clone()` 创建副本，支持定制化参数

**需要添加的定制化功能：**
1. ✅ `continue_prompt` 支持函数类型
2. ✅ `on_progress` 回调函数
3. ✅ `continue_delay` 参数（固定或随机延迟）
4. ✅ `on_error` 错误处理策略
5. ✅ `on_error_callback` 错误处理回调

**实现检查清单：**
- [ ] 所有方法在修改 history 前都使用 `history.clone()` 创建副本
- [ ] 测试用例验证原始 history 不被修改
- [ ] 支持定制化 continue 策略（prompt、进度、延迟、错误处理）
- [ ] 测试用例验证定制化功能
- [ ] 文档明确说明 History Immutability 原则
- [ ] 文档明确说明定制化 continue 策略
- [ ] 更新所有示例代码
- [ ] 提供 docdance 风格的示例代码
