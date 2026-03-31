from astrbot.api.all import *
from astrbot.api.event.filter import command 

@register("contact_owner_pro", "Care", "联系主人Pro：极简稳定版", "2.4.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 这里填你的 QQ 号
        self.owner_id = "3524815759"
        # 记录用户 Session 的字典
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        '''用户调用：联系机器人主人'''
        msg = event.message_str.strip()
        if not msg:
            yield event.plain_result("请输入你想说的话。")
            return

        sender_id = str(event.get_sender_id())
        # 记录这次对话的 event，方便后面回复
        self.reply_map[sender_id] = event
        
        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 发送者：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        # 尝试直接发送给主人私聊，如果框架不支持主动私聊，它会报错
        try:
            # 这里的地址格式根据你之前的截图调整
            target = f"llbot:FriendMessage:{self.owner_id}"
            await self.context.send_message(target, forward_text)
            yield event.plain_result("✅ 消息已转发给主人。")
        except Exception as e:
            # 如果私聊转发失败，就在当前群里艾特主人（保底方案）
            yield event.chain_result([
                At(qq=self.owner_id),
                Plain(f" 有人找你！\n{forward_text}")
            ])

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：回复指定用户'''
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        
        # 核心：尝试从记录里找那个人的 event
        target_event = self.reply_map.get(target_id)
        
        if target_event:
            try:
                # 这种方式最稳，它是顺着之前的事件回过去的
                await self.context.send_message(target_event.session_id, f"收到主人的回信：\n{reply_content}")
                yield event.plain_result(f"🚀 已成功回复给 {target_id}")
            except Exception as e:
                yield event.plain_result(f"❌ 回复失败：{str(e)}")
        else:
            yield event.plain_result(f"❌ 找不到该用户的联系记录，可能机器人重启了。")
