#!/bin/bash

# 监控系统部署脚本

# 安装依赖
pip install -r requirements.txt

# 配置Prometheus
if ! command -v prometheus &> /dev/null; then
    echo "安装Prometheus..."
    wget https://github.com/prometheus/prometheus/releases/download/v2.50.1/prometheus-2.50.1.linux-amd64.tar.gz
    tar xvfz prometheus-*.tar.gz
    cd prometheus-* || exit
    ./prometheus --version
    cp prometheus.yml ../config/
    cd ..
fi

# 配置Grafana (可选)
if [ "$1" == "--grafana" ]; then
    echo "安装Grafana..."
    sudo apt-get install -y adduser libfontconfig1
    wget https://dl.grafana.com/oss/release/grafana_10.4.1_amd64.deb
    sudo dpkg -i grafana_*.deb
fi

# 启动服务
echo "启动监控系统..."
python src/main.py &

echo "启动Prometheus..."
./prometheus-*/prometheus --config.file=config/prometheus.yml &

if [ "$1" == "--grafana" ]; then
    echo "启动Grafana..."
    sudo systemctl start grafana-server
fi

echo "部署完成!"