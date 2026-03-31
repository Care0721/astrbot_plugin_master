from astrbot.api.all import *

@register("contact_owner_pro", "Care", "联系主人：终极兼容版", "7.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # --- 这里的 ID 必须配置为三段式，否则你会收不到转发 ---
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
        # 存下 event 对象，这是解决“缺少 session_id”报错的关键
        self.reply_map[sender_id] = event 

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 发送者：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 解决 'str' has no attribute 'chain'：用 [Plain(...)] 发送
            await self.context.send_message(self.owner_session, [Plain(forward_text)])
            yield event.plain_result("✅ 消息已成功转发给主人。")
        except Exception as e:
            # 如果还收不到，这里会显示具体的报错原因
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
            yield event.plain_result(f"❌ 找不到该用户 {target_id} 的联系记录，请让对方重新发送一次消息。")
            return

        try:
            from astrbot.api.message_components import Plain, At
            # 构造带 @ 的消息链
            msg_chain = [
                At(qq=target_id), 
                Plain(" "), 
                Plain(f"收到主人的回信：\n\n{reply_content}")
            ]
            # 直接使用 target_event 发送，最稳妥
            await self.context.send_message(target_event, msg_chain)
            yield event.plain_result(f"🚀 已成功艾特并回复给 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{str(e)}")
