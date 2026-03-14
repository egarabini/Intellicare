import { useState, useRef } from 'react'
import { Button, Paper, ScrollArea, Text, Textarea, Stack, Badge } from '@mantine/core'

interface Props {
  encounterContext?: string
}

export function SLMAssistant({ encounterContext }: Props) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const handleAsk = async () => {
    if (!question.trim()) return
    setAnswer('')
    setError(null)
    setStreaming(true)

    abortRef.current = new AbortController()
    const token = sessionStorage.getItem('oidc.access_token') ?? ''

    try {
      const res = await fetch('/slm/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          question,
          context: encounterContext ?? '',
          stream: true,
        }),
        signal: abortRef.current.signal,
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        chunk.split('\n').forEach(line => {
          if (line.startsWith('data: ')) {
            const tok = line.slice(6)
            if (tok !== '[DONE]') setAnswer(prev => prev + tok)
          }
        })
      }
    } catch (err: unknown) {
      if ((err as Error).name !== 'AbortError') {
        setError((err as Error).message)
      }
    } finally {
      setStreaming(false)
    }
  }

  const handleStop = () => {
    abortRef.current?.abort()
    setStreaming(false)
  }

  return (
    <Stack gap="sm">
      <Textarea
        label="Pergunta ao Assistente IA"
        placeholder="Ex: Sugestão de CID para hipertensão com nefropatia..."
        minRows={3}
        value={question}
        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setQuestion(e.currentTarget.value)}
        disabled={streaming}
      />

      <Button
        onClick={streaming ? handleStop : handleAsk}
        color={streaming ? 'red' : 'blue'}
        disabled={!streaming && !question.trim()}
      >
        {streaming ? 'Parar' : 'Perguntar'}
      </Button>

      {error && <Text c="red" size="sm">{error}</Text>}

      {(answer || streaming) && (
        <Paper withBorder p="sm" radius="md">
          <Stack gap={4}>
            <Badge color={streaming ? 'yellow' : 'green'} variant="light" size="sm">
              {streaming ? 'Gerando...' : 'Concluído'}
            </Badge>
            <ScrollArea h={300}>
              <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>{answer}</Text>
            </ScrollArea>
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}
