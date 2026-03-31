from astrbot.api.all import *

# 手动构造一个完全符合框架要求的消息类，解决 'list' 或 'str' no attribute 'chain' 的问题
class CustomChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            # 1. 核心需求：自动识别 QQ 并添加艾特组件
            self.chain.append(At(qq=str(at_qq)))
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_pro", "Care", "联系主人：精准艾特修复版", "8.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 配置你的大号 ID
        self.owner_id = "3524815759"
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 记录完整的 event 对象，用于后续精准原路回复
        self.reply_map[sender_id] = event 

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 发送者：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 转发给主人，使用包装类解决属性报错
            await self.context.send_message(self.owner_session, CustomChain(forward_text))
            yield event.plain_result("✅ 消息已转发。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        target_event = self.reply_map.get(target_id) # 从记录获取 event

        if not target_event:
            # 提醒：重启或保存代码会清空此处记录
            yield event.plain_result(f"❌ 找不到用户 {target_id} 的记录，请让对方先发一条消息。")
            return

        try:
            # 2. 核心需求：回复时自动艾特目标 QQ
            # 我们通过 target_id 动态生成艾特组件
            msg_obj = CustomChain(f"主人回信：\n{reply_content}", at_qq=target_id)
            
            # 使用 target_event 发送，它是最能解决“缺少 session_id”报错的方法
            await self.context.send_message(target_event, msg_obj)
            yield event.plain_result(f"🚀 已成功艾特并回复给 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{str(e)}")
