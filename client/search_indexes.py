from haystack import indexes

from common.models import Courses


class CoursesIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Couses索引数据模型类
    """
    text = indexes.CharField(document=True, use_template=True)
    # 保存在索引库中的字段
    uuid = indexes.CharField(model_attr='uuid')
    name = indexes.CharField(model_attr='name')

    def get_model(self):
        """返回建立索引的模型类"""
        return Courses

    def index_queryset(self, using=None):
        """返回要建立索引的数据查询集"""
        return self.get_model().objects.filter(status=1)

