#HDrive Host

HDrive开源电机驱动器的简易上位机，支持实时控制、状态监控和历史数据图表。

## 功能特性

- **串口通信**: 支持 921600/460800/115200 波特率
- **电机控制**:
  - 电机使能/关闭
  - MIT 控制模式（位置+速度+Kp+Kd+力矩前馈）
  - PID 位置控制
  - PID 速度控制
  - PID 电流控制
- **实时状态**: 位置、速度、电流、温度、电压
- **历史图表**: 电流、温度、电压曲线，支持暂停/清空
- **扩展协议**: 新增 GET_STATE 查询命令

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

### 连接电机

1. 选择正确的串口号（如 COM3）
2. 选择波特率（默认 921600）
3. 设置电机地址（默认 1）
4. 点击"连接"按钮

## 协议说明

### 基础帧格式

TEST3 使用简化串口协议：

```
[0xAA] [Len] [Addr] [Cmd] [Data...] [CRC] [0x55]
  1B      1B    1B     1B    N字节    1B     1B
```

- **帧头**: `0xAA`
- **长度**: 整帧字节数
- **地址**: 电机地址（1-255）
- **命令**: 见下表
- **数据**: 命令参数（可选）
- **CRC**: 8位累加和（除 CRC 和帧尾）
- **帧尾**: `0x55`

### 命令列表

| 命令 | 代码 | 数据长度 | 说明 |
|------|------|----------|------|
| MOTOR_OFF | 0x00 | 0 | 电机关闭 |
| MOTOR_ON | 0x01 | 0 | 电机使能 |
| MIT_CONTROL | 0x0A | 20B | MIT控制模式 |
| PID_POSITION | 0x0B | 4B | PID位置控制 |
| PID_SPEED | 0x0C | 4B | PID速度控制 |
| PID_CURRENT | 0x0D | 4B | PID电流控制 |
| **GET_STATE** | **0x14** | **0** | **查询状态（新增）** |

### GET_STATE 命令详解（新增）

原固件协议没有查询命令，只能被动接收控制命令的回复。此上位机配合固件扩展，增加了主动查询功能。

#### 查询帧（上位机→下位机）

```
AA 06 01 14 C5 55
│  │  │  │  │  │
│  │  │  │  │  └── 帧尾 0x55
│  │  │  │  └───── CRC校验: 0xAA+0x06+0x01+0x14 = 0xC5
│  │  │  └──────── 命令: GET_STATE (20 = 0x14)
│  │  └─────────── 电机地址: 1
│  └────────────── 帧长度: 6
└───────────────── 帧头: 0xAA
```

#### 回复帧（下位机→上位机）

```
AA 16 01 14 [position:4B] [speed:4B] [iq:4B] [temp:4B] [CRC] 55
│  │  │  │  └────────────────────────────────────────────────────
│  │  │  │     position: float, 电机位置 (rad)
│  │  │  │     speed:    float, 速度 (rad/s)
│  │  │  │     iq:       float, 电流 (A)
│  │  │  │     temp:     float, 温度 (°C)
│  │  │  └────────────────── 命令: 0x14
│  │  └───────────────────── 地址: 1
│  └──────────────────────── 帧长度: 22 (0x16)
└─────────────────────────── 帧头: 0xAA
```

#### 固件修改方法

在 `command.h` 中新增命令：

```c
enum COMMAND{
    MOTOR_OFF=0,
    MOTOR_ON = 1,
    MIT_CONTROL=10,
    PID_POSITION_CONTROL=11,
    PID_SPEED_CONTROL=12,
    PID_CURRENT_CONTROL=13,
    GET_STATE=20           // 新增查询状态命令
};
```

在 `command.c` 的 `commandParsing()` 函数中添加处理：

```c
// AA 06 01 14 [CRC] 55 - 查询状态命令
case GET_STATE:
    if(motor1.uart3Data.rx_buffer[1]==6)
    {
        float temp[4];
        temp[0] = motor1.position;   // 位置（弧度）
        temp[1] = motor1.speed;      // 速度（rad/s）
        temp[2] = motor1.iq;         // 电流（A）
        temp[3] = motor1.ntc;        // 温度（摄氏度）

        motor1.uart3Data.tx_buffer[0]=0XAA;
        motor1.uart3Data.tx_buffer[1]=0x16;  // 22字节总长度
        motor1.uart3Data.tx_buffer[2]=motor1.motorID;
        motor1.uart3Data.tx_buffer[3]=GET_STATE;
        memcpy(&motor1.uart3Data.tx_buffer[4], (uint8_t *)&temp, sizeof(float) * 4);
        motor1.uart3Data.tx_buffer[20]=checksum_8bit_simple(motor1.uart3Data.tx_buffer,20);
        motor1.uart3Data.tx_buffer[21]= 0x55;
        HAL_GPIO_WritePin(RE_GPIO_Port,RE_Pin,GPIO_PIN_SET);
        DE_DELAY();
        HAL_UART_Transmit_DMA(&huart3,motor1.uart3Data.tx_buffer,22);
    }
    break;
```

## 界面说明

### 左侧面板

- **串口连接**: 选择串口、波特率、电机地址
- **实时状态**: 位置、速度、电流、温度、电压
- **连接状态**: 显示当前连接情况
- **统计信息**: 接收帧数、丢帧数

### 中间控制面板

- **电机电源**: ON/OFF 按钮
- **MIT控制**: 设置位置、速度、Kp、Kd、前馈力矩
- **位置控制**: PID位置模式目标值
- **速度控制**: PID速度模式目标值
- **电流控制**: PID电流模式目标值

### 右侧图表

- **电流曲线** (橙色): 实时电流变化
- **温度曲线** (红色): 电机温度变化 (暂时不可用)
- **电压曲线** (紫色): 总线电压变化
- 支持显示/隐藏各曲线
- 支持暂停采集和清空数据

## 项目结构

```
Hdrive_Host/
├── main.py                 # 程序入口
├── README.md               # 本文件
├── requirements.txt        # Python依赖
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── protocol.py         # 协议编解码
│   └── serial_worker.py    # 串口通信线程
└── ui/                     # 用户界面
    ├── __init__.py
    ├── main_window.py      # 主窗口
    └── widgets/
        ├── __init__.py
        ├── control_panel.py    # 控制面板
        ├── status_panel.py     # 状态面板
        └── chart_panel.py      # 图表面板
```

## 与 TEST (MT Protocol v3.2) 的区别

| 特性 | TEST3 (本上位机) | TEST (MT v3.2) |
|------|-----------------|----------------|
| 地址长度 | 1字节 | 2字节 |
| 校验方式 | 8bit累加和 | CRC16 |
| 帧尾 | 0x55 | 无 |
| 时间戳 | 无 | 有 |
| 状态上报 | 查询-响应 | 主动周期性 |
| 协议复杂度 | 简单 | 完整 |


## 作者

蟠桃  

WeChat : endpang 
Email  : endler@qq.com

## 许可证

MIT License - 开源自由使用
