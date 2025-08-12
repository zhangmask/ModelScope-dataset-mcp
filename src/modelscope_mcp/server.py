"""ModelScope数据集即时查询MCP服务器

基于MCP协议的数据集查询服务器主入口。
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    ServerCapabilities,
    ToolsCapability,
)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.modelscope_mcp.core.config import Config
from src.modelscope_mcp.core.logger import get_logger, setup_logging
from src.modelscope_mcp.tools.list_datasets import ListDatasetsHandler
from src.modelscope_mcp.tools.query_dataset import QueryDatasetHandler
from src.modelscope_mcp.tools.get_dataset_info import GetDatasetInfoHandler
from src.modelscope_mcp.tools.filter_samples import FilterSamplesHandler
from src.modelscope_mcp.services.database import DatabaseService
from src.modelscope_mcp.services.cache import CacheService


class ModelScopeMCPServer:
    """ModelScope MCP服务器"""
    
    def __init__(self, config: Config):
        """初始化服务器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__, config)
        
        # 创建MCP服务器实例
        self.server = Server(self.config.mcp_server_name)
        
        # 初始化服务
        self.db_service = None
        self.cache_service = None
        
        # 初始化工具处理器
        self.tool_handlers = {}
        
        # 注册服务器事件处理器
        self._register_handlers()
    
    async def initialize_services(self) -> None:
        """初始化服务"""
        try:
            self.logger.info("正在初始化服务...")
            
            # 初始化数据库服务
            self.db_service = DatabaseService(self.config)
            await self.db_service.initialize()
            
            # 初始化缓存服务
            self.cache_service = CacheService(self.config)
            await self.cache_service.initialize()
            
            # 初始化工具处理器
            self.tool_handlers = {
                "list_datasets": ListDatasetsHandler(self.db_service, self.cache_service),
                "query_dataset": QueryDatasetHandler(self.db_service, self.cache_service),
                "get_dataset_info": GetDatasetInfoHandler(self.db_service, self.cache_service),
                "filter_samples": FilterSamplesHandler(self.db_service, self.cache_service),
            }
            
            self.logger.info("服务初始化完成")
            
        except Exception as e:
            self.logger.error(f"服务初始化失败: {e}")
            raise
    
    def _register_handlers(self) -> None:
        """注册事件处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """列出可用的工具"""
            return [
                Tool(
                    name="list_datasets",
                    description="列出可用的数据集，支持分类和搜索过滤",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "数据集分类过滤（如：vision, nlp, audio）"
                            },
                            "search": {
                                "type": "string",
                                "description": "搜索关键词"
                            },
                            "source": {
                                "type": "string",
                                "enum": ["modelscope", "huggingface", "all"],
                                "description": "数据集来源",
                                "default": "all"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回结果数量限制",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 200
                            }
                        }
                    }
                ),
                Tool(
                    name="query_dataset",
                    description="执行自然语言查询，返回符合条件的数据样本",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "自然语言查询，如：'获取COCO数据集中前50张包含person标注的图片'"
                            },
                            "max_samples": {
                                "type": "integer",
                                "description": "最大返回样本数",
                                "default": 100,
                                "minimum": 1,
                                "maximum": 1000
                            },
                            "format": {
                                "type": "string",
                                "enum": ["json", "arrow", "pandas"],
                                "description": "输出格式",
                                "default": "json"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_dataset_info",
                    description="获取指定数据集的详细信息和结构",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dataset_name": {
                                "type": "string",
                                "description": "数据集名称"
                            },
                            "include_schema": {
                                "type": "boolean",
                                "description": "是否包含数据结构信息",
                                "default": True
                            },
                            "include_samples": {
                                "type": "boolean",
                                "description": "是否包含样本预览",
                                "default": False
                            }
                        },
                        "required": ["dataset_name"]
                    }
                ),
                Tool(
                    name="filter_samples",
                    description="基于SQL/Arrow条件过滤数据样本",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dataset_name": {
                                "type": "string",
                                "description": "数据集名称"
                            },
                            "filter_condition": {
                                "type": "string",
                                "description": "过滤条件，如：'category_name == \"person\"'"
                            },
                            "subset": {
                                "type": "string",
                                "description": "数据集子集名称",
                                "default": "train"
                            },
                            "max_samples": {
                                "type": "integer",
                                "description": "最大返回样本数",
                                "default": 100,
                                "minimum": 1,
                                "maximum": 1000
                            },
                            "format": {
                                "type": "string",
                                "enum": ["json", "arrow", "pandas"],
                                "description": "输出格式",
                                "default": "json"
                            }
                        },
                        "required": ["dataset_name", "filter_condition"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            """处理工具调用"""
            try:
                self.logger.info(f"调用工具: {name}, 参数: {arguments}")
                
                if name not in self.tool_handlers:
                    raise ValueError(f"未知的工具: {name}")
                
                handler = self.tool_handlers[name]
                result = await handler.handle(arguments)
                
                return [TextContent(type="text", text=str(result))]
                
            except Exception as e:
                self.logger.error(f"工具调用失败 {name}: {e}")
                error_msg = f"工具调用失败: {str(e)}"
                return [TextContent(type="text", text=error_msg)]
    
    async def run(self) -> None:
        """运行服务器"""
        try:
            self.logger.info(f"启动 {self.config.mcp_server_name} v{self.config.mcp_server_version}")
            
            # 初始化服务
            await self.initialize_services()
            
            # 运行服务器
            try:
                async with stdio_server() as (read_stream, write_stream):
                    await self.server.run(
                        read_stream,
                        write_stream,
                        InitializationOptions(
                            server_name=self.config.mcp_server_name,
                            server_version=self.config.mcp_server_version,
                            capabilities=ServerCapabilities(
                                tools=ToolsCapability(listChanged=True),
                                experimental={}
                            )
                        )
                    )
            except asyncio.CancelledError:
                self.logger.info("服务器接收到取消信号")
                raise
            except Exception as e:
                self.logger.error(f"stdio_server运行失败: {e}")
                raise
                
        except Exception as e:
            self.logger.error(f"服务器运行失败: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            self.logger.info("正在清理资源...")
            
            if self.cache_service:
                await self.cache_service.close()
            
            if self.db_service:
                await self.db_service.close()
                
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")


async def main():
    """主函数"""
    server = None
    try:
        # 加载配置
        config = Config.from_env_file()
        
        # 设置日志
        setup_logging(config)
        
        # 创建并运行服务器
        server = ModelScopeMCPServer(config)
        await server.run()
        
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except asyncio.CancelledError:
        print("\n服务器被取消")
    except Exception as e:
        print(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if server:
            try:
                await server.cleanup()
            except Exception as e:
                print(f"清理资源时出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())