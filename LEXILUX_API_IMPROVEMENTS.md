# Lexilux API 改进建议

## 概述

本文档基于实际使用体验（在 docdance 项目中的 LLM 调用场景），提出对 lexilux API 的改进建议。主要关注点：
1. 简化常用操作的工作流
2. 提高错误处理的明确性
3. 增强 auto_history 与 ChatContinue 的集成
4. 提供更高级的便捷方法

---

## 1. ChatContinue API 简化

### 当前问题

**使用场景**：需要处理输出截断（finish_reason="length"）并继续生成。

**当前实现**：需要3个步骤，且容易出错：

```python
# 步骤1：检查 finish_reason
result = chat("Write a long story", max_tokens=50)
if result.finish_reason == "length":
    # 步骤2：创建历史
    history = ChatHistory.from_chat_result("Write a long story", result)
    # 步骤3：继续并合并
    continue_result = ChatContinue.continue_request(chat, history, result)
    full_result = ChatContinue.merge_results(result, continue_result)
```

**问题**：
1. 步骤多，容易遗漏合并步骤
2. 使用 auto_history 时仍需手动创建历史
3. 多次继续需要手动循环
4. 错误处理不明确

### 建议方案

#### 方案1：增强 ChatContinue.continue_request（推荐）

**改进理由**：
- 保持向后兼容
- 利用 auto_history 自动获取历史
- 减少用户需要管理的状态

**接口设计**：

```python
class ChatContinue:
    @staticmethod
    def continue_request(
        chat: Chat,
        last_result: ChatResult,
        *,
        history: ChatHistory | None = None,  # 新增：可选参数
        add_continue_prompt: bool = True,
        continue_prompt: str = "continue",
        max_continues: int = 1,  # 新增：支持多次继续
        auto_merge: bool = True,  # 新增：自动合并结果
        **params: Any,
    ) -> ChatResult | list[ChatResult]:
        """
        继续生成请求（增强版）。
        
        Args:
            chat: Chat 客户端实例
            last_result: 上一个结果（finish_reason == "length"）
            history: 对话历史（可选）。如果为 None 且 chat.auto_history=True，自动获取
            add_continue_prompt: 是否添加继续提示
            continue_prompt: 继续提示文本
            max_continues: 最大继续次数（如果结果仍被截断，自动继续）
            auto_merge: 是否自动合并结果。如果 False，返回结果列表
            **params: 传递给 chat 的额外参数
        
        Returns:
            如果 auto_merge=True: 返回合并后的 ChatResult
            如果 auto_merge=False: 返回结果列表 [last_result, continue_result1, ...]
        
        Raises:
            ValueError: 如果 last_result.finish_reason != "length"
            RuntimeError: 如果达到 max_continues 后仍被截断
        
        Examples:
            # 基本用法（自动获取历史）
            result = chat("Long story", max_tokens=50)
            if result.finish_reason == "length":
                full_result = ChatContinue.continue_request(chat, result)
                print(full_result.text)  # 完整的合并文本
            
            # 多次继续
            result = chat("Very long story", max_tokens=30)
            if result.finish_reason == "length":
                full_result = ChatContinue.continue_request(
                    chat, result, max_continues=3
                )
            
            # 获取所有中间结果
            result = chat("Story", max_tokens=50)
            if result.finish_reason == "length":
                all_results = ChatContinue.continue_request(
                    chat, result, auto_merge=False
                )
                # all_results = [result, continue_result1, continue_result2, ...]
        """
        if last_result.finish_reason != "length":
            raise ValueError(
                f"continue_request requires finish_reason='length', "
                f"got '{last_result.finish_reason}'"
            )
        
        # 自动获取历史（如果未提供且启用了 auto_history）
        if history is None:
            if chat.auto_history:
                history = chat.get_history()
                if history is None:
                    # 如果历史不存在，从结果创建
                    # 需要从 chat 的调用中获取原始 prompt
                    # 这里假设可以通过某种方式获取（可能需要改进 Chat 类）
                    raise ValueError(
                        "History not available. Either provide history manually "
                        "or ensure auto_history is enabled and chat was called."
                    )
            else:
                raise ValueError(
                    "History is required when auto_history=False. "
                    "Provide history manually or enable auto_history."
                )
        
        all_results = [last_result]
        current_result = last_result
        continue_count = 0
        
        while current_result.finish_reason == "length" and continue_count < max_continues:
            continue_count += 1
            
            # 继续生成
            continue_result = ChatContinue._single_continue_request(
                chat, history, current_result,
                add_continue_prompt=add_continue_prompt,
                continue_prompt=continue_prompt,
                **params
            )
            
            all_results.append(continue_result)
            current_result = continue_result
            
            # 更新历史（如果使用 auto_history，已自动更新）
            if not chat.auto_history:
                history.append_result(continue_result)
        
        # 检查是否仍被截断
        if current_result.finish_reason == "length":
            if auto_merge:
                # 即使被截断，也返回合并结果
                return ChatContinue.merge_results(*all_results)
            else:
                # 返回所有结果，让用户决定如何处理
                return all_results
        
        # 合并结果
        if auto_merge:
            if len(all_results) == 1:
                return all_results[0]
            return ChatContinue.merge_results(*all_results)
        else:
            return all_results
    
    @staticmethod
    def _single_continue_request(
        chat: Chat,
        history: ChatHistory,
        last_result: ChatResult,
        *,
        add_continue_prompt: bool = True,
        continue_prompt: str = "continue",
        **params: Any,
    ) -> ChatResult:
        """执行单次继续请求（内部方法，保持原有逻辑）"""
        if add_continue_prompt:
            history.add_user(continue_prompt)
        return chat(history.get_messages(), **params)
```

