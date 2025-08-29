export interface MCPServer {
  id: string
  name: string
  url: string
  description: string | null
  authType: "none" | "bearer" | "oauth" | "apikey"
  credentials: unknown
  isActive: boolean
  userId: string
  createdAt: Date
  updatedAt: Date
}

export interface MCPTool {
  name: string
  description: string
  inputSchema: any
}

export interface MCPAuthResult {
  success: boolean
  message: string
  server_id?: string
  authorization_url?: string // Added for OAuth flow
}

export interface MCPToolResult {
  success: boolean
  result?: any
  error?: string
}

class MCPFlaskService {
  private baseUrl = "/api/flask"

  async startOAuthFlow(serverUrl: string, serverName: string): Promise<MCPAuthResult> {
    const response = await fetch(`${this.baseUrl}/mcp/start-auth`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: serverUrl, name: serverName }),
    })

    if (!response.ok) {
      throw new Error(`OAuth start failed: ${response.statusText}`)
    }

    return response.json()
  }

  async authenticateServer(serverData: {
    name: string
    url: string
    authType: string
    credentials?: any
  }): Promise<MCPAuthResult> {
    if (serverData.authType === "oauth") {
      return await this.startOAuthFlow(serverData.url, serverData.name)
    }

    // For non-OAuth authentication, use the existing endpoint
    const response = await fetch(`${this.baseUrl}/mcp/authenticate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(serverData),
    })

    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.statusText}`)
    }

    return response.json()
  }

  async getServerTools(serverId: string): Promise<MCPTool[]> {
    const response = await fetch(`${this.baseUrl}/mcp/servers/${serverId}/tools`)

    if (!response.ok) {
      throw new Error(`Failed to get tools: ${response.statusText}`)
    }

    const data = await response.json()
    return data.tools || []
  }

  async callTool(serverId: string, toolName: string, args: any): Promise<MCPToolResult> {
    const response = await fetch(`${this.baseUrl}/mcp/servers/${serverId}/call`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        tool_name: toolName,
        arguments: args,
      }),
    })

    if (!response.ok) {
      throw new Error(`Tool call failed: ${response.statusText}`)
    }

    return response.json()
  }

  async getAuthenticatedServers(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/mcp/servers`)

    if (!response.ok) {
      throw new Error(`Failed to get servers: ${response.statusText}`)
    }

    const data = await response.json()
    return data.servers || []
  }

  async disconnectServer(serverId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/mcp/servers/${serverId}`, {
      method: "DELETE",
    })

    if (!response.ok) {
      throw new Error(`Failed to disconnect server: ${response.statusText}`)
    }
  }

  async saveServer(serverData: {
    name: string
    url: string
    description: string
    authType: string
    credentials?: any
    flaskServerId: string
  }): Promise<MCPAuthResult> {
    const response = await fetch(`${this.baseUrl}/mcp/servers`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(serverData),
    })

    if (!response.ok) {
      throw new Error(`Failed to save server: ${response.statusText}`)
    }

    return response.json()
  }

  async pingServer(serverId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/mcp/servers/${serverId}/ping`)
      return response.ok
    } catch {
      return false
    }
  }
}

export const mcpFlaskService = new MCPFlaskService()
