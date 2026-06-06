"""彩蛋地图数据采集 - 数据模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SourcePlatform(str, Enum):
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    WEIBO = "weibo"
    USER_SUBMIT = "user_submit"


class EggCategory(str, Enum):
    BOOK = "书籍"
    MAGAZINE = "杂志"
    LETTER = "手写信"
    BLIND_BOX = "盲盒"
    OTHER = "其他"


class ScrapedEgg(BaseModel):
    """采集到的彩蛋数据结构"""
    title: str = Field(description="标题")
    description: str = Field(description="描述内容")
    category: EggCategory = Field(default=EggCategory.OTHER, description="分类")
    images: list[str] = Field(default_factory=list, description="图片URL列表")
    location_name: Optional[str] = Field(None, description="地点名称")
    city: Optional[str] = Field(None, description="城市")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")
    source_url: str = Field(description="原始来源链接")
    source_platform: SourcePlatform = Field(description="来源平台")
    source_author: Optional[str] = Field(None, description="原作者昵称")
    placed_at: Optional[datetime] = Field(None, description="发布/放置时间")
    scraped_at: datetime = Field(default_factory=datetime.now, description="采集时间")

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
