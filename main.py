from astrbot.api.all import *

# 修正导入方式，避开内置 filter 冲突
from astrbot.api.event.filter import command 
from astrbot.api.message_components import Plain

@register("contact_owner_pro", "YourName", "联系主人Pro：精准回复版", "1.3.2")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 硬编码主人 QQ 号
        self.owner_id = "3524815759"

    # 使用直接导入的 command 装饰器，不再通过 filter.command 调用
    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        '''用户调用：联系机器人主人。用法：/联系主人 [内容]'''
        message_content = event.message_str.strip()
        if not message_content:
            yield event.plain_result("请输入你想对主人说的话。")
            return

        sender_id = event.get_sender_id()
        sender_name = event.get_sender_name()
        
        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 发送者：{sender_name}\n"
            f"🆔 QQ/ID：{sender_id}\n"
            f"📝 内容：{message_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复：/回复 {sender_id} [内容]"
        )

        try:
            await self.context.send_message(self.owner_id, [Plain(forward_text)])
            yield event.plain_result("✅ 消息已成功转发给主人。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{e}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：指定 ID 回复。用法：/回复 [QQ/ID] [内容]'''
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]

        try:
            reply_msg = f"🔔 您收到了主人的回信：\n\n{reply_content}"
            await self.context.send_message(target_id, [Plain(reply_msg)])
            yield event.plain_result(f"🚀 已成功发送给用户({target_id})")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{e}")
