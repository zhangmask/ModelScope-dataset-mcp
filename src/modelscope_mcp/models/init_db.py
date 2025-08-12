"""数据库初始化脚本

创建数据库表和初始数据。
"""

import os
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.modelscope_mcp.models.base import Base
from src.modelscope_mcp.models.dataset import Dataset, DatasetSubset
from src.modelscope_mcp.models.query import QueryHistory, QueryResult
from src.modelscope_mcp.models.cache import CacheEntry
from src.modelscope_mcp.core.config import Config
from src.modelscope_mcp.core.logger import get_logger

logger = get_logger(__name__)


def create_database(database_url: Optional[str] = None) -> None:
    """创建数据库和表
    
    Args:
        database_url: 数据库连接URL，如果为None则使用配置文件中的URL
    """
    if database_url is None:
        config = Config()
        database_url = config.database_url
    
    logger.info(f"正在创建数据库: {database_url}")
    
    # 创建引擎
    engine = create_engine(database_url, echo=True)
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    logger.info("数据库表创建完成")
    
    return engine


def init_sample_data(engine) -> None:
    """初始化示例数据
    
    Args:
        engine: 数据库引擎
    """
    logger.info("正在初始化示例数据")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查是否已有数据
        existing_datasets = session.query(Dataset).count()
        if existing_datasets > 0:
            logger.info("数据库中已存在数据，跳过初始化")
            return
        
        # 创建示例数据集
        sample_datasets = [
            Dataset(
                name="coco2017",
                display_name="COCO 2017",
                description="COCO 2017目标检测数据集",
                source="modelscope",
                source_id="modelscope/coco_2017_dataset",
                category="vision",
                tags=["object-detection", "computer-vision", "coco"],
                total_samples=118287,
                schema_info={
                    "features": {
                        "image": {"type": "Image"},
                        "objects": {
                            "type": "Sequence",
                            "feature": {
                                "bbox": {"type": "Sequence", "length": 4},
                                "category_id": {"type": "Value", "dtype": "int64"},
                                "category_name": {"type": "Value", "dtype": "string"}
                            }
                        }
                    }
                }
            ),
            Dataset(
                name="imagenet-1k",
                display_name="ImageNet-1K",
                description="ImageNet 1K图像分类数据集",
                source="huggingface",
                source_id="imagenet-1k",
                category="vision",
                tags=["image-classification", "computer-vision", "imagenet"],
                total_samples=1281167,
                schema_info={
                    "features": {
                        "image": {"type": "Image"},
                        "label": {"type": "Value", "dtype": "int64"}
                    }
                }
            ),
            Dataset(
                name="squad",
                display_name="SQuAD",
                description="Stanford Question Answering Dataset",
                source="huggingface",
                source_id="squad",
                category="nlp",
                tags=["question-answering", "nlp", "reading-comprehension"],
                total_samples=87599,
                schema_info={
                    "features": {
                        "id": {"type": "Value", "dtype": "string"},
                        "title": {"type": "Value", "dtype": "string"},
                        "context": {"type": "Value", "dtype": "string"},
                        "question": {"type": "Value", "dtype": "string"},
                        "answers": {
                            "type": "Sequence",
                            "feature": {
                                "text": {"type": "Value", "dtype": "string"},
                                "answer_start": {"type": "Value", "dtype": "int32"}
                            }
                        }
                    }
                }
            )
        ]
        
        # 添加数据集
        for dataset in sample_datasets:
            session.add(dataset)
        
        session.commit()
        
        # 为COCO数据集添加子集
        coco_dataset = session.query(Dataset).filter_by(name="coco2017").first()
        if coco_dataset:
            coco_subsets = [
                DatasetSubset(
                    dataset_id=coco_dataset.id,
                    name="train",
                    split="train",
                    sample_count=118287
                ),
                DatasetSubset(
                    dataset_id=coco_dataset.id,
                    name="validation",
                    split="validation",
                    sample_count=5000
                )
            ]
            
            for subset in coco_subsets:
                session.add(subset)
        
        session.commit()
        logger.info("示例数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化示例数据失败: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """主函数"""
    try:
        # 创建数据目录
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        
        # 创建数据库
        engine = create_database()
        
        # 初始化示例数据
        init_sample_data(engine)
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()