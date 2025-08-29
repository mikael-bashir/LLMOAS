from dotenv import load_dotenv # <-- 1. ADD THIS IMPORT
load_dotenv() # <-- 2. ADD THIS LINE TO LOAD THE .ENV FILE

from quart import Quart, request, jsonify, redirect
from quart_session import Session
from quart_cors import cors
import logging
import uuid
import redis # <-- NEW: Import the redis library
import os # <-- NEW: Import os to read the environment variable
from typing import Dict, Any
import asyncio

from fastmcp import Client
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_xai import ChatXAI
import json
from langchain_core.tools import Tool # <-- NEW: Import Tool from langchain_core
from google import genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. CHANGE Flask to Quart and add CORS
app = Quart(__name__)
app = cors(app, allow_origin=["http://localhost:3000"], allow_credentials=True)

app.config["SECRET_KEY"] = "super-secret-key-change-in-production"
# 2. CHANGE session type to 'redis'
app.config["SESSION_TYPE"] = "redis"
# 3. NEW: Tell quart-session where your Redis server is
app.config["SESSION_REDIS"] = redis.from_url(os.getenv("REDIS_URL"))
Session(app)

authenticated_clients: Dict[str, Any] = {}
# Add httpx for the auth flow
# import httpx

# # Helper function to get the Redis client from the app config
# def get_redis_client():
#     return app.config["SESSION_REDIS"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 2. Make the route asynchronous with 'async def'
@app.route("/api/mcp/start-auth", methods=["POST"])
async def authenticate_mcp_server():
    data = await request.get_json()
    server_url = data.get("url")
    server_name = data.get("name", "Unnamed Server")
    if not server_url:
        return jsonify({"success": False, "message": "url is required"}), 400

    try:
        client = Client(server_url, auth="oauth")

        async with client:
            await client.ping()
        
        server_id = str(uuid.uuid4())
        authenticated_clients[server_id] = {
            "client": client,
            "server_url": server_url,
            "server_name": server_name,
            "authenticated_at": "now",
            "auth_headers": getattr(client, '_auth_headers', {}),  # Store auth headers if available
            "auth_token": getattr(client, '_auth_token', None)     # Store auth token if available
        }
        return jsonify({"success": True, "server_id": server_id})

    except Exception as e:
        logger.error(f"Native OAuth flow failed: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/mcp/servers/<server_id>/tools", methods=["GET"])
async def get_mcp_tools(server_id):
    """Get available tools from an authenticated FastMCP server."""
    try:
        if server_id not in authenticated_clients:
            return jsonify({"error": "FastMCP server not authenticated"}), 401

        client = authenticated_clients[server_id]["client"]

        async with client:
            tools = await client.list_tools()
            formatted_tools = []
            for tool in tools:
                if hasattr(tool, 'dict'):
                    tool_data = tool.dict()
                else:
                    tool_data = {"name": str(tool), "description": ""}

                formatted_tools.append({
                    "name": tool_data.get("name", str(tool)),
                    "description": tool_data.get("description", ""),
                    "inputSchema": tool_data.get("inputSchema", {})
                })
            return jsonify({"tools": formatted_tools})

    except Exception as e:
        logger.error(f"Error fetching tools: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/mcp/servers/<server_id>/call", methods=["POST"])
async def call_mcp_tool(server_id):
    """Call a tool on an authenticated FastMCP server."""
    try:
        if server_id not in authenticated_clients:
            return jsonify({"success": False, "error": "Server not authenticated"}), 401

        data = await request.get_json()
        tool_name = data.get("tool_name")
        arguments = data.get("arguments", {})

        if not tool_name:
            return jsonify({"success": False, "error": "tool_name is required"}), 400

        client = authenticated_clients[server_id]["client"]

        async with client:
            result = await client.call_tool(tool_name, arguments)
            return jsonify({"success": True, "result": result.dict() if hasattr(result, 'dict') else str(result)})

    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/mcp/servers", methods=["GET"])
