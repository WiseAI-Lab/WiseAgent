# Wise-Agent: A Easy-going Agent Framework

![image](https://github.com/Dongbox/wgent/blob/main/logo.png)

### Features

...

## Quick Start

`example_agent_config.json`实现了一个简单的Agent，当不声明`config_path`地址的时候将默认加载此文件

### 1. Behaviour Config

| 我们可以在config文件中定义一个已有behaviour的基本信息

Example:
`Transport Behaviour`

```json
"PahoMQTTMessageTransportBehaviour": {
"name": "PahoMQTTMessageTransportBehaviour_v1",
"configuration": {
"pool_size": 5,
"process_pool": false,
"table": "MessageQueueTransportTable"
},
"description": "Version of Behaviour",
"status": 1,
"url": "local",
"store_type": "git",
"category": "transport.mqtb.mqtt",
"import_path": "transport.mqtb.mqtt.mqtt_paho",
}
```

- name：行为的名字(Repo:Topic)
- configuration：配置信息
- status：是否启用
- url && store_type：根据保存方法对url进行请求并保存到本地
- import_path: 动态导入的地址，此处一定要定义清楚

### 2. Agent Config

...