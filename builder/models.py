import uuid

from django.db import models

# Create your models here.

class Component(models.Model):
    class Category(models.TextChoices):
        PROCESSOR = "processor", "Процессор"
        MOTHERBOARD = "motherboard", "Материнская плата"
        GPU = "gpu", "Видеокарта"
        MEMORY = "memory", "Оперативная память"
        STORAGE = "storage", "Накопитель"
        POWER_SUPPLY = "power_supply", "Блок питания"
        CASE = "case", "Корпус"
        COOLER = "cooler", "Охлаждение"

    category = models.CharField("Категория", max_length=20, choices=Category.choices)
    name = models.CharField("Название", max_length=160)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    specifications = models.JSONField(
        "Характеристики",
        default=dict,
        blank=True,
        help_text='Для проверки совместимости: сокет — {"socket": "AM5"}; тип памяти — {"memory_type": "DDR5"}.',
    )
    in_stock = models.BooleanField("В наличии", default=True)
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "Комплектующая"
        verbose_name_plural = "Комплектующие"

    def __str__(self):
        return self.name


class Build(models.Model):
    name = models.CharField("Название сборки", max_length=100)
    share_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    components = models.ManyToManyField(Component)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.name