async def list_authenticated_servers():
    """List all authenticated FastMCP servers."""
    try:
        servers = []
        for server_id, client_info in authenticated_clients.items():
            servers.append({
                "id": server_id,
                "server_id": server_id,  # Keep both for compatibility
                "server_url": client_info["server_url"],
                "url": client_info["server_url"],  # Keep both for compatibility
                "name": client_info.get("server_name", "Unknown"),
                "authType": client_info.get("auth_type", "oauth"),  # Fixed field name to match frontend expectation
                "authenticated_at": client_info["authenticated_at"],
                "status": "connected",
                "isActive": True,  # Added isActive field expected by frontend
                "description": client_info.get("description", ""),  # Added description field
                "credentials": {}  # Added credentials field expected by frontend
            })

        return jsonify(servers)  # Return array directly instead of wrapping in {"servers": ...}

    except Exception as e:
        logger.error(f"Error in list_authenticated_servers: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/mcp/servers/<server_id>/ping", methods=["GET"])
async def ping_mcp_server(server_id):
    """Ping an MCP server to check connection status."""
    try:
        if server_id not in authenticated_clients:
            return jsonify({"connected": False, "error": "Server not authenticated"}), 404

        client = authenticated_clients[server_id]["client"]

        async with client:
            try:
                await client.ping()
                return jsonify({"connected": True})
            except Exception as e:
                logger.error(f"Ping failed for server {server_id}: {e}")
                return jsonify({"connected": False})

    except Exception as e:
        logger.error(f"Error in ping_mcp_server: {e}")
        return jsonify({"connected": False, "error": str(e)}), 500

@app.route("/api/mcp/servers/<server_id>", methods=["DELETE"])
async def disconnect_mcp_server(server_id):
    """Disconnect from an MCP server."""
    try:
        if server_id not in authenticated_clients:
            return jsonify({"error": "Server not found"}), 404

        client_info = authenticated_clients[server_id]
        client = client_info["client"]

        # Close client connection if it has a close method
        if hasattr(client, 'close'):
            async with client:
                await client.close()

        # Remove from authenticated clients
        del authenticated_clients[server_id]

        return jsonify({
            "status": "disconnected",
            "message": f"Server {server_id} disconnected successfully"
        })

    except Exception as e:
        logger.error(f"Error in disconnect_mcp_server: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat/langchain", methods=["POST"])
async def chat_with_langchain():
    """Chat endpoint using LangChain orchestration with MCP tools and Grok."""
    try:
        data = await request.get_json()
        messages = data.get("messages", [])
        
        if not messages:
            return jsonify({"error": "Messages are required"}), 400

        logger.info(f"[v0] Starting LangChain chat with {len(authenticated_clients)} authenticated MCP servers")
        
        all_tools = []
        successful_servers = []
        failed_servers = []
        
        for server_id, client_info in authenticated_clients.items():
            server_url = client_info["server_url"]
            server_name = client_info.get("server_name", "Unknown")
            
            logger.info(f"[v0] Loading tools from {server_name} using authenticated FastMCP client")
            
            try:
                client = client_info["client"]
                
                async with client:
                    # Get tools directly from FastMCP client
                    tools_list = await client.list_tools()
                    logger.info(f"[v0] FastMCP client returned {len(tools_list)} tools from {server_name}")
                    
                    # Convert FastMCP tools to LangChain tools manually since we can't use streamable client
                    server_tools = []
                    for tool in tools_list:
                        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                        tool_description = tool.description if hasattr(tool, 'description') else f"Tool: {tool_name}"
                        
                        # Create a wrapper function for the tool
                        async def tool_wrapper(tool_name=tool_name, **kwargs):
                            try:
                                result = await client.call_tool(tool_name, kwargs)
                                return str(result)
                            except Exception as e:
                                return f"Error calling tool {tool_name}: {str(e)}"
                        
                        # Create LangChain tool
                        langchain_tool = Tool(
                            name=tool_name,
                            description=tool_description,
                            func=tool_wrapper
                        )
                        server_tools.append(langchain_tool)
                    
                    logger.info(f"[v0] Converted {len(server_tools)} FastMCP tools to LangChain format for {server_name}")
                    all_tools.extend(server_tools)
                    successful_servers.append(server_name)
                        
            except Exception as e:
                logger.error(f"[v0] Failed to load tools from {server_name}: {e}")
                failed_servers.append(f"{server_name}: {str(e)}")
                continue

        logger.info(f"[v0] Creating agent with {len(all_tools)} tools using authenticated FastMCP clients")
        
        model = ChatXAI(
            model="grok-2",
            xai_api_key=os.getenv("XAI_API_KEY"),
            temperature=0.7
        )
        
        agent = create_react_agent(model, all_tools)
        
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            if msg.get("role") == "user":
                langchain_messages.append({"role": "human", "content": msg.get("content", "")})
            elif msg.get("role") == "assistant":
                langchain_messages.append({"role": "ai", "content": msg.get("content", "")})
        
        logger.info(f"[v0] Invoking agent with {len(all_tools)} MCP tools: {[tool.name for tool in all_tools]}")
        
        response = await agent.ainvoke({"messages": langchain_messages})
        
        # Extract response content
        response_content = ""
        if hasattr(response, 'content'):
            response_content = response.content
        elif isinstance(response, dict) and 'messages' in response:
            last_msg = response['messages'][-1] if response['messages'] else None
            if last_msg and hasattr(last_msg, 'content'):
                response_content = last_msg.content
            else:
                response_content = str(last_msg) if last_msg else str(response)
        else:
            response_content = str(response)
        
        logger.info(f"[v0] Agent response: {response_content[:100]}...")
        
        return jsonify({
            "success": True,
            "response": response_content,
            "tools_loaded": len(all_tools),
            "successful_servers": successful_servers,
            "failed_servers": failed_servers,
            "model": "grok-2"
        })

    except Exception as e:
        logger.error(f"[v0] Error in LangChain chat: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/chat/gemini", methods=["POST"])
