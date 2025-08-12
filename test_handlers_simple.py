#!/usr/bin/env python3
"""简化的Handler测试

测试实际的Handler接口和功能。
"""

import asyncio
from unittest.mock import Mock, AsyncMock


async def test_handlers():
    """测试所有Handler的基本功能"""
    print("开始Handler功能测试...")
    
    # 创建Mock服务
    mock_db_service = Mock()
    mock_cache_service = Mock()
    
    # Mock数据库服务方法
    mock_db_service.get_datasets = AsyncMock(return_value=[])
    mock_db_service.get_dataset_by_name = AsyncMock(return_value=None)
    
    # Mock缓存服务方法
    mock_cache_service.get = AsyncMock(return_value=None)
    mock_cache_service.set = AsyncMock(return_value=True)
    
    tests = [
        ("ListDatasetsHandler测试", test_list_datasets_handler, mock_db_service, mock_cache_service),
        ("GetDatasetInfoHandler测试", test_get_dataset_info_handler, mock_db_service, mock_cache_service),
        ("FilterSamplesHandler测试", test_filter_samples_handler, mock_db_service, mock_cache_service),
        ("QueryDatasetHandler测试", test_query_dataset_handler, mock_db_service, mock_cache_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func, db_service, cache_service in tests:
        print(f"\n运行 {test_name}...")
        try:
            await test_func(db_service, cache_service)
            print(f"✓ {test_name} 通过")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} 失败: {e}")
    
    print(f"\n测试结果: {passed}/{total} 通过")
    if passed == total:
        print("🎉 所有Handler测试通过!")
    else:
        print("❌ 部分Handler测试失败")
    
    return passed == total


async def test_list_datasets_handler(db_service, cache_service):
    """测试ListDatasetsHandler"""
    from src.modelscope_mcp.tools.list_datasets import ListDatasetsHandler
    
    handler = ListDatasetsHandler(db_service, cache_service)
    
    # 测试基本调用
    result = await handler.handle({})
    assert "success" in result
    assert "datasets" in result
    print("  ✓ 基本调用成功")
    
    # 测试带参数调用
    result = await handler.handle({
        "category": "nlp",
        "source": "modelscope",
        "limit": 10
    })
    assert "success" in result
    print("  ✓ 带参数调用成功")


async def test_get_dataset_info_handler(db_service, cache_service):
    """测试GetDatasetInfoHandler"""
    from src.modelscope_mcp.tools.get_dataset_info import GetDatasetInfoHandler
    
    handler = GetDatasetInfoHandler(db_service, cache_service)
    
    # 测试基本调用
    result = await handler.handle({"dataset_name": "test-dataset"})
    assert "success" in result
    print("  ✓ 基本调用成功")


async def test_filter_samples_handler(db_service, cache_service):
    """测试FilterSamplesHandler"""
    from src.modelscope_mcp.tools.filter_samples import FilterSamplesHandler
    
    handler = FilterSamplesHandler(db_service, cache_service)
    
    # 测试基本调用
    result = await handler.handle({
        "dataset_name": "test-dataset",
        "filters": {"label": "positive"},
        "limit": 10
    })
    assert "success" in result
    print("  ✓ 基本调用成功")


async def test_query_dataset_handler(db_service, cache_service):
    """测试QueryDatasetHandler"""
    from src.modelscope_mcp.tools.query_dataset import QueryDatasetHandler
    
    # Mock额外的数据库方法
    db_service.create_query_history = AsyncMock(return_value=Mock(id=1))
    db_service.update_query_history = AsyncMock(return_value=True)
    
    handler = QueryDatasetHandler(db_service, cache_service)
    
    # 测试基本调用
    result = await handler.handle({"query": "列出所有数据集"})
    assert "success" in result
    print("  ✓ 基本调用成功")


if __name__ == "__main__":
    asyncio.run(test_handlers())