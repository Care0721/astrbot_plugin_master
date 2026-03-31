from astrbot.api.all import *
from astrbot.api.event import MessageChain

@register("contact_owner_pro", "Care", "联系主人：正式@版", "3.3.4")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        self.owner_umo = f"llbot:FriendMessage:{self.owner_id}"
        self.user_sessions = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        self.user_sessions[sender_id] = {
            "umo": event.unified_msg_origin,
            "name": event.get_sender_name() or "用户",
            "qq": int(sender_id)
        }

        forward_text = (
            f"📩 【新留言】\n"
            f"来自：{event.get_sender_name()}({sender_id})\n"
            f"内容：{msg_str}\n\n"
            f"回复格式：回复 {sender_id} 内容\n"
            f"（也可以用 /回复 {sender_id} 内容）"
        )

        try:
            await self.context.send_message(
                self.owner_umo,
                MessageChain().message(forward_text)
            )
            yield event.plain_result("✅ 消息已转发给主人～")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id:
            return

        # 解析命令
        raw = event.message_str.strip()
        if raw.startswith('/'):
            raw = raw[1:].strip()
        if raw.startswith("回复"):
            raw = raw[2:].strip()

        parts = raw.split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误：回复 [QQ号] [内容]\n示例：回复 2370045690 你好呀")
            return

        target_id = parts[0].strip()
        reply_content = parts[1].strip()

        session = self.user_sessions.get(target_id)
        if not session:
            yield event.plain_result(f"❌ 找不到用户 {target_id} 的联系记录（可能已过期或未联系过）。")
            return

        try:
            # 使用 qq= 关键字参数 + name
            chain = MessageChain()
            chain.at(qq=session["qq"], name=session["name"])   # 正式 @（带名字）
            chain.message(f" 主人回复：\n{reply_content}")

            await self.context.send_message(
                session["umo"],
                chain
            )
            yield event.plain_result(f"🚀 已成功@回复给 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{str(e)}")