**使用示例**：

```python
# 场景1：简单继续（最常见）
chat = Chat(..., auto_history=True)
result = chat("Write a long JSON response", max_tokens=100)

if result.finish_reason == "length":
    # 一行代码完成继续和合并
    full_result = ChatContinue.continue_request(chat, result)
    print(full_result.text)  # 完整的 JSON

# 场景2：多次继续
result = chat("Very long response", max_tokens=50)
if result.finish_reason == "length":
    # 自动继续最多3次
    full_result = ChatContinue.continue_request(chat, result, max_continues=3)
    if full_result.finish_reason == "length":
        print("Warning: Still truncated after 3 continues")

# 场景3：需要所有中间结果
result = chat("Story", max_tokens=50)
if result.finish_reason == "length":
    all_results = ChatContinue.continue_request(chat, result, auto_merge=False)
    for i, r in enumerate(all_results):
        print(f"Part {i+1}: {len(r.text)} chars")
```

#### 方案2：在 Chat 类中添加便捷方法

**改进理由**：
- 更符合面向对象设计
- 方法调用更直观
- 可以更好地利用 auto_history

**接口设计**：

```python
class Chat:
    def continue_if_needed(
        self,
        result: ChatResult,
        *,
        max_continues: int = 3,
        continue_prompt: str = "continue",
        **params: Any,
    ) -> ChatResult:
        """
        如果结果被截断，自动继续生成直到完成。
        
        Args:
            result: 上一个结果
            max_continues: 最大继续次数
            continue_prompt: 继续提示文本
            **params: 传递给继续请求的参数
        
        Returns:
            合并后的完整结果
        
        Examples:
            result = chat("Long story", max_tokens=50)
            full_result = chat.continue_if_needed(result)
            # 如果 result.finish_reason == "length"，自动继续并合并
            # 如果 result.finish_reason != "length"，直接返回 result
        """
        if result.finish_reason != "length":
            return result
        
        history = self.get_history() if self.auto_history else None
        if history is None:
            raise ValueError(
                "Cannot continue: history not available. "
                "Enable auto_history or provide history manually."
            )
        
        return ChatContinue.continue_request(
            self, result,
            history=history,
            max_continues=max_continues,
            continue_prompt=continue_prompt,
            **params
        )
    
    def complete(
        self,
        messages: MessagesLike,
        *,
        max_continues: int = 3,
        ensure_complete: bool = True,
        **params: Any,
    ) -> ChatResult:
        """
        确保获取完整响应，自动处理截断。
        
        Args:
            messages: 输入消息
            max_continues: 最大继续次数
            ensure_complete: 如果为 True，达到最大次数后仍被截断会抛出异常
            **params: 传递给 chat 的参数
        
        Returns:
            完整的 ChatResult（可能经过多次继续和合并）
        
        Raises:
            RuntimeError: 如果 ensure_complete=True 且最终结果仍被截断
        
        Examples:
            # 确保获取完整响应
            result = chat.complete("Write a long JSON", max_tokens=100)
            # 自动处理截断，返回完整结果
            
            # 允许部分结果
            result = chat.complete(
                "Long story",
                max_tokens=50,
                ensure_complete=False
            )
            if result.finish_reason == "length":
                print("Warning: Response was truncated")
        """
        result = self(messages, **params)
        
        if result.finish_reason == "length":
            try:
                result = self.continue_if_needed(
                    result,
                    max_continues=max_continues,
                    **params
                )
            except Exception as e:
                if ensure_complete:
                    raise RuntimeError(
                        f"Failed to get complete response after {max_continues} continues"
                    ) from e
                raise
        
        if ensure_complete and result.finish_reason == "length":
            raise RuntimeError(
                f"Response still truncated after {max_continues} continues. "
                f"Consider increasing max_continues or max_tokens."
            )
        
        return result
```

