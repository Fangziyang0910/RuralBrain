# 混合测试图片集

此文件夹用于测试大模型在**没有路径提示信息**的情况下智能识别图片类型的能力。

## 图片映射表

| 文件名 | 实际类型 | 来源 |
|--------|---------|------|
| 1.jpg | 害虫 | pests/1.jpg |
| 2.jpg | 害虫 | pests/2.jpg |
| 3.jpg | 大米 | rice/1.jpg |
| 4.jpg | 大米 | rice/2.jpg |
| 5.jpg | 牛只 | cows/1.jpg |
| 6.jpg | 牛只 | cows/2.jpg |

## 使用说明

当测试时使用如 `tests/resources/mixed/1.jpg` 这样的路径,大模型无法从路径中获取任何类型提示信息,必须依靠其他机制来判断图片类型。

## 复制命令(备用)

```powershell
Copy-Item "tests\resources\pests\1.jpg" "tests\resources\mixed\1.jpg"
Copy-Item "tests\resources\pests\2.jpg" "tests\resources\mixed\2.jpg"
Copy-Item "tests\resources\rice\1.jpg" "tests\resources\mixed\3.jpg"
Copy-Item "tests\resources\rice\2.jpg" "tests\resources\mixed\4.jpg"
Copy-Item "tests\resources\cows\1.jpg" "tests\resources\mixed\5.jpg"
Copy-Item "tests\resources\cows\2.jpg" "tests\resources\mixed\6.jpg"
```
