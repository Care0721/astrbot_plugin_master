from astrbot.api.all import *
from astrbot.api.event.filter import command 

# 尝试导入组件，如果找不到 MessageChain 就自己定义一个，绕过报错
try:
    from astrbot.api.message_components import Plain, At, MessageChain
except ImportError:
    from astrbot.api.message_components import Plain, At
    # 自己定义一个兼容类，防止底层框架报错 'list' object has no attribute 'chain'
    class MessageChain:
        def __init__(self, components):
            self.chain = components

@register("contact_owner_pro", "YourName", "联系主人Pro：终极兼容版", "2.2.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 1. 你的 ID
        self.owner_id = "3524815759"
        # 2. 根据你的截图，这是最标准的私聊地址格式
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        # 3. 记录来源的小本本
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
        self.reply_map[sender_id] = event.session_id

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 发送者：{sender_name}\n"
            f"🆔 QQ号：{sender_id}\n"
            f"📍 来源：{event.session_id}\n"
            f"📝 内容：{message_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 优先用包装盒发送
            await self.context.send_message(self.owner_session, MessageChain([Plain(forward_text)]))
            yield event.plain_result("✅ 消息已转发给主人。")
        except:
            try:
                # 如果还报错，直接发纯字符串字符串（这是最原始、最兼容的办法）
                await self.context.send_message(self.owner_session, forward_text)
                yield event.plain_result("✅ 消息已转发（文本模式）。")
            except Exception as e:
                yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：回复指定用户。用法：/回复 [QQ号] [内容]'''
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        target_session = self.reply_map.get(target_id)
        
        # 如果没记录，拼一个私聊地址
        if not target_session:
            target_session = f"llbot:FriendMessage:{target_id}"

        try:
            # 组合回复内容
            msg_list = [At(qq=target_id), Plain(f" 收到主人的回信：\n\n{reply_content}")]
            await self.context.send_message(target_session, MessageChain(msg_list))
            yield event.plain_result(f"🚀 已发送至：{target_session}")
        except:
            try:
                # 兼容模式：如果艾特组件报错，就发纯文字
                await self.context.send_message(target_session, f"@{target_id} 收到主人的回信：\n\n{reply_content}")
                yield event.plain_result(f"🚀 已发送（纯文本模式）")
            except Exception as e:
                yield event.plain_result(f"❌ 投递失败：{str(e)}")