**使用示例**：

```python
# 场景1：确保完整响应（最简单）
chat = Chat(..., auto_history=True)
result = chat.complete("Write a long JSON", max_tokens=100)
# 自动处理截断，返回完整结果
json_data = json.loads(result.text)

# 场景2：允许部分结果
result = chat.complete(
    "Long story",
    max_tokens=50,
    ensure_complete=False
)
if result.finish_reason == "length":
    print("Warning: Truncated")

# 场景3：手动控制
result = chat("Story", max_tokens=50)
if result.finish_reason == "length":
    full_result = chat.continue_if_needed(result, max_continues=3)
```

---

## 2. 错误处理行为明确化

### 当前问题

**问题1**：流式调用中断时的行为不明确

```python
# 如果网络中断，会发生什么？
for chunk in chat.stream("Hello"):
    print(chunk.delta, end="")
    # 如果这里网络中断，已接收的 chunks 如何处理？
    # finish_reason 是什么？
    # 如何恢复？
```

**问题2**：异常类型和恢复策略不明确

- 网络错误 vs 正常完成如何区分？
- 部分接收的数据如何保存？
- 如何从错误中恢复？

### 建议方案

#### 方案1：明确的异常类型和错误信息

**接口设计**：

```python
class ChatStreamInterrupted(Exception):
    """流式调用被中断的异常"""
    def __init__(
        self,
        message: str,
        partial_result: ChatResult | None = None,
        received_chunks: list[ChatStreamChunk] | None = None,
    ):
        super().__init__(message)
        self.partial_result = partial_result
        self.received_chunks = received_chunks or []
    
    def get_partial_text(self) -> str:
        """获取已接收的部分文本"""
        if self.partial_result:
            return self.partial_result.text
        return "".join(chunk.delta for chunk in self.received_chunks)


class ChatIncompleteResponse(Exception):
    """响应不完整的异常（达到最大继续次数后仍被截断）"""
    def __init__(
        self,
        message: str,
        final_result: ChatResult,
        continue_count: int,
    ):
        super().__init__(message)
        self.final_result = final_result
        self.continue_count = continue_count
```

**行为定义**：

```python
class Chat:
    def stream(
        self,
        messages: MessagesLike,
        *,
        # ... 其他参数 ...
        raise_on_interrupt: bool = True,  # 新增：中断时是否抛出异常
    ) -> StreamingIterator:
        """
        流式调用。
        
        Args:
            raise_on_interrupt: 如果为 True，网络中断时抛出 ChatStreamInterrupted
                               如果为 False，返回部分结果
        
        Raises:
            ChatStreamInterrupted: 如果网络中断且 raise_on_interrupt=True
            requests.RequestException: 其他网络错误
        
        Behavior:
            - 正常完成：返回完整的 StreamingIterator，chunk.done=True 时 finish_reason 可用
            - 网络中断（raise_on_interrupt=True）：抛出 ChatStreamInterrupted，包含部分结果
            - 网络中断（raise_on_interrupt=False）：返回部分结果，iterator.result 包含已接收的文本
        """
        # 实现...
```

**使用示例**：

```python
# 场景1：处理中断
try:
    iterator = chat.stream("Long response", raise_on_interrupt=True)
    for chunk in iterator:
        print(chunk.delta, end="")
except ChatStreamInterrupted as e:
    print(f"\nStream interrupted. Received: {len(e.get_partial_text())} chars")
    # 可以尝试恢复
    partial_text = e.get_partial_text()
    # 使用 ChatContinue 或重新调用

# 场景2：允许部分结果
iterator = chat.stream("Long response", raise_on_interrupt=False)
for chunk in iterator:
    print(chunk.delta, end="")
# 即使中断，iterator.result 也包含部分结果
partial_result = iterator.result.to_chat_result()
```

