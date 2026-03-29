部署说明 - hxz-fortune-telling (systemd + Nginx)

简介
- 本目录包含可复用的部署模板：`hxz-fortune.service`（systemd）、`nginx-hxz-fortune.conf`（Nginx）和 `setup.sh`（自动化安装脚本）。

快速上手（服务器上执行）
1. 将整个项目复制到服务器的 `/opt/hxz-fortune-telling`：

```bash
# 在服务器上（示例）
sudo mkdir -p /opt
sudo rsync -a --exclude '.git' /local/path/hxz-fortune-telling /opt/hxz-fortune-telling
```

2. 编辑 `deploy/setup.sh` 顶部的 `DOMAIN` 变量，替换为你的域名或在运行前以环境变量方式修改。
3. 以 `root` 或 `sudo` 运行安装脚本：

```bash
sudo bash /opt/hxz-fortune-telling/deploy/setup.sh
```

部署完成后，systemd 单元名为 `hxz-fortune-telling.service`，可用以下命令查看与管理服务：

```bash
sudo systemctl status hxz-fortune-telling --no-pager
sudo journalctl -u hxz-fortune-telling -f
sudo systemctl restart hxz-fortune-telling
```

4. 完成后访问 `https://<your-domain>`。

手动步骤（替代）
- 如果你想手动控制每一步，请参照 `deploy/setup.sh` 中的命令：创建 venv、安装依赖、复制 nginx 配置、申请证书、安装 systemd 服务并启动。

注意
- `setup.sh` 为示例脚本，假定运行环境为 Debian/Ubuntu 系列。根据目标服务器（CentOS、Alma、Arch）适当调整包管理命令与路径。
- 若想改用容器化（Docker Compose + Traefik），可先使用本方案上线，再迁移到容器化（我可以帮你生成迁移模板）。
