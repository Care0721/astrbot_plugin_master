from astrbot.api.all import *

# 手动构造一个满足框架‘强迫症’的消息盒
class SimpleChain:
    def __init__(self, text):
        from astrbot.api.message_components import Plain
        self.chain = [Plain(text)]

@register("contact_owner_pro", "Care", "联系主人：兼容修复版", "3.3.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 这里填你的数字 QQ 号
        self.owner_id = "3524815759"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        self.reply_map[sender_id] = event # 存下 event 对象，这是解决 session_id 报错的关键

        forward_text = f"📩 【新留言】\n来自：{event.get_sender_name()}({sender_id})\n内容：{msg_str}\n\n回复格式：/回复 {sender_id} 内容"

        try:
            # 尝试最稳妥的三段式发送给主人
            target = f"llbot:FriendMessage:{self.owner_id}"
            await self.context.send_message(target, SimpleChain(forward_text))
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
        target_event = self.reply_map.get(target_id)

        if not target_event:
            yield event.plain_result(f"❌ 找不到该用户 {target_id} 的联系记录。")
            return

        try:
            # 解决“缺少有效数字 session_id”的核心：直接把原 event 丢回去
            # 框架会自己从 event 里提取它想要的路径
            await self.context.send_message(target_event, SimpleChain(f"主人回复：\n{reply_content}"))
            yield event.plain_result(f"🚀 已回复给 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
