# AI对冲基金分析软件 - GUI扩展

本项目为 virattt 最初开发的AI对冲基金分析软件提供了一个图形用户界面（GUI）。它旨在简化与强大的底层AI驱动金融分析工具的交互。

OSM：这是全AI 开发的软件
AI驱动的软件开发代表了技术革新的重要里程碑。通过AI完整开发OSM这样的实用工具，我们展示了人工智能在代码生成、系统设计和问题解决方面的卓越能力。这种开发模式不仅提高了效率，降低了传统开发中的人力成本和时间投入，还能确保代码质量的一致性。AI能够快速吸收最佳实践，避免常见错误，并提供创新解决方案。人工智能与软件工程融合的有力证明，揭示了未来开发范式的转变方向。

![gui_cn](https://github.com/user-attachments/assets/46d2e0a6-a29c-4464-8383-fe25a3069579)

## 功能特性

*   **图形用户界面**：一个直观的界面，用于管理和运行金融分析。
*   **简化工作流程**：轻松配置股票代码、日期范围、API密钥和AI模型。
*   **多AI服务商支持**：兼容多种AI模型服务提供商。
*   **配置管理**：保存和加载您的分析设置。


## 安装与使用

要使用此GUI扩展，请按照以下步骤操作：

1.  **克隆原始代码仓库**：
    首先，您需要从virattt的代码仓库克隆基础的 ai-hedge-fund 项目。
    ```bash
    git clone https://github.com/virattt/ai-hedge-fund.git
    ```
2.  **添加GUI文件**：
    下载最新版本的GUI扩展。将下载的文件放到您在上一步克隆的 ai-hedge-fund 目录中。
    ```bash
    git clone https://github.com/hengruiyun/ai-hedge-fund-gui.git
    copy /y ai-hedge-fund-gui\*.*  ai-hedge-fund
    copy /y ai-hedge-fund-gui\src\*.*  ai-hedge-fund\src
    cd ai-hedge-fund
    ```
3.  **设置环境和依赖项**：
    强烈建议使用虚拟环境。
    ```bash
    uv venv --python=3.10
    .venv\Scripts\activate
    uv pip install -r requirements.txt
    ```
4.  **配置API密钥**：
    该软件需要AI模型提供商（例如 OpenAI, Groq）的API密钥，可能还需要金融数据源的API密钥。
    *   将 .env.example 文件复制为 .env：
    ```bash
        copy /y  .env.example .env
    ```
    *   编辑 .env 文件并添加您的API密钥。
    *   或者，您可以在启动GUI后直接在GUI中配置API密钥。GUI将帮助创建或更新 .env 文件。

5.  **运行GUI**：
    ```bash
    gui
    或者
    uv run gui_launcher.py
    ```
![a8](https://github.com/user-attachments/assets/6ad676c8-d40f-4c11-85a3-229ab1f258be)


## 配置说明

API密钥和其他设置通过 ai-hedge-fund 目录根目录下的 .env 文件以及GUI本身进行管理。

*   **分析师选择**：在"分析师"选项卡中选择参与分析的AI分析师。
*   **API密钥**：在GUI的"API密钥"选项卡中输入您的API密钥，或通过编辑 .env 文件输入。通常至少需要一个AI提供商的密钥。
*   **模型选择**：在"模型配置"选项卡中选择您偏好的AI模型提供商和模型名称。
*   **分析参数**：在"参数"选项卡中设置股票代码、日期范围、初始现金等。

在GUI中配置的设置（包括API密钥）将保存到 hedge_fund_config.json 文件中，相关的API密钥也会写入 .env 文件。


## 故障排除

*   **缺少依赖项**：确保 requirements.txt 中的所有依赖项已在您激活的Python环境中正确安装。运行 python dependency_checker.py 进行快速检查。
*   **API密钥错误**：仔细检查您的API密钥是否正确输入、是否有效，并确保有足够的配额。
*   **GUI启动失败**：
    *   确认已安装并可访问 Python（推荐 Python 3.10+）。
    *   确保 tkinter（通常是 Python标准安装的一部分）可用。
    *   尝试重新安装依赖项：pip install -r requirements.txt --force-reinstall。


## 许可证

此GUI扩展根据 Apache License 2.0 获得许可。更多详情请参阅 LICENSE 文件


## 致谢

*   本项目是 virattt 的 ai-hedge-fund 项目的扩展。我们感谢他们最初的工作并将其开源。您可以在以下地址找到原始项目：[https://github.com/virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund)。
*   我们使用了 uv，一个由 Astral 开发的用 Rust 编写的极速 Python 包安装器和解析器。更多信息请访问：[https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)。


## 联系方式

Gmail: hengruiyun


## 免责声明

本软件仅用于教育和研究目的，不构成真实的交易或投资建议。本软件的创建者和贡献者不对因使用本软件而产生的任何财务损失负责。在做出投资决策前，请务必咨询合格的财务顾问。 