#### 方案2：错误恢复工具

**接口设计**：

```python
class ChatErrorRecovery:
    """错误恢复工具类"""
    
    @staticmethod
    def recover_from_interruption(
        chat: Chat,
        partial_result: ChatResult | str,
        original_prompt: str | None = None,
        *,
        strategy: str = "continue",  # "continue" | "retry" | "merge"
    ) -> ChatResult:
        """
        从网络中断中恢复。
        
        Args:
            chat: Chat 客户端
            partial_result: 部分结果（ChatResult 或文本）
            original_prompt: 原始提示（如果提供，使用 retry 策略）
            strategy: 恢复策略
                - "continue": 继续生成（假设 partial_result 是截断的）
                - "retry": 重新开始（使用 original_prompt）
                - "merge": 合并部分结果和重试结果
        
        Returns:
            恢复后的结果
        
        Examples:
            try:
                result = chat("Long response")
            except ChatStreamInterrupted as e:
                recovered = ChatErrorRecovery.recover_from_interruption(
                    chat, e.partial_result, original_prompt="Long response"
                )
        """
        if isinstance(partial_result, str):
            from lexilux.usage import Usage
            partial_result = ChatResult(
                text=partial_result,
                usage=Usage(),
                finish_reason="length"  # 假设是截断的
            )
        
        if strategy == "continue":
            # 使用 ChatContinue 继续
            if chat.auto_history:
                history = chat.get_history()
            else:
                history = ChatHistory.from_chat_result(
                    original_prompt or "", partial_result
                )
            
            return ChatContinue.continue_request(
                chat, partial_result, history=history
            )
        
        elif strategy == "retry":
            # 重新开始
            if original_prompt is None:
                raise ValueError("original_prompt required for retry strategy")
            return chat(original_prompt)
        
        elif strategy == "merge":
            # 合并策略：重试并合并结果
            if original_prompt is None:
                raise ValueError("original_prompt required for merge strategy")
            
            retry_result = chat(original_prompt)
            return ChatContinue.merge_results(partial_result, retry_result)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
```

---

## 3. 文档改进建议

### 当前问题

- 缺少"推荐工作流"章节
- 常见场景的完整示例不够
- 错误处理的最佳实践不明确

### 建议内容

#### 1. 添加"推荐工作流"章节

```rst
推荐工作流
==========

场景1：简单对话（推荐）
-----------------------

最简单的使用方式，适合大多数场景：

.. code-block:: python

   from lexilux import Chat
   
   chat = Chat(
       base_url="https://api.example.com/v1",
       api_key="your-key",
       model="gpt-4",
       auto_history=True,  # 启用自动历史
   )
   
   # 直接调用，历史自动管理
   result = chat("What is Python?")
   result = chat("Tell me more")
   
   # 获取完整历史
   history = chat.get_history()

场景2：确保完整响应（推荐）
---------------------------

当需要确保响应完整时（如 JSON 提取）：

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   # 方法1：使用 complete() 方法（推荐）
   result = chat.complete("Write a long JSON", max_tokens=100)
   # 自动处理截断，返回完整结果
   
   # 方法2：手动处理
   result = chat("Write a long JSON", max_tokens=100)
   if result.finish_reason == "length":
       result = chat.continue_if_needed(result)

场景3：流式输出（推荐）
-----------------------

实时显示输出，自动处理中断：

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   try:
       iterator = chat.stream("Long response")
       for chunk in iterator:
           print(chunk.delta, end="", flush=True)
           if chunk.done:
               print(f"\nFinish: {chunk.finish_reason}")
   except ChatStreamInterrupted as e:
       print(f"\nInterrupted. Received: {e.get_partial_text()}")
       # 尝试恢复
       recovered = ChatErrorRecovery.recover_from_interruption(
           chat, e.partial_result
       )
```

#### 2. 添加"错误处理最佳实践"章节

