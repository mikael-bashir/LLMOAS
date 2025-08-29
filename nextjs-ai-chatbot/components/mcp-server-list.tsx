"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { TrashIcon } from "./icons"
import { toast } from "sonner"
import type { MCPServer } from "@/lib/types/mcp"
import { mcpFlaskService, type MCPTool } from "@/lib/services/mcp-flask-service"

interface MCPServerListProps {
  refreshTrigger?: number
}

interface ExtendedMCPServer extends MCPServer {
  isConnected?: boolean
  tools?: MCPTool[]
  flaskServerId?: string
}

export function MCPServerList({ refreshTrigger }: MCPServerListProps) {
  const [servers, setServers] = useState<ExtendedMCPServer[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchServers = async () => {
    try {
      const [dbResponse, flaskServers] = await Promise.all([
        fetch("/api/mcp/servers"),
        mcpFlaskService.getAuthenticatedServers().catch(() => []),
      ])

      if (!dbResponse.ok) throw new Error("Failed to fetch servers")
      const dbServers = await dbResponse.json()

      const enhancedServers = await Promise.all(
        dbServers.map(async (server: MCPServer) => {
          const flaskServer = flaskServers.find((fs: any) => fs.url === server.url)
          const isConnected = flaskServer ? await mcpFlaskService.pingServer(flaskServer.id).catch(() => false) : false

          let tools: MCPTool[] = []
          if (isConnected && flaskServer) {
            try {
              tools = await mcpFlaskService.getServerTools(flaskServer.id)
            } catch (error) {
              console.error(`Failed to get tools for ${server.name}:`, error)
            }
          }

          return {
            ...server,
            isConnected,
            tools,
            flaskServerId: flaskServer?.id,
          }
        }),
      )

      setServers(enhancedServers)
    } catch (error) {
      console.error("Error fetching MCP servers:", error)
      toast.error("Failed to load MCP servers")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchServers()
  }, [refreshTrigger])

  const toggleServer = async (serverId: string, isActive: boolean) => {
    try {
      const server = servers.find((s) => s.id === serverId)

      if (isActive && server && !server.isConnected) {
        const authResult = await mcpFlaskService.authenticateServer({
          name: server.name,
          url: server.url,
          authType: server.authType,
          credentials: server.credentials,
        })

        if (!authResult.success) {
          throw new Error("Failed to connect to MCP server")
        }
      } else if (!isActive && server?.flaskServerId) {
        await mcpFlaskService.disconnectServer(server.flaskServerId)
      }

      const response = await fetch(`/api/mcp/servers/${serverId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ isActive }),
      })

      if (!response.ok) throw new Error("Failed to update server")

      await fetchServers()
      toast.success(`Server ${isActive ? "enabled" : "disabled"}`)
    } catch (error) {
      console.error("Error updating server:", error)
      toast.error(error instanceof Error ? error.message : "Failed to update server")
    }
  }

  const deleteServer = async (serverId: string) => {
    if (!confirm("Are you sure you want to delete this MCP server?")) return

    try {
      const server = servers.find((s) => s.id === serverId)

      if (server?.flaskServerId) {
        await mcpFlaskService.disconnectServer(server.flaskServerId)
      }

      const response = await fetch(`/api/mcp/servers/${serverId}`, {
        method: "DELETE",
      })

      if (!response.ok) throw new Error("Failed to delete server")

      setServers(servers.filter((server) => server.id !== serverId))
      toast.success("Server deleted successfully")
    } catch (error) {
      console.error("Error deleting server:", error)
      toast.error("Failed to delete server")
    }
  }

  if (isLoading) {
    return <div className="text-center py-4">Loading MCP servers...</div>
  }

  if (servers.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No MCP servers configured yet.</p>
        <p className="text-sm">Add your first server to get started.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {servers.map((server) => (
        <Card key={server.id}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">{server.name}</CardTitle>
                <CardDescription className="text-sm">{server.url}</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={server.isConnected ? "default" : "secondary"}>
                  {server.isConnected ? "Connected" : "Disconnected"}
                </Badge>
                <Badge variant={server.authType === "none" ? "secondary" : "default"}>
                  {server.authType === "none" ? "No Auth" : server.authType.toUpperCase()}
                </Badge>
                <Switch checked={server.isActive} onCheckedChange={(checked) => toggleServer(server.id, checked)} />
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {server.description && <p className="text-sm text-muted-foreground mb-2">{server.description}</p>}
            {server.isConnected && server.tools && server.tools.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-muted-foreground mb-1">Available Tools:</p>
                <div className="flex flex-wrap gap-1">
                  {server.tools.map((tool) => (
                    <Badge key={tool.name} variant="outline" className="text-xs">
                      {tool.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => deleteServer(server.id)}
                className="text-destructive hover:text-destructive"
              >
                <TrashIcon size={14} />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
