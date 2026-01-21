# Titanic - Machine Learning from Disaster

## 任务描述

预测哪些乘客在泰坦尼克号沉船事故中幸存下来。

## 数据说明

### 训练集 (train.csv)
- **PassengerId**: 乘客 ID
- **Survived**: 是否幸存 (0 = 否, 1 = 是)
- **Pclass**: 船票等级 (1 = 1等舱, 2 = 2等舱, 3 = 3等舱)
- **Name**: 姓名
- **Sex**: 性别
- **Age**: 年龄
- **SibSp**: 船上兄弟姐妹/配偶数量
- **Parch**: 船上父母/子女数量
- **Ticket**: 船票编号
- **Fare**: 票价
- **Cabin**: 船舱号
- **Embarked**: 登船港口 (C = Cherbourg, Q = Queenstown, S = Southampton)

### 测试集 (test.csv)
包含相同特征，但不包含 `Survived` 列，需要预测。

## 评估指标

**准确率 (Accuracy)**: 预测正确的乘客比例

## 提交格式

提交文件应包含两列：
- **PassengerId**: 乘客 ID
- **Survived**: 预测的幸存状态 (0 或 1)

示例：
```csv
PassengerId,Survived
892,0
893,1
894,0
...
```

## I/O 指令

训练一个模型来预测乘客是否幸存：
1. 加载训练数据 (train.csv)
2. 进行特征工程和数据清洗
3. 训练分类模型
4. 在测试集 (test.csv) 上进行预测
5. 生成符合要求的提交文件

## 注意事项

- 数据存在缺失值，特别是 Age 和 Cabin 列
- 需要进行特征编码（如 Sex, Embarked）
- 可以使用 Pclass, Sex, Age, Fare 等特征
- 建议尝试多种模型（逻辑回归、随机森林、XGBoost 等）
