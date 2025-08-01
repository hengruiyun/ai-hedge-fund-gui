# AI对冲基金分析软件 - GUI扩展

本项目为 virattt 最初开发的AI对冲基金分析软件提供了一个图形用户界面（GUI）。它旨在简化与强大的底层AI驱动金融分析工具的交互。

## 注意
*   **不支持A股**：一此软件为国外作者制作，不支持A股/港股，如需A股，请改用[AI基金大师(https://github.com/hengruiyun/AI-Fund-Master)]。
  
## 功能特性

*   **图形用户界面**：一个直观的界面，用于管理和运行金融分析。
*   **简化工作流程**：轻松配置股票代码、日期范围、API密钥和AI模型。
*   **多AI服务商支持**：兼容多种AI模型服务提供商。

<img width="1258" height="974" alt="aifc" src="https://github.com/user-attachments/assets/c191b591-8455-4e3e-ba8f-4eaeb4ff1702" />


## 安装与使用

要使用此GUI扩展，请按照以下步骤操作：

  **运行GUI**：
    ```
    gui
    ```



## 配置说明

API密钥和其他设置通过 ai-hedge-fund-gui 目录下的 .env 文件以及GUI本身进行管理。

*   **分析师选择**：在"分析师"选项卡中选择参与分析的AI分析师。
*   **API密钥**：在GUI的"API密钥"选项卡中输入您的API密钥，或通过编辑 .env 文件输入。通常至少需要一个AI提供商的密钥。
*   **模型选择**：在"模型配置"选项卡中选择您偏好的AI模型提供商和模型名称。



## 许可证

此GUI扩展根据 Apache License 2.0 获得许可。更多详情请参阅 LICENSE 文件


## 致谢

*   本项目是 virattt 的 ai-hedge-fund 项目的扩展。我们感谢他们的工作并将其开源。您可以在以下地址找到原始项目：[https://github.com/virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund)。
*   我们使用了 uv，一个由 Astral 开发的用 Rust 编写的极速 Python 包安装器和解析器。更多信息请访问：[https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)。


## 联系方式

Email: 267278466@qq.com


## 免责声明

本软件仅用于教育和研究目的，不构成真实的交易或投资建议。本软件的创建者和贡献者不对因使用本软件而产生的任何财务损失负责。在做出投资决策前，请务必咨询合格的财务顾问。 
