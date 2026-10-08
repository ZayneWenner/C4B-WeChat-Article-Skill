# AI 使用日志 + AAR 复盘（C4B）

> 本文件是挑战的强制交付项（无此项无法评审）。
> 记录：如何用 skill-creator 方法论开发本技能、过程中真实的迭代与失败、以及复盘改进。
> 时间：2026-10-07 ｜ 执行者：WorkBuddy（AI 驱动）｜ 人：贾静文（jiajingwen）

---

## 一、目标

把挑战附带的 `c4b-wechat-publisher-starter` 改造成一个**可复用、可执行、可验证**的公众号文章生成技能，并产出一篇真实可发布的文章。核心约束（来自 CHALLENGE.md）：

- 必须用 **skill-creator** 技能来创建/优化（不是从零写，是「做技能的技能」做技能）
- 至少新增 **2 项** 能力（我新增了 7 项）
- 必须有可工作的技能 + 真实发布的文章 + AI 日志

---

## 二、AI 工作流设计（总体）

采用 skill-creator 的标准流程：`理解 → 规划 → 初始化 → 编辑 → 打包 → 迭代`。

1. **理解约束**：先读 `CHALLENGE.md` / `challenge.json` / `rubric.json`，明确交付物、命名规范、评分维度、红线（缺交付物 / 无 AI 日志 / 一句话提交）。
2. **拆解 starter**：解压 `c4b-wechat-publisher-starter.zip`，逐行读 `SKILL.md`、`convert_to_wechat.py`、`references/*`、`examples/*`，摸清原架构（read→sanitize→style→clean→output）。
3. **规划新增能力**：对照 starter 的「缺失能力」清单，选定 7 项（多主题 / callout / 目录 / 元数据 / 页脚 / 中文排版 / 图片内嵌），其中数学公式主动放弃并说明理由。
4. **初始化技能**：用 skill-creator 的 `init_skill.py` 脚手架生成目录骨架，删除占位文件。
5. **编辑技能**：重写 `SKILL.md`（命令式写法 + `agent_created: true`）、扩展 `convert_to_wechat.py`、`references/*`、`examples/*`。
6. **打包**：用 `package_skill.py` 校验并打成 zip。
7. **迭代**：用真实文章反复跑、写校验脚本、发现并修复 3 个真实 bug。

---

## 三、多轮迭代记录（含失败经验）

### 迭代 1：先验证 starter 基线
- 动作：用 starter 示例文章 + 增强脚本先跑通，确认基础转换无误。
- 校验：写 Python 校验脚本，确认输出不含 `<h1>/<div>/<script>/<style>/class/id`，主题色、`table`、引用样式都在。
- 结果：基线通过，15 项检查全 OK。

### 迭代 2（失败→修复）：代码块被正文样式覆盖
- **现象**：`apply_styles` 在给段落上样式时，把「代码块（pre→p，含换行）」也套成了正文 `<p>` 样式，导致代码块失去等宽底色。
- **根因**：`apply_styles` 对 `<p>` 无差别上样式，没排除含换行的代码块 `<p>`。
- **修复**：在 `apply_styles` 里对 `<p>` 增加「含 `\n` 则跳过」的守卫；新增 `restyle_code_and_quote`，专门给代码块上 `code_block` 样式、给无样式的 `<span>`（行内 code）上 `code_inline` 样式。
- **教训**：sanitize 阶段把 `<pre><code>` 拍平成了 `<p>`，后续所有「按标签批量上样式」的逻辑都必须先识别「它是不是代码块」。

### 迭代 3（失败→修复）：中文排版破坏了代码
- **现象**：`apply_typography` 给中英文间加空格时，会波及代码块里的命令（如 `python convert_to_wechat.py`），破坏可执行性。
- **根因**：typography 只跳过了 `<code>` 祖先，但代码块已被拍平成 `<p>`，不再是 `<code>`。
- **修复**：typography 改为同时跳过「父节点是 `<p>` 且 style 含 `pre-wrap`」的文本节点（即代码块）；行内 code 因是 ASCII 一般不受影响，但同样被安全排除。
- **教训**：任何「全文级文本改写」都必须显式排除代码上下文，否则会悄悄破坏内容。

### 迭代 4（失败→修复）：打包校验失败
- **现象**：`package_skill.py` 报 `Validation failed: Description cannot contain angle brackets (< or >)`。
- **根因**：SKILL.md 的 `description: >` 用了 YAML 折叠指示符 `>`，校验器把 `>` 当成了尖括号。
- **修复**：把 `description: >` 改为 `description: |`（字面量块，不含 `>`），重新打包通过校验。
- **教训**：skill-creator 的校验对 frontmatter 很严格（连指示符都查），写 SKILL.md 时描述里避免 `<`/`>`。

### 迭代 5：全能力冒烟测试
- 动作：用真实文章分别测试 5 套主题（warm/forest/minimal/default/accent）、`--no-toc --no-typo`、`--embed-images`（造一张 1×1 PNG 验证 base64 内嵌且无外链残留）。
- 结果：全部通过；图片内嵌后 `data:image/png;base64,` 出现且原路径不再出现。

---

## 四、Prompt / 工作流设计要点

- **模块化脚本**：所有样式收敛到 `THEMES` 字典、callout 样式到 `CALLOUT_TYPES` 字典，新增主题/框类型零侵入。
- **frontmatter 驱动元数据**：文章用 YAML 声明 title/author/date/abstract/theme/toc/footer，零代码改动即可个性化——这是「可复用」的关键。
- **callout 用单 `<p>` 实现**：刻意不用 `<div>`，保证公众号粘贴后不丢样式（这是 starter 没解决的核心坑）。
- **校验即文档**：每加一个能力，立刻写一条 Python 断言验证；校验脚本本身成了能力清单的「可执行证明」。

---

## 五、复盘（AAR）

### 做得好的
1. **严格走 skill-creator 流程**：init → 编辑 → package → 迭代，交付物齐全且技能通过官方校验。
2. **端到端验证**：不是「理论上能跑」，而是用真实文章 + 15 项断言 + 5 主题 + 图片内嵌全部实测。
3. **透明拿来主义**：专门写「拿来说明」逐项交代拿了/改了/为什么，符合挑战「拿来主义」原则。

### 不够好的 / 风险
1. **真实发布未由 AI 完成**：实际「粘贴到公众号并发布」这一步需要人的微信账号与登录，AI 无法代操作。已交付可一键复制的 HTML 与详细发布步骤，并在「文章链接.md」说明草稿箱截图的替代方案。
2. **数学公式未实现**：因真实文章无公式且依赖偏重，主动放弃；若后续需写技术文，应补上（用 `matplotlib` 把 LaTeX 渲成 PNG base64）。
3. **TOC 不能跳转**：公众号剥离 `id`，目录只能做结构预览。这是平台限制，已在文档中说明，避免使用者误以为是 bug。

### 改进方案
- 下一步给脚本加 `--math` 开关，按需渲染公式，不增加默认路径负担。
- 增加 `wechat-math-html` 参考的 PNG base64 方案对接。
- 提供一个「发布 SOP 检查清单」模板，降低首次发布者的踩坑率。

---

## 六、一句话总结

这次不是「写了个转换器」，而是用 **skill-creator（做技能的技能）** 把「写作→排版→发布」做成了一个可复用、可验证、可定制的技能，并通过真实文章跑通了端到端流程——这正是 C4B「内容生产过程产品化」的题眼。
