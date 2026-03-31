from astrbot.api.all import *
from astrbot.api.event import MessageChain  # 必须加这一行

@register("contact_owner_pro", "Care", "联系主人：兼容修复版", "3.3.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 这里填你的数字 QQ 号（字符串）
        self.owner_id = "3524815759"
        # 主人接收消息的 unified_msg_origin（llbot 是你当前适配器名，保持一致即可）
        self.owner_umo = f"llbot:FriendMessage:{self.owner_id}"
        # 存储联系过用户的 session（key: QQ号, value: unified_msg_origin）
        self.user_umos = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 关键修复：保存用户的 unified_msg_origin（官方推荐方式）
        self.user_umos[sender_id] = event.unified_msg_origin

        forward_text = f"📩 【新留言】\n来自：{event.get_sender_name()}({sender_id})\n内容：{msg_str}\n\n回复格式：/回复 {sender_id} 内容"

        try:
            # 使用官方 MessageChain 发送给主人
            await self.context.send_message(
                self.owner_umo,
                MessageChain().message(forward_text)
            )
            yield event.plain_result("✅ 消息已转发给主人～")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 只有主人才能使用回复命令
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        target_umo = self.user_umos.get(target_id)

        if not target_umo:
            yield event.plain_result(f"❌ 找不到用户 {target_id} 的联系记录（可能已过期或未联系过）。")
            return

        try:
            # 关键修复：用保存的 unified_msg_origin 回复用户
            await self.context.send_message(
                target_umo,
                MessageChain().message(f"主人回复：\n{reply_content}")
            )
            yield event.plain_result(f"🚀 已成功回复给 {target_id}")
            # 可选：回复成功后清除记录（防止内存占用，可自行决定是否保留）
            # del self.user_umos[target_id]
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{str(e)}")