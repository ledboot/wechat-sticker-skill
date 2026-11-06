# 微信原创动态表情 Skill

这是可复用的 **Agent Skill 工作流 + 本地处理脚本**，不是无需生成模型即可凭文字输出 GIF 的离线绘图引擎。AI 执行器需提供图像生成功能，才能从角色描述绘制 9 帧动作；本项目负责角色一致性规范、选题规划、独立 GIF 合成、资源验证和打包。

## 安装
把整个 `wechat_sticker_skill` 目录放到支持 Agent Skills 的客户端的 skills 目录中（例如 `.agents/skills/wechat-sticker-pack/` 或对应产品自定义技能目录），保持 `SKILL.md` 位于目录根部；安装 Python 3 与 Pillow：

```bash
python -m pip install Pillow
```

## 最简工作流
1. 用户：`制作16张微信动态表情，角色是一只戴紫色三角巾的奶黄小鸡，动作夸张。`
2. Agent 读取 `SKILL.md`，补全并保存角色设定及 16 个均衡场景，建立 reference image。
3. Agent 调用可用图像生成工具，为每个场景绘制单独的连贯 9 帧（最终至少 16 × 9 张源帧），写入 `frames/01/001.png` 等。**这一步需要图像生成工具，不能用下面的脚本自动凭空画出。**
4. `python scripts/build_gif.py --frames frames/01 --out output/stickers/01.gif --thumb output/thumbs/01.png --max-kb 100`
5. 为全部条目循环执行第 4 步；再生成 `banner_750x400.jpg`、`cover_240x240.png`、`icon_50x50.png`、`tip_guide_750x560.png`、`tip_thanks_750x750.png`。
6. 辅助素材统一采用 `名称_宽x高.扩展名` 命名，图片实际像素必须匹配文件名。
7. `python scripts/validate_pack.py --root output --selection selection.json --report output/validation.json`
8. 验证通过后压缩整个 output 目录为 ZIP，给独立 GIF 下载入口和 ZIP。

## 主题选择示例
```bash
python scripts/select_topics.py --count 16 --seed 42 --out selection.json
python scripts/select_topics.py --count 24 --include 收到 爱你 好困 --exclude 摸鱼中 --out selection.json
```

## 规格风险
所附规范是**用户目标 / 保守制作目标**，不是平台实时法律或技术承诺。2026 年公开资料对 GIF 限制存在 100KB、500KB 等不同表述；投稿前请打开 https://sticker.weixin.qq.com/ 核对后台最新规则。无上架账户授权时，本 Skill 不会提交审核。默认启用保守规格并要求透明背景，最终仍需逐张视觉复核。


MIT License