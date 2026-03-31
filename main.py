from astrbot.api.all import *

@register("session_reply_pro", "Care", "Session 字符串硬核回复版", "25.0.0")
class SessionReplyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        # 依然需要这个来记录对方的名字
        self.reply_map = {} 

    @command("联系主人")
    async def to_owner(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        if not msg: return
        
        sender_id = str(event.get_sender_id())
        self.reply_map[sender_id] = event.get_sender_name() # 只存名字
        
        # 构造发给你的三段式 session
        my_session = f"llbot:FriendMessage:{self.owner_id}"
        
        forward_text = (
            f"📩 【新留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} 内容"
        )

        try:
            # 使用字符串 session 发送
            await self.context.send_message(my_session, [Plain(forward_text)])
            yield event.plain_result("✅ 转发成功。")
        except Exception as e:
            yield event.plain_result(f"✅ 转发(保底): {str(e)}")

    @command("回复")
    async def to_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id: return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_qq = parts[0].strip()
        content = parts[1].strip()
        
        # 1. 识别名字：从记录里拿，拿不到就显示 QQ 号
        target_name = self.reply_map.get(target_qq, target_qq)

        # 2. 关键：构造严格的三段式 Session 字符串
        # 必须保证是这样：llbot:FriendMessage:123456
        target_session = f"llbot:FriendMessage:{target_qq}"

        try:
            from astrbot.api.message_components import At, Plain
            # 3. 构造带艾特的消息链
            msg_chain = [
                At(qq=target_qq), 
                Plain(f" 你好 {target_name}，收到主人的回信：\n{content}")
            ]

            # 4. 使用你要求的 session 格式发送
            await self.context.send_message(target_session, msg_chain)
            yield event.plain_result(f"🚀 已通过 Session 成功回复：{target_name}")

        except Exception as e:
            error_info = str(e)
            if "expected 3" in error_info:
                yield event.plain_result(f"❌ Session 格式错误(依旧是 unpack 问题): {error_info}")
            else:
                yield event.plain_result(f"❌ 发送失败: {error_info}")