```rst
错误处理最佳实践
================

网络错误处理
-----------

.. code-block:: python

   import time
   from lexilux import Chat
   from lexilux.chat.exceptions import ChatStreamInterrupted
   
   chat = Chat(...)
   max_retries = 3
   
   for attempt in range(max_retries):
       try:
           result = chat("Your prompt")
           break  # 成功
       except requests.RequestException as e:
           if attempt < max_retries - 1:
               wait_time = 2 ** attempt  # 指数退避
               time.sleep(wait_time)
               continue
           raise  # 最后一次尝试失败
   
   流式调用中断处理
   ----------------
   
   .. code-block:: python
   
      iterator = chat.stream("Long response", raise_on_interrupt=False)
      for chunk in iterator:
          print(chunk.delta, end="")
      
      # 检查是否完整
      result = iterator.result.to_chat_result()
      if result.finish_reason != "stop":
          # 不完整，尝试继续
          if chat.auto_history:
              full_result = chat.continue_if_needed(result)
```

---

## 4. 实现优先级建议

### 高优先级（立即实现）

1. **ChatContinue.continue_request 增强**
   - 添加 `history=None` 自动获取
   - 添加 `max_continues` 支持多次继续
   - 影响：大幅简化常用场景

2. **Chat.complete() 方法**
   - 确保完整响应的便捷方法
   - 影响：简化 JSON 提取等场景

### 中优先级（后续版本）

3. **明确的异常类型**
   - `ChatStreamInterrupted`
   - `ChatIncompleteResponse`
   - 影响：提高错误处理的可预测性

4. **错误恢复工具**
   - `ChatErrorRecovery` 类
   - 影响：简化错误恢复逻辑

### 低优先级（长期改进）

5. **文档完善**
   - 推荐工作流
   - 错误处理最佳实践
   - 影响：提高用户体验

---

## 5. 向后兼容性

所有建议的改进都保持向后兼容：

1. **ChatContinue.continue_request**
   - 新参数都有默认值
   - 原有调用方式仍然有效

2. **Chat 类新方法**
   - 都是新增方法，不影响现有 API

3. **异常类型**
   - 新增异常类型，原有异常仍然抛出

---

## 6. 测试建议

为每个新功能添加测试：

```python
def test_continue_request_auto_history():
    """测试自动获取历史"""
    chat = Chat(..., auto_history=True)
    result = chat("Test", max_tokens=10)
    if result.finish_reason == "length":
        # 不提供 history，应该自动获取
        full_result = ChatContinue.continue_request(chat, result)
        assert full_result.finish_reason == "stop"

def test_complete_method():
    """测试 complete 方法"""
    chat = Chat(..., auto_history=True)
    result = chat.complete("Long response", max_tokens=50)
    assert result.finish_reason == "stop"  # 应该自动继续直到完成

def test_stream_interruption():
    """测试流式中断处理"""
    # 模拟网络中断
    # 验证 ChatStreamInterrupted 异常和部分结果
    pass
```

---

## 7. 完整实现示例

### 示例1：增强的 ChatContinue.continue_request 实现

```python
# lexilux/chat/continue_.py

class ChatContinue:
    @staticmethod
    def continue_request(
        chat: Chat,
        last_result: ChatResult,
        *,
        history: ChatHistory | None = None,
        add_continue_prompt: bool = True,
        continue_prompt: str = "continue",
        max_continues: int = 1,
        auto_merge: bool = True,
        **params: Any,
    ) -> ChatResult | list[ChatResult]:
        """
        继续生成请求（增强版）。
        
        如果 history 为 None 且 chat.auto_history=True，自动从 chat.get_history() 获取。
        支持多次继续（max_continues > 1）。
        """
        if last_result.finish_reason != "length":
            raise ValueError(
                f"continue_request requires finish_reason='length', "
                f"got '{last_result.finish_reason}'"
            )
        
        # 自动获取历史
        if history is None:
            if chat.auto_history:
                history = chat.get_history()
                if history is None:
                    # 尝试从 last_result 创建历史
                    # 注意：这需要知道原始 prompt，可能需要改进
                    raise ValueError(
                        "History not available. Either provide history manually "
                        "or ensure the chat call was made with auto_history=True."
                    )
            else:
                raise ValueError(
                    "History is required when auto_history=False. "
                    "Provide history manually or enable auto_history."
                )
        
        all_results = [last_result]
        current_result = last_result
        continue_count = 0
        
        while current_result.finish_reason == "length" and continue_count < max_continues:
            continue_count += 1
            
            # 执行单次继续
            if add_continue_prompt:
                history.add_user(continue_prompt)
            
            continue_result = chat(history.get_messages(), **params)
            all_results.append(continue_result)
            current_result = continue_result
            
            # 更新历史（如果未使用 auto_history）
            if not chat.auto_history:
                history.append_result(continue_result)
        
        # 合并结果
        if auto_merge:
            if len(all_results) == 1:
                return all_results[0]
            return ChatContinue.merge_results(*all_results)
        else:
            return all_results
```

