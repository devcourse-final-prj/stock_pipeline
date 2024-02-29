from django.db import models

# Create your models here.


class chart(models.Model):
    title = models.CharField('차트 이름', max_length=30)
    link = models.CharField('연결 링크', max_length=1000)
    date = models.DateTimeField('업데이트 시간', auto_now=True)
