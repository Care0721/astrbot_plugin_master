from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("contact_owner_pro", "YourName", "联系主人Pro：支持指定QQ号精准回复", "1.3.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 硬编码主人 QQ 号
        self.owner_id = "3524815759"

    @filter.command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        '''用户调用：联系机器人主人。用法：/联系主人 [内容]'''
        message_content = event.message_str.strip()
        if not message_content:
            yield event.plain_result("请输入你想对主人说的话。")
            return

        sender_id = event.get_sender_id()
        sender_name = event.get_sender_name()
        platform = event.get_platform_name()

        # 构造给主人的格式化信息，突出显示 QQ 号方便复制
        forward_text = (
            f"📩 【收到新留言】\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 发送者：{sender_name}\n"
            f"🆔 QQ/ID：{sender_id}\n"  # 显式显示 QQ 号
            f"🌐 平台：{platform}\n"
            f"📝 内容：{message_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [你的回复内容]"
        )

        try:
            # 转发给主人
            await self.context.send_message(self.owner_id, [Plain(forward_text)])
            yield event.plain_result("✅ 消息已转发，主人看到后会给您回复。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{e}")

    @filter.command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：指定 ID 回复。用法：/回复 [QQ/ID] [内容]'''
        
        # 权限校验
        if str(event.get_sender_id()) != self.owner_id:
            return

        # 解析参数：尝试从 "/回复 123456 内容" 中提取 ID 和内容
        parts = event.message_str.strip().split(maxsplit=1)
        
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误！请使用：/回复 [QQ号] [内容]\n示例：/回复 12345678 你好呀")
            return

        target_id = parts[0]    # 目标 QQ 号
        reply_content = parts[1] # 回复的文本

        try:
            # 构造发送给用户的消息内容
            reply_msg = f"🔔 您收到了主人的回信：\n\n{reply_content}"
            
            # 发送消息给指定 ID
            await self.context.send_message(target_id, [Plain(reply_msg)])
            
            yield event.plain_result(f"🚀 已成功发送给用户({target_id})")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败。可能原因：机器人未加对方好友、ID 错误。错误信息：{e}")

