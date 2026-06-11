# 安裝程序

這個專案提供一支 Bash 指令 `extract-audio`。你可以直接在專案目錄內執行，也可以安裝成全域指令。

## 1. 安裝系統依賴

在 Ubuntu / WSL：

```bash
sudo apt update
sudo apt install -y ffmpeg
```

確認：

```bash
ffmpeg -version
ffprobe -version
```

## 2. 取得專案

如果你是本機建立：

```bash
cd ~/extract-audio
```

如果之後放到 Git 遠端，可用：

```bash
git clone <your-repo-url>
cd extract-audio
```

## 3. 直接執行

先給執行權限：

```bash
chmod +x ./bin/extract-audio
```

直接使用：

```bash
./bin/extract-audio
./bin/extract-audio "/mnt/d/Videos/Meeting"
./bin/extract-audio --force
```

## 4. 安裝成全域指令

建立個人 `bin` 目錄並複製腳本：

```bash
mkdir -p ~/bin
cp ./bin/extract-audio ~/bin/extract-audio
chmod +x ~/bin/extract-audio
```

把 `~/bin` 加入 PATH：

```bash
grep -qxF 'export PATH="$HOME/bin:$PATH"' ~/.bashrc || \
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
```

重新載入 shell：

```bash
source ~/.bashrc
```

確認安裝：

```bash
which extract-audio
extract-audio --help
```

## 5. 更新安裝

若腳本有新版本：

```bash
cd ~/extract-audio
cp ./bin/extract-audio ~/bin/extract-audio
chmod +x ~/bin/extract-audio
```

## 6. 移除

如果只移除全域指令：

```bash
rm -f ~/bin/extract-audio
```

如果也要刪掉專案目錄：

```bash
cd ~
rm -rf ~/extract-audio
```
