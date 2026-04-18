/**
 * SSE 流式请求 composable
 * 用于所有金融分析页面的流式 API 调用
 * 
 * 事件类型:
 *   thinking  - AI 思考过程
 *   chunk     - 正文 token 片段
 *   done      - 完成, data 字段为解析后的 JSON
 *   error     - 错误
 */
import { ref } from 'vue'

/**
 * @param {string} url - API 地址
 * @param {Object} options
 * @param {Function} options.onThinking  - 收到思考片段回调 (text)
 * @param {Function} options.onChunk     - 收到正文片段回调 (text)
 * @param {Function} options.onDone      - 完成回调 (parsedJSON)
 * @param {Function} options.onError     - 错误回调 (message)
 */
export function useSSE() {
  const loading = ref(false)
  const error = ref('')
  const thinkingText = ref('')
  const streamText = ref('')
  const result = ref(null)

  let abortController = null

  const abort = () => {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  /**
   * 发起 SSE 流式请求
   * @param {string} url 
   * @param {Object} body - POST body
   * @param {Object} callbacks - { onThinking, onChunk, onDone, onError }
   */
  const fetchSSE = async (url, body, callbacks = {}) => {
    abort()
    loading.value = true
    error.value = ''
    thinkingText.value = ''
    streamText.value = ''
    result.value = null

    abortController = new AbortController()

    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(body),
        signal: abortController.signal,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `请求失败 (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const dataStr = line.slice(6).trim()
          if (!dataStr || dataStr === '[DONE]') continue

          try {
            const evt = JSON.parse(dataStr)
            switch (evt.type) {
              case 'thinking':
                thinkingText.value += evt.content || ''
                callbacks.onThinking?.(evt.content)
                break
              case 'chunk':
                streamText.value += evt.content || ''
                callbacks.onChunk?.(evt.content)
                break
              case 'done':
                result.value = evt.data
                loading.value = false
                callbacks.onDone?.(evt.data)
                return evt.data
              case 'error':
                throw new Error(evt.message || '分析失败')
            }
          } catch (parseErr) {
            if (parseErr.message && !parseErr.message.includes('JSON')) {
              throw parseErr
            }
          }
        }
      }

      // 如果流结束但没有 done 事件
      if (!result.value) {
        throw new Error('流式响应异常结束')
      }
    } catch (e) {
      if (e.name === 'AbortError') return
      error.value = e.message
      callbacks.onError?.(e.message)
    } finally {
      loading.value = false
      abortController = null
    }
  }

  return {
    loading,
    error,
    thinkingText,
    streamText,
    result,
    fetchSSE,
    abort,
  }
}
