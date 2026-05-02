"""
MCP Server for TrainCLI — enables Claude Code to train ML models.
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from traincli.core import run_pipeline, profile_dataset, suggest_target


# Initialize MCP server
app = Server("traincli")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="train_model",
            description="Train a machine learning model on a CSV file. Automatically profiles data, cleans it, selects the best model via cross-validation, and exports everything.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Path to CSV file"
                    },
                    "target": {
                        "type": "string",
                        "description": "Target column name to predict"
                    },
                    "model": {
                        "type": "string",
                        "description": "Optional: specific model to use (e.g., 'random_forest', 'gradient_boosting'). If not provided, auto-selects via CV.",
                        "default": None
                    },
                    "task": {
                        "type": "string",
                        "enum": ["classification", "regression"],
                        "description": "Optional: override problem type detection",
                        "default": None
                    },
                    "drop": {
                        "type": "string",
                        "description": "Optional: comma-separated columns to drop (e.g., 'col1,col2')",
                        "default": None
                    },
                    "output": {
                        "type": "string",
                        "description": "Output directory path",
                        "default": "./output"
                    }
                },
                "required": ["data", "target"]
            }
        ),
        Tool(
            name="profile_dataset",
            description="Profile a CSV dataset to understand its structure, detect issues, and check for data leakage. Does not train a model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Path to CSV file"
                    },
                    "target": {
                        "type": "string",
                        "description": "Optional: target column for leakage detection",
                        "default": None
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="suggest_target",
            description="Suggest the best target column for a dataset based on heuristics (column names, cardinality, position).",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Path to CSV file"
                    }
                },
                "required": ["data"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "train_model":
        try:
            result = run_pipeline(
                data_path=arguments["data"],
                target=arguments["target"],
                model_key=arguments.get("model"),
                task=arguments.get("task"),
                out=arguments.get("output", "./output"),
                auto=True,
                drop=arguments.get("drop")
            )
            
            # Format response
            metrics = result["results"]["metrics"]
            model_label = result["results"]["model_entry"]["label"]
            confidence = result["results"]["confidence"]
            
            response = {
                "status": "success",
                "model": model_label,
                "metrics": metrics,
                "confidence": confidence,
                "output_directory": result["output_dir"],
                "files": [
                    "model.pkl",
                    "train.py",
                    "report.md",
                    "metrics.json",
                    "session.json"
                ],
                "interpretation": result["results"].get("interpretation", "")
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "error": str(e)
                }, indent=2)
            )]
    
    elif name == "profile_dataset":
        try:
            prof = profile_dataset(
                data_path=arguments["data"],
                target=arguments.get("target")
            )
            
            # Simplify profile for response
            response = {
                "status": "success",
                "rows": prof["rows"],
                "cols": prof["cols"],
                "target": prof["target"],
                "null_percentage": prof["null_pct"],
                "issues_found": len(prof["issues"]),
                "issues": prof["issues"],
                "leakage_suspects": prof.get("leakage", []),
                "columns": {
                    col: {
                        "type": info.get("type", info.get("dtype")),
                        "null_pct": info.get("null_pct", 0),
                        "nunique": info.get("nunique", 0)
                    }
                    for col, info in prof["columns"].items()
                }
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "error": str(e)
                }, indent=2)
            )]
    
    elif name == "suggest_target":
        try:
            suggestion = suggest_target(arguments["data"])
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    **suggestion
                }, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "error": str(e)
                }, indent=2)
            )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": f"Unknown tool: {name}"
            }, indent=2)
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
