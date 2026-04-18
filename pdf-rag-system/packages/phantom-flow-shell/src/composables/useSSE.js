/**
 * SSE streaming request composable.
 * Generic — works with any backend that sends `data: {type, content/data/message}` events.
 *
 * Event types:
 *   thinking  - AI thinking process
 *   chunk     - Content token fragment
 *   done      - Complete, data field is parsed JSON
 *   error     - Error
 */
import { ref } from 'vue'

/**
 * @param {Object} [globalOptions]
 * @param {() => string|null} [globalOptions.getToken] - Token provider, defaults to localStorage
 */
export function useSSE(globalOptions = {}) {
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

  const getToken = globalOptions.getToken || (() => localStorage.getItem('access_token'))

  /**
   * Start an SSE streaming request.
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
      const token = getToken()
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
        signal: abortController.signal,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Request failed (${res.status})`)
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
                throw new Error(evt.message || 'Stream error')
            }
          } catch (parseErr) {
            if (parseErr.message && !parseErr.message.includes('JSON')) {
              throw parseErr
            }
          }
        }
      }

      if (!result.value) {
        throw new Error('Stream ended unexpectedly')
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