### 示例2：Chat.complete() 方法实现

```python
# lexilux/chat/client.py

class Chat:
    def complete(
        self,
        messages: MessagesLike,
        *,
        max_continues: int = 3,
        ensure_complete: bool = True,
        continue_prompt: str = "continue",
        **params: Any,
    ) -> ChatResult:
        """
        确保获取完整响应，自动处理截断。
        
        这是最推荐的方法，用于需要完整响应的场景（如 JSON 提取）。
        """
        result = self(messages, **params)
        
        if result.finish_reason == "length":
            try:
                # 使用增强的 continue_request
                result = ChatContinue.continue_request(
                    self,
                    result,
                    max_continues=max_continues,
                    continue_prompt=continue_prompt,
                    **params
                )
            except Exception as e:
                if ensure_complete:
                    raise RuntimeError(
                        f"Failed to get complete response after {max_continues} continues: {e}"
                    ) from e
                raise
        
        if ensure_complete and result.finish_reason == "length":
            raise RuntimeError(
                f"Response still truncated after {max_continues} continues. "
                f"Consider increasing max_continues or max_tokens."
            )
        
        return result
    
    def continue_if_needed(
        self,
        result: ChatResult,
        *,
        max_continues: int = 3,
        continue_prompt: str = "continue",
        **params: Any,
    ) -> ChatResult:
        """
        如果结果被截断，自动继续生成直到完成。
        
        如果 result.finish_reason != "length"，直接返回 result。
        """
        if result.finish_reason != "length":
            return result
        
        history = self.get_history() if self.auto_history else None
        if history is None:
            raise ValueError(
                "Cannot continue: history not available. "
                "Enable auto_history or provide history manually."
            )
        
        return ChatContinue.continue_request(
            self,
            result,
            history=history,
            max_continues=max_continues,
            continue_prompt=continue_prompt,
            **params
        )
```

### 示例3：错误处理异常类

```python
# lexilux/chat/exceptions.py

class ChatStreamInterrupted(Exception):
    """流式调用被中断的异常"""
    
    def __init__(
        self,
        message: str,
        partial_result: ChatResult | None = None,
        received_chunks: list[ChatStreamChunk] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.partial_result = partial_result
        self.received_chunks = received_chunks or []
        self.original_error = original_error
    
    def get_partial_text(self) -> str:
        """获取已接收的部分文本"""
        if self.partial_result:
            return self.partial_result.text
        return "".join(chunk.delta for chunk in self.received_chunks)
    
    def get_partial_result(self) -> ChatResult:
        """获取部分结果的 ChatResult 对象"""
        if self.partial_result:
            return self.partial_result
        
        from lexilux.usage import Usage
        partial_text = self.get_partial_text()
        return ChatResult(
            text=partial_text,
            usage=Usage(),
            finish_reason="length"  # 假设是截断的
        )


class ChatIncompleteResponse(Exception):
    """响应不完整的异常（达到最大继续次数后仍被截断）"""
    
    def __init__(
        self,
        message: str,
        final_result: ChatResult,
        continue_count: int,
        max_continues: int,
    ):
        super().__init__(message)
        self.final_result = final_result
        self.continue_count = continue_count
        self.max_continues = max_continues
    
    def get_final_text(self) -> str:
        """获取最终（可能不完整）的文本"""
        return self.final_result.text
```

### 示例4：错误恢复工具实现

