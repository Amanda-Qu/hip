# 髋关节三平面与肌肉运动演示

交互式中文教学演示：左侧观察全身动作、运动平面与动作要义，右侧同步观察骨盆、股骨近端和可选肌肉。

## 打开方式

下载项目后，用现代浏览器打开仓库根目录的 `index.html` 即可，无须安装依赖或联网加载模型。直接打开 `src/hip-planes.html` 也会跳转到完整页面。也可以在项目目录运行：

```sh
python -m http.server 8000
```

然后访问 `http://localhost:8000`。

## 功能

- 矢状面、额状面、水平面的方向演示。
- 髋飞机、侧蹲、弓步抗旋、弹力带臀桥。
- 小人与骨盆、股骨近端同步运动；支持暂停、拖动进度和切换视角。
- 电脑上并排比较动作与解剖结构；手机上用“动作与要义 / 骨骼与肌肉”切换，同一动作进度保持同步。
- 左侧动作下方可切换本动作的关键肌群，查看运动中的作用与伸缩提示。
- 右侧默认仅显示骨骼；肌肉选项始终可见，可勾选右髋的臀大肌、臀中肌、臀小肌、梨状肌、髂腰肌和内收短肌。
- 点击“仅看骨头”隐藏全部肌肉。查看深层肌肉时，可取消遮挡它的表层肌肉。
- 肌肉位置、伸缩趋势和动作要义；适配窄屏、深色模式与减少动态效果偏好。
- 优先使用 WebGL，无法使用时退回 Canvas 绘制。

## 项目结构与修改

```text
index.html                    可直接打开的完整页面
src/hip-planes.html            演示源码和压缩后的内嵌模型数据
src/page-template.html         独立页面的样式与状态保存外壳
scripts/build.py               生成 index.html（仅使用 Python 标准库）
bone-assets/prepare_bones.py   下载、处理骨骼参考网格
bone-assets/prepare_muscles.py 下载、处理肌肉参考网格
bone-assets/install_anatomy.py 将处理后的网格写入演示源码
requirements-models.txt        仅重新生成模型时需要的依赖
THIRD_PARTY_NOTICES.md         模型来源与署名
```

修改 `src/hip-planes.html` 后运行：

```sh
python scripts/build.py
```

源文件内的关键算法均有注释。骨骼围绕拟合的股骨头中心转动，使球与窝共享旋转中心。肌肉顶点在骨盆与股骨的旋转之间做四元数插值：例如臀中肌上部主要跟随髂骨，下端主要跟随股骨，肌腹在两者之间平滑过渡。

## 可选：重新生成模型

日常打开、修改动作或重新构建页面不需要执行以下步骤。仅修改解剖网格时需要联网下载参考 STL：

```sh
python -m pip install -r requirements-models.txt
python bone-assets/prepare_bones.py
python bone-assets/prepare_muscles.py
python bone-assets/install_anatomy.py
python scripts/build.py
```

原始 STL、临时网格、开发依赖和验证截图未纳入版本管理。完整运行数据已内嵌在源码和页面中。

## 模型说明

骨骼和肌肉参考形状来自 BodyParts3D。网格经简化和局部裁切：股骨只显示近端，髂腰肌只显示髋旁段。肌肉默认不选中，选择后显示右髋一侧，便于观察层次。

骨骼运动、肌肉形变和伸缩趋势属于教学近似，未采用个体运动捕捉或生物力学求解，不能用于测量实际肌力、肌长或临床活动范围。模型署名和参考资料见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
