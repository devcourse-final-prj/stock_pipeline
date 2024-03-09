from django.db import models


class DailyStockPrice(models.Model):
    sector_name = models.CharField(max_length=100, verbose_name="부문")
    stock_code = models.CharField(max_length=10, verbose_name="주식 코드")
    kr_stock_name = models.CharField(max_length=100, verbose_name="회사 이름")
    date_column = models.DateField(verbose_name="날짜")
    closing_price = models.IntegerField(verbose_name="종가")

    def __str__(self):
        return f"[{self.sector_name}] {self.kr_stock_name}({self.stock_code}) - {self.date_column}: {self.closing_price}"

    class Meta:
        verbose_name = "주식 일간 종가"
        verbose_name_plural = "주식 일간 종가들"