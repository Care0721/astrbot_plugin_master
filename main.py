from astrbot.api.all import *

@register("contact_owner_pro", "Care", "联系主人：终极兼容版", "3.1.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 这里的 ID 必须是三段式：平台:消息类型:QQ号
        # 根据你的查询结果，这里设置为发往你的私聊
        self.owner_session = "llbot:FriendMessage:3524815759" 
        self.reply_map = {}

    # 使用最基础的 command 装饰器，解决 filter 报错问题
    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        if not msg:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 存下 event 对象，这是回复时绕过 session 格式校验的关键
        self.reply_map[sender_id] = event

        forward_text = (
            f"📩 【新留言】\n"
            f"来自：{event.get_sender_name()}({sender_id})\n"
            f"内容：{msg}\n"
            f"━━━━━━━━━━━━━━\n"
            f"回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 直接发送纯文本字符串，不使用任何消息链包装，兼容性最强
            await self.context.send_message(self.owner_session, forward_text)
            yield event.plain_result("✅ 消息已转发。")
        except Exception as e:
            # 如果转发失败，打印出具体的报错，方便排查
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 校验是否为主人发送
        if str(event.get_sender_id()) != "3524815759":
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_text = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        try:
            if target_event:
                # 核心修复：直接传入原有的 event 对象，框架会自动处理 session
                await self.context.send_message(target_event, f"收到主人的回信：\n\n{reply_text}")
                yield event.plain_result(f"🚀 已成功回复给 {target_id}")
            else:
                yield event.plain_result(f"❌ 找不到该用户的联系记录，请让用户重新发送一次消息。")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
