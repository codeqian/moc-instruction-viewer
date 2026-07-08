# 部署指南

## 前置条件

- 阿里云 ECS（Ubuntu 22.04 推荐）
- 域名已完成 ICP 备案
- 域名 DNS 解析到 ECS 公网 IP
- 本地已上传 LDraw 零件库和模型文件

## 首次部署

1. SSH 登录 ECS：
   ```bash
   ssh root@<ECS公网IP>
   ```

2. 执行一键部署脚本：
   ```bash
   cd /opt/moc-viewer
   bash deploy/setup.sh
   ```

   或者直接从 GitHub 拉取：
   ```bash
   git clone https://github.com/codeqian/moc-instruction-viewer.git /opt/moc-viewer
   cd /opt/moc-viewer
   bash deploy/setup.sh
   ```

3. 上传 LDraw 零件库：
   ```bash
   # 从本地上传（如果零件库在本地）
   scp -r ldraw-lib/* root@<ECS_IP>:/data/moc-viewer/ldraw-lib/
   ```

4. 上传模型文件：
   ```bash
   scp *.ldr *.mpd root@<ECS_IP>:/data/moc-viewer/source/
   ```

5. 修改 Nginx 域名配置：
   ```bash
   vim /etc/nginx/sites-available/moc-viewer
   # 将 server_name _; 改为 server_name 你的域名;
   nginx -t && systemctl reload nginx
   ```

## 更新部署

代码有修改后：

```bash
cd /opt/moc-viewer
bash deploy/update.sh
```

## 查看状态

```bash
# 后端服务状态
systemctl status moc-viewer

# 查看后端日志
journalctl -u moc-viewer -f

# 查看 Nginx 日志
tail -f /var/log/nginx/moc-viewer-access.log
tail -f /var/log/nginx/moc-viewer-error.log
```
