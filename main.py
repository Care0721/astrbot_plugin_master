from astrbot.api.all import *
from astrbot.api.event.filter import command 
from astrbot.api.message_components import Plain

@register("contact_owner_pro", "YourName", "联系主人Pro：全平台兼容版", "1.3.3")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 硬编码主人 ID
        self.owner_id = "3524815759"

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        '''用户调用：联系机器人主人。用法：/联系主人 [内容]'''
        message_content = event.message_str.strip()
        if not message_content:
            yield event.plain_result("请输入你想对主人说的话。")
            return

        # 获取完整的发送者信息（包含适配器和平台前缀）
        # event.session_id 通常是 "adapter:platform:user_id"
        sender_session_id = event.session_id
        sender_name = event.get_sender_name()
        
        # 提取前缀（适配器:平台），用于构造主人的 Session ID
        # 这样无论你在 QQ、TG 还是微信，都能准确找到主人
        prefix = ":".join(sender_session_id.split(":")[:-1])
        owner_session = f"{prefix}:{self.owner_id}"

        forward_text = (
            f"📩 【收到留言】\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 发送者：{sender_name}\n"
            f"🆔 完整ID：{sender_session_id}\n"
            f"📝 内容：{message_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_session_id} [内容]"
        )

        try:
            # 使用组装好的完整 Session ID 发送
            await self.context.send_message(owner_session, [Plain(forward_text)])
            yield event.plain_result("✅ 消息已成功转发给主人。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：回复指定用户。用法：/回复 [完整ID] [内容]'''
        
        # 权限校验：只允许硬编码的那个 ID 回复
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [完整ID] [内容]\n提示：直接复制主人收到的“完整ID”即可")
            return

        target_session = parts[0] # 这里的 target_session 应该是 adapter:platform:id
        reply_content = parts[1]

        try:
            # 如果主人输入的只是纯数字，我们尝试帮他补全前缀
            if ":" not in target_session:
                prefix = ":".join(event.session_id.split(":")[:-1])
                target_session = f"{prefix}:{target_session}"

            reply_msg = f"🔔 您收到了主人的回信：\n\n{reply_content}"
            await self.context.send_message(target_session, [Plain(reply_msg)])
            yield event.plain_result(f"🚀 已成功发送给：{target_session}")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{str(e)}")
