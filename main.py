from astrbot.api.all import *
from astrbot.api.event.filter import command 
# 明确导入 Plain(纯文本)、At(艾特) 以及关键的 MessageChain(消息链)
from astrbot.api.message_components import Plain, At, MessageChain

@register("contact_owner_pro", "YourName", "联系主人Pro：完美发送版", "2.1.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 硬编码主人 QQ 号及合法的私聊 Session ID
        self.owner_id = "3524815759"
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        
        # 记录用户来源的字典
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        '''用户调用：联系机器人主人。用法：/联系主人 [内容]'''
        message_content = event.message_str.strip()
        if not message_content:
            yield event.plain_result("请输入你想对主人说的话。")
            return

        sender_id = str(event.get_sender_id())
        sender_name = event.get_sender_name()
        
        # 记录用户的会话地址
        self.reply_map[sender_id] = event.session_id

        forward_text = (
            f"📩 【收到留言】\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 发送者：{sender_name}\n"
            f"🆔 QQ号：{sender_id}\n"
            f"📍 来源：{event.session_id}\n"
            f"📝 内容：{message_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 快捷回复：直接复制下面这行 👇\n"
            f"/回复 {sender_id} [内容]"
        )

        try:
            # 【修复点】：使用 MessageChain 将消息组件包装起来
            chain = MessageChain([Plain(forward_text)])
            await self.context.send_message(self.owner_session, chain)
            yield event.plain_result("✅ 消息已成功转发给主人，请耐心等待回复。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发给主人失败，内部错误：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：回复指定用户。用法：/回复 [QQ号] [内容]'''
        # 权限校验
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误。正确格式：/回复 [QQ号] [内容]")
            return

        target_id = parts[0]
        reply_content = parts[1]

        target_session = self.reply_map.get(target_id)
        if not target_session:
            target_session = f"llbot:FriendMessage:{target_id}"

        try:
            # 【修复点】：使用 MessageChain 包装 At 和 Plain
            chain = MessageChain([
                At(qq=target_id), 
                Plain(f" 收到主人的回信：\n\n{reply_content}")
            ])
            await self.context.send_message(target_session, chain)
            
            yield event.plain_result(f"🚀 已成功送达给 {target_id}！\n📍 投递路线：{target_session}")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败！目标地址无法送达。报错详情：{str(e)}")

