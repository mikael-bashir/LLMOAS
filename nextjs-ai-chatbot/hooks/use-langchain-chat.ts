"use client"

import type React from "react"

import { useState, useCallback } from "react"
import { generateUUID } from "@/lib/utils"
import { toast } from "sonner"

export interface UIMessage {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  createdAt?: Date
  parts: Array<{ type: "text"; text: string }>
  experimental_attachments?: Array<any>
}

export interface Attachment {
  name: string
  contentType: string
  size: number
  url: string
}

export type ChatStatus = "ready" | "streaming" | "submitted" | "error"

interface UseLangChainChatOptions {
  id: string
  initialMessages: UIMessage[]
  body?: Record<string, any>
  onFinish?: () => void
  onError?: () => void
}

export interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  createdAt?: Date
}

export function useLangChainChat({ id, initialMessages, body = {}, onFinish, onError }: UseLangChainChatOptions) {
  const [messages, setMessages] = useState<UIMessage[]>(initialMessages)
  const [input, setInput] = useState("")
  const [status, setStatus] = useState<ChatStatus>("ready")

  const handleSubmit = useCallback(
    async (
      e?: React.FormEvent,
      options?: { experimental_attachments?: Attachment[] },
    ): Promise<string | null | undefined> => {
      if (e) e.preventDefault()

      if (!input.trim() && !options?.experimental_attachments?.length) return null

      const userMessage: UIMessage = {
        id: generateUUID(),
        role: "user",
        content: input,
        createdAt: new Date(),
        parts: [{ type: "text", text: input }],
        experimental_attachments: options?.experimental_attachments,
      }

      setMessages((prev) => [...prev, userMessage])
      setInput("")
      setStatus("streaming")

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            id,
            messages: [...messages, userMessage],
            ...body,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error("No response body")
        }

        let assistantMessage: UIMessage = {
          id: generateUUID(),
          role: "assistant",
          content: "",
          createdAt: new Date(),
          parts: [{ type: "text", text: "" }],
        }

        setMessages((prev) => [...prev, assistantMessage])

        const decoder = new TextDecoder()
        let buffer = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() || ""

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === "text-delta") {
                  assistantMessage = {
                    ...assistantMessage,
                    content: assistantMessage.content + data.content,
                  }
                  assistantMessage.parts[0].text = assistantMessage.content
                  setMessages((prev) => prev.map((msg) => (msg.id === assistantMessage.id ? assistantMessage : msg)))
                }
              } catch (e) {
                // Ignore parsing errors for non-JSON lines
              }
            }
          }
        }

        setStatus("ready")
        onFinish?.()
        return assistantMessage.content
      } catch (error) {
        console.error("Chat error:", error)
        setStatus("error")
        onError?.()
        toast.error("An error occurred, please try again!")
        return null
      }
    },
    [input, messages, id, body, onFinish, onError],
  )

  const setMessagesWrapper = useCallback(
    (messagesOrUpdater: UIMessage[] | ((messages: UIMessage[]) => UIMessage[])) => {
      if (typeof messagesOrUpdater === "function") {
        setMessages(messagesOrUpdater)
      } else {
        setMessages(messagesOrUpdater)
      }
    },
    [],
  )

  const append = useCallback(async (message: UIMessage): Promise<string | null | undefined> => {
    setMessages((prev) => [...prev, message])
    return message.content
  }, [])

  const reload = useCallback(async (): Promise<string | null | undefined> => {
    // Implement reload logic if needed
    console.log("Reload not implemented yet")
    return null
  }, [])

  const stop = useCallback(() => {
    setStatus("ready")
  }, [])

  return {
    messages,
    setMessages: setMessagesWrapper,
    input,
    setInput,
    handleSubmit,
    append,
    reload,
    stop,
    status,
  }
}
