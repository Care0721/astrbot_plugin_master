from astrbot.api.all import *

# 1. 强制封装类：解决你遇到的所有 'no attribute chain' 报错
class MessageWrapper:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            # 2. 核心：在群聊会话中强制艾特目标 QQ
            self.chain.append(At(qq=str(at_qq)))
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_final", "Care", "联系主人：群聊私聊艾特版", "10.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        # 严格三段式 ID 确保你能收到转发
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 3. 关键：记录完整的群聊会话 event，这样回复时就是直接在群里艾特他
        self.reply_map[sender_id] = event 

        forward_text = (
            f"📩 【群留言】\n"
            f"👤 留言人：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            await self.context.send_message(self.owner_session, MessageWrapper(forward_text))
            yield event.plain_result("✅ 已转发至主人私聊。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 仅限主人操作
        if str(event.get_sender_id()) != self.owner_id: return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        if not target_event:
            # 重启后需要对方重新发消息激活
            yield event.plain_result(f"❌ 找不到 {target_id} 的群聊记录，请让对方在群里重新发一次。")
            return

        try:
            # 4. 自动识别：如果对方是在群里留言，这里会直接在群里 @ 他回复
            msg_obj = MessageWrapper(f"主人回复：{reply_content}", at_qq=target_id)
            await self.context.send_message(target_event, msg_obj)
            yield event.plain_result(f"🚀 已在群聊中艾特回复给 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{str(e)}")
