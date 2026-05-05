# 解魔方机器人 — 树莓派端

## 文件说明

| 文件 | 功能 |
|---|---|
| `main.py` | 主程序, 完整流程入口 |
| `config.py` | 硬件配置 (相机/串口/颜色阈值) |
| `camera.py` | 4相机采集管理 |
| `color_detect.py` | 魔方面检测 + 颜色识别 |
| `cube_model.py` | 魔方状态建模 + kociemba→机器人动作转换 |
| `solver.py` | kociemba 求解器封装 |
| `serial_protocol.py` | 与STM32的100字节串口协议 |
| `calibrate_colors.py` | 颜色校准工具 |
| `requirements.txt` | Python依赖 |

## 树莓派上首次使用

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 测试相机
python main.py --test-camera

# 3. 颜色校准 (重要!)
python calibrate_colors.py
# 将输出的HSV范围复制到 config.py 的 COLOR_RANGES_HSV

# 4. 测试串口 (STM32需已上电)
python main.py --test-serial

# 5. 完整运行
python main.py
```

## 命令行选项

```
python main.py                    # 完整自动流程
python main.py --calibrate        # 颜色校准
python main.py --test-camera      # 测试相机
python main.py --test-serial      # 测试串口
python main.py --no-robot         # 仅视觉 (不连机器人)
python main.py --solve "UUU..."   # 直接求解
```
