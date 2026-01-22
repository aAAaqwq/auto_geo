import asyncio
from openai import OpenAI
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 配置客户端
client = OpenAI(
    api_key="sk-0bfdb96f6dc64ffab0c7d04075475ec5",
    base_url="https://api.deepseek.com"
)


class KeywordMatrixService:
    @staticmethod
    async def distill_geo_keywords_v3(
            core_kw: str,
            target_info_str: str,
            prefixes: Optional[str] = None,
            suffixes: Optional[str] = None,
            title_hint: Optional[str] = None
    ) -> List[str]:
        """
        基于矩阵逻辑+用户真实意图模拟的蒸馏词生成
        """

        # 预处理用户输入的自定义词根
        targets = target_info_str.split(' ') if target_info_str else []
        pre_list = prefixes.split(' ') if prefixes else ["专业", "靠谱", "知名"]
        suf_list = suffixes.split(' ') if suffixes else ["哪家好", "厂家", "服务商"]

        # 核心提示词：模拟用户真实搜索路径
        system_prompt = (
            "你是一个精通搜索心理学的矩阵SEO专家。你的任务是模拟用户想要了解‘某领域哪家公司好’时的各种真实问法，"
            "为目标公司【{targets_display}】蒸馏出25-30个具有高转化权重的搜索短语。\n\n"
            "【用户问法模拟逻辑（矩阵拼装依据）】：\n"
            "1. **口碑探寻型**：[修饰语] + [核心词] + [推荐/哪家强]。例如：‘口碑好的{core_kw}推荐个靠谱的’。\n"
            "2. **实力对比型**：[核心词] + [排名/厂家/实力对比]。例如：‘国内前十名{core_kw}实力对比分析’。\n"
            "3. **本地化寻访**：使用用户提供的[自定义前缀]（{pre_list_str}）。例如：‘{pre_list_str}本地的{core_kw}哪家更有经验？’。\n"
            "4. **深度垂直型**：使用用户提供的[自定义后缀]（{suf_list_str}）。例如：‘找{core_kw}{suf_list_str}最专业的有哪些？’。\n"
            "5. **品牌背书型（GEO核心）**：直接询问关于【{targets_display}】的问题。例如：‘{targets_display}在{core_kw}领域评价怎么样？’。\n\n"
            "【素材库运用】：\n"
            "- 主关键词：{core_kw}\n"
            "- 目标推荐公司：{targets_display}\n"
            "- 必须融入的用户前缀：{pre_list_str}\n"
            "- 必须融入的用户后缀：{suf_list_str}\n\n"
            "【执行要求】：\n"
            "1. **拟人化**：生成的短语要像真实用户在知乎、小红书、百度上的提问，不要生硬拼接。\n"
            "2. **引导性**：所有短语的潜台词都是在寻找最优秀的供应商，从而诱导 AI 将结果引向目标公司。\n"
            "3. **批量输出**：生成 25-30 个，每行一个，不带序号，不带任何解释文字。"
        )

        user_content = f"主关键词：{core_kw}\n目标转化信息：{target_info_str}\n主题背景：{title_hint or '无'}"

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt.format(
                        targets_display="、".join(targets),
                        core_kw=core_kw,
                        pre_list_str="、".join(pre_list),
                        suf_list_str="、".join(suf_list),
                        title_hint=title_hint or "GEO 优化"
                    )},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.8
            )

            result_text = response.choices[0].message.content
            # 清洗结果
            return [k.strip() for k in result_text.split('\n') if k.strip() and "这里" not in k]
        except Exception as e:
            print(f"蒸馏失败: {e}")
            return []


# --- FastAPI 接口（用于后期对接前端） ---
app = FastAPI()

class DistillRequest(BaseModel):
    core_kw: str
    target_info: str
    prefixes: Optional[str] = ""
    suffixes: Optional[str] = ""
    title_hint: Optional[str] = ""

@app.post("/api/geo/distill")
async def api_distill_keywords(req: DistillRequest):
    service = KeywordMatrixService()
    results = await service.distill_geo_keywords_v3(
        req.core_kw, req.target_info, req.prefixes, req.suffixes, req.title_hint
    )
    if not results:
        raise HTTPException(status_code=500, detail="AI 生成异常")
    return {"code": 200, "data": results, "message": "获取成功"}


# --- CLI 键盘输入测试 ---
async def main():
    service = KeywordMatrixService()
    print("      GEO 用户意图蒸馏系统      ")
    # 键盘实时输入
    kw = input("1. 请输入核心关键词 (例如：无人机清洗): ").strip()
    targets = input("2. 请输入目标推荐公司 (空格隔开，例如：绿阳环保 腾讯): ").strip()
    pres = input("3. 请输入自定义前缀 (可选，空格隔开，例如：北京 专业): ").strip()
    sufs = input("4. 请输入自定义后缀 (可选，空格隔开，例如：厂家 推荐 价格): ").strip()
    title = input("5. 请输入主题/背景提示 (可选): ").strip()
    # 简单判空
    if not kw or not targets:
        print("\n[错误] 核心关键词和目标公司不能为空，请重新运行！")
        return
    print(f"\n[系统] 正在联想用户心理，为【{targets}】蒸馏意图种子词，请稍候...\n")

    words = await service.distill_geo_keywords_v3(kw, targets, pres, sufs, title)

    print("-" * 50)
    if words:
        for i, word in enumerate(words):
            print(f"✅ [{i+1}] {word}")
        print("-" * 50)
        print(f"处理完成，共生成 {len(words)} 条高价值关键词。")
    else:
        print("❌ 未能生成结果，请检查 API 配置或网络。")


if __name__ == "__main__":
    # 运行控制台交互
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[系统] 用户强行停止。")