async def chat_with_gemini():
    """
    Chat endpoint using the genai.Client pattern with in-memory FastMCP clients,
    correctly managing concurrent connections with TaskGroup.
    """
    try:
        data = await request.get_json()
        messages = data.get("messages", [])
        
        if not messages:
            return jsonify({"error": "Messages are required"}), 400

        logger.info(f"[v0] Starting Gemini chat with {len(authenticated_clients)} in-memory servers")
        
        # 1. Create a list of the client objects from your dictionary
        mcp_clients = [info["client"] for info in authenticated_clients.values()]
        
        mcp_sessions = []
        successful_servers = []
        
        # 2. Use a TaskGroup to manage all client connections simultaneously
        async with asyncio.TaskGroup() as tg:
            
            # --- THIS IS THE CORRECTED LOGIC ---
            # Create a list to hold the tasks
            connection_tasks = []
            for client in mcp_clients:
                # Start each client's context manager and add the task to our list
                task = tg.create_task(client.__aenter__())
                connection_tasks.append(task)
            
            # Wait for all connection tasks to complete
            await asyncio.gather(*connection_tasks)
            
            # Now that all connections are guaranteed to be OPEN, collect the sessions
            for client in mcp_clients:
                mcp_sessions.append(client.session)
            
            successful_servers = [info.get("server_name", "Unknown") for info in authenticated_clients.values()]
            logger.info(f"[v0] Collected {len(mcp_sessions)} MCP sessions")

            # 3. Configure and call Gemini while the connections are open
            gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            # Format conversation history into a single string
            conversation_history = [f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}" for msg in messages[:-1]]
            latest_message = messages[-1].get("content", "") if messages else ""
            context = "Previous conversation:\n" + "\n".join(conversation_history) + "\n\nCurrent message: " if conversation_history else ""
            full_prompt = context + latest_message

            response = await gemini_client.aio.models.generate_content(
                model="models/gemini-1.5-flash",
                contents=full_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=mcp_sessions,  # Pass the FastMCP client session
                ),
            )
            
            # The TaskGroup will automatically close all client connections
            # when this 'async with' block exits.

        response_text = response.text if hasattr(response, 'text') else str(response)
        logger.info(f"[v0] Gemini response: {response_text[:100]}...")
        
        return jsonify({
            "success": True,
            "response": response_text,
            "mcp_tools": len(mcp_sessions),
            "successful_servers": successful_servers,
            "model": "gemini-1.5-flash"
        })

    except Exception as e:
        logger.error(f"[v0] Error in Gemini chat: {e}")
        import traceback
        logger.error(f"[v0] Full traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True, port=5328, threaded=True)