```python
# lexilux/chat/recovery.py

class ChatErrorRecovery:
    """错误恢复工具类"""
    
    @staticmethod
    def recover_from_interruption(
        chat: Chat,
        partial_result: ChatResult | str,
        original_prompt: str | None = None,
        *,
        strategy: str = "continue",
        **params: Any,
    ) -> ChatResult:
        """
        从网络中断中恢复。
        
        Args:
            chat: Chat 客户端
            partial_result: 部分结果
            original_prompt: 原始提示（retry/merge 策略需要）
            strategy: 恢复策略
                - "continue": 继续生成（推荐，如果部分结果看起来完整）
                - "retry": 重新开始（如果部分结果不可用）
                - "merge": 合并部分结果和重试结果（保守策略）
        """
        # 转换字符串为 ChatResult
        if isinstance(partial_result, str):
            from lexilux.usage import Usage
            partial_result = ChatResult(
                text=partial_result,
                usage=Usage(),
                finish_reason="length"
            )
        
        if strategy == "continue":
            # 使用 ChatContinue 继续
            if chat.auto_history:
                history = chat.get_history()
                if history is None:
                    # 如果历史不存在，从部分结果创建
                    if original_prompt:
                        history = ChatHistory.from_chat_result(
                            original_prompt, partial_result
                        )
                    else:
                        raise ValueError(
                            "Cannot continue: history not available and "
                            "original_prompt not provided."
                        )
            else:
                if original_prompt:
                    history = ChatHistory.from_chat_result(
                        original_prompt, partial_result
                    )
                else:
                    raise ValueError(
                        "Cannot continue: auto_history=False and "
                        "original_prompt not provided."
                    )
            
            return ChatContinue.continue_request(
                chat, partial_result, history=history, **params
            )
        
        elif strategy == "retry":
            # 重新开始
            if original_prompt is None:
                raise ValueError("original_prompt required for retry strategy")
            return chat(original_prompt, **params)
        
        elif strategy == "merge":
            # 合并策略：重试并合并结果
            if original_prompt is None:
                raise ValueError("original_prompt required for merge strategy")
            
            retry_result = chat(original_prompt, **params)
            return ChatContinue.merge_results(partial_result, retry_result)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Use 'continue', 'retry', or 'merge'")
```

### 示例5：实际使用场景对比

#### 场景：提取 JSON（当前 vs 改进后）

**当前实现**：
```python
chat = Chat(..., auto_history=True)

# 调用 LLM
result = chat("Extract data as JSON", max_tokens=100)

# 检查并处理截断
if result.finish_reason == "length":
    # 需要手动获取历史
    history = chat.get_history()
    if history is None:
        history = ChatHistory.from_chat_result("Extract data as JSON", result)
    
    # 继续生成
    continue_result = ChatContinue.continue_request(chat, history, result)
    
    # 合并结果
    full_result = ChatContinue.merge_results(result, continue_result)
    
    # 如果继续结果也被截断，需要再次处理
    if continue_result.finish_reason == "length":
        # 需要再次继续...
        pass
else:
    full_result = result

# 提取 JSON
json_data = json.loads(full_result.text)
```

**改进后实现**：
```python
chat = Chat(..., auto_history=True)

# 方法1：使用 complete()（最简单）
result = chat.complete("Extract data as JSON", max_tokens=100)
json_data = json.loads(result.text)

# 方法2：使用 continue_if_needed()
result = chat("Extract data as JSON", max_tokens=100)
full_result = chat.continue_if_needed(result, max_continues=3)
json_data = json.loads(full_result.text)

# 方法3：使用增强的 continue_request
result = chat("Extract data as JSON", max_tokens=100)
if result.finish_reason == "length":
    # 自动获取历史，自动多次继续，自动合并
    full_result = ChatContinue.continue_request(
        chat, result, max_continues=3
    )
    json_data = json.loads(full_result.text)
else:
    json_data = json.loads(result.text)
```

**代码行数对比**：
- 当前：~20 行（包含错误处理）
- 改进后：1-3 行

---

## 总结

这些改进将显著提升 lexilux 的易用性，特别是在处理：
- 输出截断场景
- 网络错误恢复
- 确保响应完整性

同时保持向后兼容，不会破坏现有代码。

建议优先实现高优先级功能，它们能立即改善用户体验。

### 预期收益

1. **代码量减少**：常用场景从 20+ 行减少到 1-3 行
2. **错误减少**：自动处理常见错误（如忘记合并结果）
3. **可读性提升**：代码意图更清晰
4. **维护性提升**：减少重复代码

### 实施建议

1. **第一阶段**：实现 `ChatContinue.continue_request` 增强（高优先级）
2. **第二阶段**：添加 `Chat.complete()` 和 `Chat.continue_if_needed()` 方法
3. **第三阶段**：添加异常类型和错误恢复工具
4. **第四阶段**：完善文档和示例

