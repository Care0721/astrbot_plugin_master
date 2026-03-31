from astrbot.api.all import *
from astrbot.api.event.filter import command 
# 明确导入 Plain(纯文本) 和 At(艾特) 组件
from astrbot.api.message_components import Plain, At

@register("contact_owner_pro", "YourName", "联系主人Pro：完美不报错版", "2.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 1. 根据你的截图，写死你专属的、符合 AstrBot 严格规范的私聊地址！
        self.owner_id = "3524815759"
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        
        # 2. 准备一个小本本，记录是谁从哪个群/私聊找的你
        # 格式: {"用户QQ": "会话地址(如 llbot:GroupMessage:123456)"}
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        '''用户调用：联系机器人主人。用法：/联系主人 [内容]'''
        message_content = event.message_str.strip()
        if not message_content:
            yield event.plain_result("请输入你想对主人说的话。")
            return

        # 获取对方的信息
        sender_id = str(event.get_sender_id())
        sender_name = event.get_sender_name()
        
        # 核心：把对方此时此刻所在的“会话地址”记在小本本上
        # event.session_id 肯定是合法的 3 段式地址，直接存！
        self.reply_map[sender_id] = event.session_id

        forward_text = (
            f"📩 【收到留言】\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 发送者：{sender_name}\n"
            f"🆔 QQ号：{sender_id}\n"
            f"📍 来源地址：{event.session_id}\n"
            f"📝 内容：{message_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 快捷回复：直接复制下面这行 👇\n"
            f"/回复 {sender_id} [内容]"
        )

        try:
            # 明确使用咱们组装好的 3 段式合法地址发给主人
            await self.context.send_message(self.owner_session, [Plain(forward_text)])
            yield event.plain_result("✅ 消息已成功转发给主人，请耐心等待回复。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发给主人失败，内部错误：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：回复指定用户。用法：/回复 [QQ号] [内容]'''
        # 权限校验：只允许主人 QQ 号调用
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式错误。正确格式：/回复 [QQ号] [内容]")
            return

        target_id = parts[0]
        reply_content = parts[1]

        # 从小本本上查一下，这个人一开始是从哪找的我？
        target_session = self.reply_map.get(target_id)
        
        # 如果小本本上没找到（比如机器人重启过，记录丢失了）
        # 我们就自己拼一个私聊地址，赌一把他是你的好友或者允许私聊
        if not target_session:
            target_session = f"llbot:FriendMessage:{target_id}"

        try:
            # 组合消息：@那个用户 + 回复的内容
            reply_chain = [
                At(qq=target_id), 
                Plain(f" 收到主人的回信：\n\n{reply_content}")
            ]
            
            # 使用合法地址发送！
            await self.context.send_message(target_session, reply_chain)
            
            yield event.plain_result(f"🚀 已成功送达给 {target_id}！\n📍 投递路线：{target_session}")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败！目标地址 {target_session} 无法送达。报错详情：{str(e)}")
